from __future__ import print_function

import numpy as np
from pymongo import MongoClient
import sys
import time
import os

np.random.seed(1337)

from keras.preprocessing import sequence

from keras.models import Sequential, model_from_json
from keras.layers import Dense, Dropout, Activation, Flatten
from keras.layers import Convolution1D, MaxPooling1D
from keras.utils import np_utils

start_time = time.time()

client = MongoClient()
db = client.dominion

def structurize_data(rows, max_features):
	x,y = ([],[])
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
					x.append(np.array(tmp_hand))
					y.append(np.array([action[0], played_card]))
	# Convert to numpy array
	x = np.array(x)
	y = np.array(y)
	# Pad for equal length
	x = sequence.pad_sequences(x, maxlen=max_features)
	x = x.astype('float32')
	y = y.astype('float32')

	return (x,y)

training_num = 100
testing_num  = 10

max_features = 50
batch_size   = 120
nb_epoch     = 12

train_rows = db.logs.find({}).limit(training_num)
test_rows = db.logs.find({}).limit(testing_num).skip(training_num)
(X_train, y_train) = structurize_data(train_rows, max_features)
(X_test, y_test) = structurize_data(test_rows, max_features)

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

	model.add(Dense(output_dim=1, input_dim=50))
	model.add(Activation("relu"))
	model.add(Dense(output_dim=2))
	model.add(Activation("softmax"))

	model.compile(loss='categorical_crossentropy',
	              optimizer='adadelta',
	              metrics=['accuracy'])

	print("Training...")
	model.fit(X_train, y_train, batch_size=batch_size, nb_epoch=nb_epoch,
	          verbose=1, validation_data=(X_test, y_test))

	print("Saving model...")
	model_json_string = model.to_json()
	with open(architecture_file, 'w') as af:
		af.write(model_json_string)
		model.save_weights(weights_file, overwrite=True)

print("Testing...")
score = model.evaluate(X_test, y_test, verbose=1)
print('Test score:', score[0])
print('Test accuracy:', score[1])

pt = X_test[testing_num / 2]
pa = y_test[testing_num / 2]



print("Script took: {0:2f} seconds".format(time.time()-start_time))