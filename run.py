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
from keras.layers import Convolution1D, MaxPooling1D
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
	for r in rows:
		for action in r['actions']:
			hand = action[1]
			if len(hand) <= max_features and len(hand) > 0:
				for played_card in action[-1]:
					tmp_hand = hand[:]

					if action[0] == 0:
						try:
							hand.remove(played_card)
						except:
							continue

					tmp_x = np.array([0]*(max_features-len(tmp_hand))+[c for c in tmp_hand if x_list is not None])
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

max_features = 50
batch_size   = 128
nb_epoch     = 12

num_classes = db.cards.count()

train_rows = db.logs.find({}).limit(training_num)
test_rows = db.logs.find({}).limit(testing_num).skip(training_num)


(X_train, y_train) = structurize_data(train_rows, max_features)
(X_test, y_test) = structurize_data(test_rows, max_features)

Y_train = np_utils.to_categorical(y_train, num_classes)
Y_test = np_utils.to_categorical(y_test, num_classes)


weights_file = 'seq_weights.h5'
architecture_file = 'seq_architecture.json'
model = None
if os.path.isfile(weights_file) and os.path.isfile(architecture_file) and '-r' not in sys.argv:
	print("Loading model...")
	with open(architecture_file) as af:
		model = model_from_json(af.read())
		model.load_weights(weights_file)
		model.compile(loss='categorical_crossentropy',
	              optimizer='adadelta',
	              metrics=['accuracy'])

else:
	print("Building model...")
	model = Sequential()

	model.add(Dense(output_dim=32, input_dim=max_features))
	#model.add(Dropout(0.2))
	model.add(Dense(output_dim=num_classes)) # All cards
	model.add(Activation('softmax'))

	model.compile(loss='categorical_crossentropy',
	              optimizer='adadelta',
	              metrics=['accuracy'])

	print("Training...")
	model.fit(X_train, Y_train, batch_size=batch_size, nb_epoch=nb_epoch,
	          verbose=1, validation_data=(X_test, Y_test))

	print("Saving model...")
	model_json_string = model.to_json()
	with open(architecture_file, 'w') as af:
		af.write(model_json_string)
		model.save_weights(weights_file, overwrite=True)

print("Testing...")
score = model.evaluate(X_test, Y_test, verbose=1)
print('Test score:', score[0])
print('Test accuracy:', score[1])




print("Script took: {0:2f} seconds".format(time.time()-start_time))
