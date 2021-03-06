import tensorflow as tf
import numpy as np
import os
from ver_1word_embedding_frequency import emotionList_return
from tensorflow.python.framework import dtypes

#이것만 해도 논문쓸수있을거같은데 ESN이랑 다 비교해서....하나를 제대로 하자 하나를
#제대로하자
#이거 제대로 결과나와서
#논문쓰자쓰자제발좀쓰자
#화이팅

emotionList = emotionList_return()

count = 0
currentPath = os.getcwd()
os.chdir(currentPath  + "/Training")
Xtraining = np.load("transcriptIndex.npy")
Ytraining = np.load("emotionIndex.npy")

os.chdir(currentPath  + "/Test")
Xtest = np.load("transcriptIndex.npy")
Ytest = np.load("emotionIndex.npy")



hidden_size = len(emotionList)
line_length = len(Xtraining[0])
sequence_length = len(Xtraining[0])
num_classes = len(emotionList)
learning_rate = 0.01

num_epoch = 100
echo_step = 3
batch_size = 50
num_hidden = 64
num_batch = len(Xtraining)//batch_size
def generate_batch(batch_size, train, label):
    data_index = 0
    batch, labels = [] , []
    iterate_num = int(len(train)/batch_size)
    for i in range(iterate_num):
        batch.append(train[data_index:data_index+batch_size])
        labels.append(label[data_index:data_index+batch_size])
        data_index = (data_index + batch_size)
    return batch, labels



all_training = tf.convert_to_tensor(Xtraining,dtype = dtypes.float32)
all_label = tf.convert_to_tensor(Ytraining, dtype = dtypes.int32)

all_test = tf.convert_to_tensor(Xtest,dtype = dtypes.float32)
all_test_label = tf.convert_to_tensor(Ytest, dtype = dtypes.int32)

train_input_queue = tf.train.slice_input_producer([Xtraining, Ytraining], shuffle=False)
test_input_queue = tf.train.slice_input_producer([Xtest,Ytest], shuffle=False)

train_transcript = train_input_queue[0]
train_label = train_input_queue[1]

test_trancript = test_input_queue[0]
test_label = test_input_queue[1]


train_transcript_batch, train_label_batch = tf.train.batch([train_transcript,train_label], batch_size = batch_size)
print("This is the batch of x" +str(train_transcript_batch))
test_transcript_batch, test_label_batch = tf.train.batch([test_trancript,test_label],batch_size = batch_size)


inputs = []

for i in range(0,num_epoch):
    inputs.append(tf.placeholder(tf.float32,shape = [batch_size,len(Xtraining[0]),line_length]))

X = tf.placeholder(tf.float32,shape = [None,len(Xtraining[0]),line_length])
Y = tf.placeholder(tf.int32,shape = [None,len(Xtraining[0]),num_classes])


batch_, label_= generate_batch(batch_size, Xtraining, Ytraining)
test_batch_, test_label_ = generate_batch(batch_size,Xtest,Ytest)

new_batch, new_label = [], []
for i in range(0,len(batch_)):
    new_batch.append(np.ndarray.tolist(batch_[i]))
    new_label.append(np.ndarray.tolist(label_[i]))

new_test_batch , new_test_label = [], []
for i in range(0,len(test_batch_)):
    new_test_batch.append(np.ndarray.tolist(test_batch_[i]))
    new_test_label.append(np.ndarray.tolist(test_label_[i]))



finput = open("input.txt","w")
for i in range(0,len(batch_)):
    finput.write(str(batch_[i])+"\n")

cell = tf.nn.rnn_cell.BasicLSTMCell(num_units = num_classes, state_is_tuple=True)
initial_state = cell.zero_state(batch_size = batch_size, dtype = tf.float32)

output, _state = tf.nn.dynamic_rnn(cell,X,initial_state = initial_state, dtype = tf.float32,time_major=True)
output_shape = tf.shape(output)
print(str(tf.shape(Y)))
print(str(output_shape))

weight = tf.Variable(tf.random_normal([batch_size,sequence_length]))
sequence_loss = tf.nn.softmax_cross_entropy_with_logits(logits = output, labels = Y)
loss = tf.reduce_mean(sequence_loss)
train = tf.train.AdamOptimizer(learning_rate = learning_rate).minimize(loss)

#결과값중 가장 큰 값을 1로 설정하는 함수가 argmax인 것.
prediction = tf.equal(tf.argmax(Y,1), tf.argmax(output,1))
accuracy = tf.reduce_mean(tf.cast(prediction, tf.float32))


#Batch를 한번에 묶어보자 그리고 accuracy가 왜이렇게 되는지 봐야겠다.


fon = open("training.txt","w")
result = np.empty([Xtest.shape[0], Xtest.shape[1]])
avg_cost = 0
with tf.Session() as sess:
    sess.run(tf.global_variables_initializer())
    coord = tf.train.Coordinator()
    threads = tf.train.start_queue_runners(coord= coord)
    print("from the train set")
    '''
    x_batch = new_batch
    y_batch = new_label
    l, _ = sess.run([loss, train], feed_dict={X: x_batch, Y: y_batch})
    fon.write(str(i) + " The loss is " + str(l) + "\n")
    fon.write(str(result) + "\n")
    avg_cost += l / len(batch_)
    print("epoch;", "%d" % (1), "cost= ", "{:.9f}".format(avg_cost))
    print("Accuracy of total;", accuracy.eval(session=sess, feed_dict={X: new_test_batch, Y: new_test_label}))
    '''
    for epoch in range(num_epoch):
        x_batch = new_batch
        y_batch = new_label
        l,_ = sess.run([loss,train], feed_dict = {X: x_batch, Y:y_batch})
        #result_ = sess.run(accuracy, feed_dict={X:[test_batch_[i]],Y:[test_label_[i]]})
        #result = sess.run(Xtest)
        #print(str(max(result[i])))
        fon.write(str(i)  + " The loss is " +str(l) + "\n")
        fon.write(str(result) + "\n")
        avg_cost += l /len(batch_)

        print("epoch;","%d" % (epoch +1), "cost= ","{:.9f}".format(avg_cost))
        print("Accuracy of total;", accuracy.eval(session=sess, feed_dict={X: new_test_batch, Y: new_test_label}))

    coord.request_stop()
    coord.join(threads)
emotion_result = []
result = np.ndarray.tolist(result)
fon.write(str(result)+"\n")
for i in range(0,len(result)):
    line = result[i]
    max_val = max(result[i])
    index = line.index(max_val)
    try:
        emotion_result.append(emotionList[index])
    except IndexError:
        emotion_result.append("UNK")


ground_truth = []
one = 1
Ytest = np.ndarray.tolist(Ytest)
for i in range(0,len(Ytest)):
    line = Ytest[i]
    index = Ytest[i].index(one)
    ground_truth.append(emotionList[index])

fresult = open("result.txt","w")
count = 0
for i in range(0,len(emotion_result)):
    if emotion_result[i] == ground_truth[i] :  count += 1
    fresult.write(emotion_result[i]+ " " + ground_truth[i] + "\n")

print(str(count))






#The loss are not decreasing.......even it is increasing.......
