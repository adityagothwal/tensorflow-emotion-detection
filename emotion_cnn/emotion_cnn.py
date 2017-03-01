import tensorflow as tf
import matplotlib.pyplot as plt
import numpy as np

###################
emotion_name = ["anger", "disgust", "fear", "happy", "sad", "surprise", "neutral"]

###################NEURAL NETWORK PROPERTIES

n_examples = 28709
n_classes = 7

capacity = 2000
batch_size = 500
min_after_dequeue = 1000
hm_epochs = 10

###################TENSORFLOW
x = tf.placeholder('float', [None, 2304]) #48*48=2304
y = tf.placeholder('float',[None, n_classes])


keep_rate = 0.8
keep_prob = tf.placeholder(tf.float32)

def conv2d(x, W):
	return tf.nn.conv2d(x, W, strides=[1, 1, 1, 1], padding='SAME')

def maxpool2d(x):
	return tf.nn.max_pool(x, ksize=[1, 2, 2, 1], strides=[1, 2, 2,1], padding='SAME')

def conv_neural_network_model(data):
	weights = {'W_conv1': tf.Variable(tf.random_normal([5, 5, 1, 32])),
				'W_conv2': tf.Variable(tf.random_normal([5, 5, 32, 64])),
				'W_fc': tf.Variable(tf.random_normal([12*12*64, 1024])),
				'out': tf.Variable(tf.random_normal([1024, n_classes]))}
	biases = {'b_conv1': tf.Variable(tf.random_normal([32])),
				'b_conv2': tf.Variable(tf.random_normal([64])),
				'b_fc': tf.Variable(tf.random_normal([1024])),
				'out': tf.Variable(tf.random_normal([n_classes]))}
	x = tf.reshape(data, shape=[-1, 48, 48, 1])
	conv1 = conv2d(x, weights['W_conv1']) + biases['b_conv1']
	conv1 = maxpool2d(conv1)
	conv2 = conv2d(conv1, weights['W_conv2']) + biases['b_conv2']
	conv2 = maxpool2d(conv2)

	fc = tf.reshape(conv2, [-1, 12*12*64])
	fc = tf.nn.relu(tf.matmul(fc, weights['W_fc'])+biases['b_fc'])
	fc = tf.nn.dropout(fc, keep_rate)
	output = tf.matmul(fc, weights['out'])+biases['out']

	return output

result = conv_neural_network_model(x)

def val_to_one_hot(x):
	ans = np.array([0, 0, 0, 0, 0, 0, 0])
	ans[x]=1
	return ans

def plot_image(images, emotion_num, prediction, prediction_best_guess):
	images = np.reshape(images, [48, 48])
	plt.figure().suptitle("correct emotion: " + emotion_name[emotion_num] + "\n" + "best guess: " + emotion_name[prediction_best_guess], fontsize=14, fontweight='bold')
	#print(tf.to_float(prediction[0:1]))
	for k in range(n_classes):
		plt.text(-15, 10+3*k, str(emotion_name[k]) + ": " + str(prediction[0][k]), fontsize=12)
	plt.imshow(images, cmap='gray')
	plt.show()

def plot_image_no_pred(images, emotion_num):
	images = np.reshape(images, [48, 48])
	plt.figure().suptitle("correct emotion: " + emotion_name[emotion_num], fontsize=14, fontweight='bold')
	plt.imshow(images, cmap='gray')
	plt.show()

filename_queue = tf.train.string_input_producer(['train.csv'])
reader = tf.TextLineReader(skip_header_lines=1) #skip_header_lines=1
_, csv_row = reader.read(filename_queue)
record_defaults = [[0], [""]]
emotion, pixel_array = tf.decode_csv(csv_row, record_defaults=record_defaults)

emotion_batch, pixel_array_batch = tf.train.shuffle_batch(
      [emotion, pixel_array], batch_size=batch_size, capacity=capacity,
      min_after_dequeue=min_after_dequeue)

prediction = conv_neural_network_model(x)
normalized_prediction = tf.nn.softmax(conv_neural_network_model(x))
cost = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(logits=prediction, labels=y))
train_step = tf.train.AdamOptimizer().minimize(cost)

with tf.Session() as sess:
	tf.global_variables_initializer().run()
	coord = tf.train.Coordinator()
	threads = tf.train.start_queue_runners(coord=coord)

	## DO A TRAIN
	for epoch in range(hm_epochs):
		epoch_loss = 0
		for batch in range(int(n_examples/batch_size)):
			cur_emotion_batch, cur_pixel_array_batch = sess.run([emotion_batch, pixel_array_batch])		
			append_matrix_emotion = list()
			append_matrix_name = list()
			for item in range(batch_size):
				cur_pixel_array_batch[item] = np.fromstring(cur_pixel_array_batch[item], dtype=int, sep=" ")
				append_matrix_emotion.append(cur_pixel_array_batch[item])
				append_matrix_name.append(val_to_one_hot(cur_emotion_batch[item]))
			_, c = sess.run([train_step, cost], feed_dict = {x: np.array(append_matrix_emotion), y: np.array(append_matrix_name)}) #np.reshape(cur_pixel_array_batch[item], [1, 2304])
			epoch_loss += c	
		print('Epoch', epoch+1, 'completed out of', hm_epochs, 'loss:', epoch_loss)
		
	## DO AN ACCURACY PRINT
	cur_emotion_batch, cur_pixel_array_batch = sess.run([emotion_batch, pixel_array_batch])	
	accuracy = 0	
	append_matrix_emotion = list()
	append_matrix_name = list()	
	for item in range(batch_size):
		cur_pixel_array_batch[item] = np.fromstring(cur_pixel_array_batch[item], dtype=int, sep=" ")
		value = sess.run(prediction, feed_dict={x: np.array([cur_pixel_array_batch[item]] , dtype=np.float32)})
		if cur_emotion_batch[item] == np.argmax(value[0]):
			accuracy+=1
	print("Correct:", str(accuracy)+"/"+str(batch_size), "Accuracy:", accuracy/batch_size)
	
	## DO A VISUALIZE
	cur_emotion_batch, cur_pixel_array_batch = sess.run([emotion_batch, pixel_array_batch])	
	accuracy = 0	
	append_matrix_emotion = list()
	append_matrix_name = list()	
	for item in range(min(10, batch_size)):
		cur_pixel_array_batch[item] = np.fromstring(cur_pixel_array_batch[item], dtype=int, sep=" ")
		value = sess.run(prediction, feed_dict={x: np.array([cur_pixel_array_batch[item]] , dtype=np.float32)})
		plot_image(cur_pixel_array_batch[item], cur_emotion_batch[item], value, np.argmax(value[0]))

	coord.request_stop()
	coord.join(threads)