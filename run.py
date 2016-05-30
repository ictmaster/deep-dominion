from __future__ import print_function

import numpy as np
from pymongo import MongoClient
import sys
import time
import os
import random

np.random.seed(1337)

from keras.preprocessing import sequence

from keras.models import Sequential, model_from_json
from keras.layers import Dense, Dropout, Activation, Flatten
from keras.layers import Convolution1D, Convolution2D, MaxPooling1D, Embedding, Reshape
from keras.layers.recurrent import LSTM
from keras.utils import np_utils

start_time = time.time()

client = MongoClient()
db = client.dominion

def check_prediction(model, input_vector, answer):
	if np.argmax(model.predict(np.array([input_vector]))) == np.argmax(answer):
		return True
	return False

def structurize_data(rows, max_features):
	x_list,y_list = ([],[])
	for i,r in enumerate(rows):
		for j,action in enumerate(r['actions']):
			hand = action[1]
			if len(hand) <= max_features and len(hand) > 0:
				for played_card in action[-1]:
					tmp_hand = hand[:]

					if action[0] == 0:
						try:
							hand.remove(played_card)
						except:
							continue

					parsed_hand = [c for c in tmp_hand if c is not None and c < 243 and c >= 0]
					padding = [0]*(max_features-len(parsed_hand))
					tmp_x = np.array(padding+parsed_hand)

					x_list.append(tmp_x)
					y_list.append(np.array(played_card-1)) # TODO: somehow include this action[0]

	# Convert to numpy array
	x_list = np.array(x_list)
	y_list = np.array(y_list)
	x_list = x_list.astype('float32')
	y_list = y_list.astype('float32')
	return (x_list,y_list)

training_num = 10000
testing_num  = 100
skip_num = 0

max_features = 50
batch_size   = 128
nb_epoch     = 12

num_classes = db.cards.count()

train_rows = db.logs.find({}).limit(training_num).skip(skip_num)
test_rows = db.logs.find({}).limit(testing_num).skip(training_num+skip_num)

print("Structurizing training...")
(X_train, y_train) = structurize_data(train_rows, max_features)
print("Structurizing testing...")
(X_test, y_test) = structurize_data(test_rows, max_features)

Y_train = np_utils.to_categorical(y_train, num_classes)
X_train = X_train.astype('float32')
Y_test = np_utils.to_categorical(y_test, num_classes)
X_test = X_test.astype('float32')

def check_vals(l): # TODO: Remove debug function
	global parent_i
	global parent_l
	for i, val in enumerate(l):
		if hasattr(val, '__iter__'):
			parent_i = i
			parent_l = l
			check_vals(val)
		else:
			if val < 0 or val >= num_classes:
				if val < 0:
					parent_l[parent_i][i] = 0
				else:
					parent_l[parent_i][i] = num_classes-1

				print(parent_i, i, val)

weights_file = 'seq_weights.h5'
architecture_file = 'seq_architecture.json'
model = None
if os.path.isfile(weights_file) and os.path.isfile(architecture_file) and '-r' not in sys.argv:
	print("Loading model...")
	with open(architecture_file) as af:
		model = model_from_json(af.read())
		model.load_weights(weights_file)
		model.compile(loss='categorical_crossentropy', optimizer='adadelta', metrics=['accuracy'])

else:
	print("Building model...")

	model = Sequential()
	model.add(Embedding(num_classes, 128, input_length=max_features, dropout=0.5))
	model.add(LSTM(128, dropout_W=0.6, dropout_U=0.6))
	model.add(Dense(num_classes))
	model.add(Activation('softmax'))

	model.compile(loss='categorical_crossentropy', optimizer='adadelta', metrics=['accuracy'])

	print("Training...")
	model.fit(X_train, Y_train, batch_size=batch_size, nb_epoch=nb_epoch,
	          verbose=1, validation_data=(X_test, Y_test))

	print("Saving model...")
	model_json_string = model.to_json()
	with open(architecture_file, 'w') as af:
		af.write(model_json_string)
		model.save_weights(weights_file, overwrite=True)

#print("Testing...")
#score = model.evaluate(X_test, Y_test, verbose=1)
#print('Test score:', score[0])
#print('Test accuracy:', score[1])

#for x in X_test:
pr = model.predict(X_test, batch_size=batch_size)

actual_cards = []
predicted_cards = []

for x in pr:
	predicted_cards.append(np.argmax(x))
for x in Y_test:
	actual_cards.append(np.argmax(x))

act_dict = {}
for x in set(actual_cards):
	n = db.cards.find_one({'_id':x+1})['name']
	act_dict[n] = actual_cards.count(x)


with open('actual.dat', 'w') as f:
	for c in set(actual_cards):
		f.write("{}, {}\n".format(c, actual_cards.count(c)))

with open('predicted.dat', 'w') as f:
	for c in set(predicted_cards):
		f.write("{}, {}\n".format(c, predicted_cards.count(c)))



print("Script took: {0:2f} seconds".format(time.time()-start_time))
