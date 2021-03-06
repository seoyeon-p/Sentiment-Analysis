import collections
import numpy as np
import re
import tensorflow as tf
import random
import math
from collections import Counter
import itertools
import os
import pickle
'''
def openFile(filename):
    f = open(filename,mode = "r", encoding = "utf-8")
    data = f.read().replace("\t","")
    data = data.replace("\n"," ")
    data = re.sub('[(@=.#/?:$})]','',data)
    data = tf.compat.as_str(data).split()
    return data

words = openFile("output_pair.txt")
print("data size = " , len(words))

vocabulary_size = 100
'''
"""
url = 'http://mattmahoney.net/dc/'


def maybe_download(filename, expected_bytes):
  if not os.path.exists(filename):
    filename, _ = urllib.request.urlretrieve(url + filename, filename)
  statinfo = os.stat(filename)
  if statinfo.st_size == expected_bytes:
    print('Found and verified', filename)
  else:
    print(statinfo.st_size)
    raise Exception(
        'Failed to verify ' + filename + '. Can you get to it with a browser?')
  return filename

filename = maybe_download('text8.zip', 31344016)


# Read the data into a list of strings.
def read_data(filename):
  with zipfile.ZipFile(filename) as f:
    data = tf.compat.as_str(f.read(f.namelist()[0])).split()
  return data

words = read_data(filename)
print('Data size', len(words))

"""



vocabulary_size = 50000

'''
ftraining = open("rawData.txt","r")
while True:
    line = ftraining.readline()
    if not line: break
    label = line.split()[2]
    transcript = line.split()[3:]
    sentence_list.append(transcript)
'''

fcheck = open("real_embedding_value_check.txt", "w",encoding="utf-8")
fdataset = open("dataset_real_value.txt","w",encoding="utf-8")

def build_dataset(words,vocab_size):
    count = [['UNK',-1]]        #to explicity model the probability of out-of-vocab words by intorducing a specical token <UNK>
    count.extend(collections.Counter(words).most_common(vocab_size-1))
    dictionary = dict()
    for word, _ in count :
        dictionary[word] = len(dictionary)
    data = list()
    unk_count = 0
    for word in words:
        if word in dictionary:
            index = dictionary[word]
        else:
            index = 0
            unk_count +=1
        data.append(index)
    count[0][1] =unk_count
    reverse_dictionary = dict(zip(dictionary.values(), dictionary.keys()))
    fdataset.write("The words is "+ str(words)+"\n")
    fdataset.write("The data is "+str(data)+"\n")
    fdataset.write("The dictionary is "+str(dictionary)+"\n")
    fdataset.write("The reverse_dictionary" + str(reverse_dictionary)+"\n")
    return data, count, dictionary, reverse_dictionary

f = open("total_transcript_twitter_ISEAR.txt","r",encoding="utf-8")
transcript = f.readlines()
text = ""
for i in range(0,len(transcript)):
    trans = transcript[i].strip()
    text = text + " " + trans

training_transcript = Counter(text.split())
#for element in training_transcript:
#    if training_transcript[element] == 1:del training_transcript[element]
data, count, dictionary, reverse_dictionary = build_dataset(training_transcript, vocabulary_size)
print('Most common words (+UNK)', count[:5])
print('Sample data', data, [reverse_dictionary[i] for i in data[:10]])

data_index = 0


def generate_batch(batch_size,num_skips,skip_window):
    global data_index
    assert batch_size % num_skips == 0
    assert num_skips <= 2 * skip_window
    batch = np.ndarray(shape=(batch_size), dtype = np.int32)
    labels = np.ndarray(shape=(batch_size,1), dtype = np.int32)
    span = 2 * skip_window +1
    buffer = collections.deque(maxlen = span)
    for _ in range(span):
        buffer.append(data[data_index])
        data_index = (data_index+1)%len(data)
    for i in range(batch_size // num_skips):
        target = skip_window
        targets_to_avoid = [skip_window]
        for j in range(num_skips):
            while target in targets_to_avoid:
                target = random.randint(0,span-1)
            targets_to_avoid.append(target)
            batch[i * num_skips + j] = buffer[skip_window]
            labels[i * num_skips + j,0] = buffer[target]
        buffer.append(data[data_index])
        data_index = (data_index + i)%len(data)

    data_index = (data_index + len(data) - span) % len(data)
    fcheck.write("The batch contend : " + str(batch) +"\n")
    return batch, labels

batch, labels = generate_batch(batch_size= 8, num_skips=2, skip_window=1)
for i in range(8):
    print(batch[i], reverse_dictionary[batch[i]],
          '->', labels[i, 0], reverse_dictionary[labels[i, 0]])


batch_size = 128
embedding_size = 128  # Dimension of the embedding vector.
skip_window = 1       # How many words to consider left and right.
num_skips = 2         # How many times to reuse an input to generate a label.

# We pick a random validation set to sample nearest neighbors. Here we limit the
# validation samples to the words that have a low numeric ID, which by
# construction are also the most frequent.
valid_size = 16     # Random set of words to evaluate similarity on.
valid_window = 100  # Only pick dev samples in the head of the distribution.
valid_examples = np.random.choice(valid_window, valid_size, replace=False)
num_sampled = 64    # Number of negative examples to sample.

graph = tf.Graph()

with graph.as_default():
  # Input data.
  train_inputs = tf.placeholder(tf.int32, shape=[batch_size])
  train_labels = tf.placeholder(tf.int32, shape=[batch_size, 1])
  valid_dataset = tf.constant(valid_examples, dtype=tf.int32)

  with tf.device('/cpu:0'):
    # Look up embeddings for inputs.
    embeddings = tf.Variable(
        tf.random_uniform([vocabulary_size, embedding_size], -1.0, 1.0))
    embed = tf.nn.embedding_lookup(embeddings, train_inputs)
    #print(str(embed))

    # Vector가지고 similarity를 계산하는 거니까 일단 vector로 나타낸 그 부분을 찾아야한다!
    # Construct the variables for the NCE loss
    nce_weights = tf.Variable(
        tf.truncated_normal([vocabulary_size, embedding_size],
                            stddev=1.0 / math.sqrt(embedding_size)))
    nce_biases = tf.Variable(tf.zeros([vocabulary_size]))

  # Compute the average NCE loss for the batch.
  # tf.nce_loss automatically draws a new sample of the negative labels each
  # time we evaluate the loss.
  loss = tf.reduce_mean(
      tf.nn.nce_loss(weights=nce_weights,
                     biases=nce_biases,
                     labels=train_labels,
                     inputs=embed,
                     num_sampled=num_sampled,
                     num_classes=vocabulary_size))

  # Construct the SGD optimizer using a learning rate of 1.0.
  optimizer = tf.train.GradientDescentOptimizer(1.0).minimize(loss)

  # Compute the cosine similarity between minibatch examples and all embeddings.
  norm = tf.sqrt(tf.reduce_sum(tf.square(embeddings), 1, keep_dims=True))
  normalized_embeddings = embeddings / norm
  valid_embeddings = tf.nn.embedding_lookup(
      normalized_embeddings, valid_dataset)
  similarity = tf.matmul(
      valid_embeddings, normalized_embeddings, transpose_b=True)
  #Input이 embed이고, embedding은 그럼 뭐하는 얘지?


  init = tf.global_variables_initializer()


num_steps = 10001

with tf.Session(graph=graph) as session:
  init.run()
  print("Initialized")

  average_loss = 0
  for step in range(num_steps):
    batch_inputs, batch_labels = generate_batch( batch_size, num_skips, skip_window)
    feed_dict = {train_inputs: batch_inputs, train_labels: batch_labels}

    _, loss_val = session.run([optimizer, loss], feed_dict=feed_dict)
    average_loss += loss_val

    if step % 2000 == 0:
      if step > 0:
        average_loss /= 2000
      print("Average loss at step ", step, ": ", average_loss)
      average_loss = 0


    value = session.run(embeddings)
    value_check2 = session.run(normalized_embeddings)
    #Embed를 써야하는 거야 Embeddings를 써야하는 거야?...대체..
    #print(str(value))
    fcheck.write(str(value_check2)+"\n")

    if step % 10000 == 0:
      sim = similarity.eval()

      for i in range(valid_size):
        # valid_example array contains 16 numbers
        valid_word = reverse_dictionary[valid_examples[i]]
        top_k = 8
        # ndarray.argsort() return the indices after sorting the -sim[i,:]
        nearest = (-sim[i, :]).argsort()[1:top_k + 1]
        log_str = "Nearest to %s:" % valid_word
        for k in range(top_k):
          try:
           close_word = reverse_dictionary[nearest[k]]
           log_str = "%s %s," % (log_str, close_word)
           print(log_str)
          except KeyError:
           print("keyError")
           #print(str(reverse_dictionary))
  final_embeddings = normalized_embeddings.eval()

def plot_with_labels(low_dim_embs, labels, filename='tsne.png'):
  assert low_dim_embs.shape[0] >= len(labels), "More labels than embeddings"
  plt.figure(figsize=(18, 18))  # in inches
  for i, label in enumerate(labels):
    x, y = low_dim_embs[i, :]
    plt.scatter(x, y)
    plt.annotate(label,
                 xy=(x, y),
                 xytext=(5, 2),
                 textcoords='offset points',
                 ha='right',
                 va='bottom')

  plt.savefig(filename)

from sklearn.manifold import TSNE
import matplotlib.pyplot as plt

tsne = TSNE(perplexity=30, n_components=2, init='pca', n_iter=5000)
plot_only = 100
low_dim_embs = tsne.fit_transform(final_embeddings[:plot_only, :])
labels = [reverse_dictionary[i] for i in range(plot_only)]
plot_with_labels(low_dim_embs, labels)

