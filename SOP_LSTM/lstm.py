import pandas
from math import sqrt
from numpy import array
from numpy import hstack
from numpy import reshape
import keras
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error
import sklearn.model_selection as model_selection
from matplotlib import pyplot as plt
from sklearn.preprocessing import StandardScaler

# evaluate one or more weekly forecasts against expected values
def evaluate_forecasts(actual, predicted):
	scores = list()
	# calculate an RMSE score for each day
	for i in range(actual.shape[1]):
		# calculate mse
		mse = mean_squared_error(actual[:, i], predicted[:, i])
		# calculate rmse
		rmse = sqrt(mse)
		# store
		scores.append(rmse)
	# calculate overall RMSE
	s = 0
	for row in range(actual.shape[0]):
		for col in range(actual.shape[1]):
			s += (actual[row, col] - predicted[row, col])**2
	score = sqrt(s / (actual.shape[0] * actual.shape[1]))
	return score, scores

# split a multivariate sequence into samples
def split_sequences(sequences, output, n_steps):
	X, y = list(), list()
	for i in range(len(sequences)):
		end_ix = i + n_steps
		if end_ix >= len(sequences):
			break
		seq_x = sequences[i:end_ix]
		seq_y = output[end_ix]
		X.append(seq_x)
		y.append(seq_y)
	return array(X), array(y)
	
road = [] # data of road segments
ts = [] # timeslots
vel = [] # velocities for corresponding timeslots and road segemtns
for i in range(5):
	road.append(pandas.read_excel('Data.xlsx', sheet_name='Road'+str(i+1)))
	ts.append(road[i]["Timeslot"].tolist())
	vel.append(road[i]["Velocity"].tolist())

# print(len(ts),len(ts[0]))

avel = [[] for i in range(5)] # list of average velocities

for i in range(5):
	initT = ts[i][0]
	# print(initT)
	sum = 0
	cnt = 0
	for (t,v) in zip(ts[i],vel[i]):
		if initT == t:
			sum = sum + v
			cnt = cnt + 1
		else:
			if cnt != 0:
				avel[i].append(sum/cnt)
			else:
				avel[i].append(0)
			initT = t
			sum = v
			cnt = 1
	if cnt !=0:
		avel[i].append(sum/cnt)
	else:
		avel[i].append(0)

for i in range(5):
	avel[i] = array(avel[i])
	avel[i] = avel[i].reshape((len(avel[i]), 1))

idata = hstack((avel[0],avel[1],avel[2],avel[3],avel[4]))
n_steps = 50 # timesteps
n_features = 5 # will be the number of road segments

# normalize the dataset
scaler = MinMaxScaler(feature_range=(0, 1))
idata = scaler.fit_transform(idata)
print(idata[0])

X, y = split_sequences(idata,idata,n_steps)
# print(X[-1],y[-1])

# Split to train and test
train_X, test_X, train_y, test_y = model_selection.train_test_split(X, y, train_size=0.65,test_size=0.35, random_state=99)
print(train_X.shape,train_y.shape)
print(test_X.shape,test_y.shape)
print(len(test_X))

# define model
model = keras.models.Sequential()
model.add(keras.layers.LSTM(units = 200, activation='relu', input_shape=(n_steps, n_features)))
model.add(keras.layers.Dense(5))
model.compile(optimizer='adam', loss='mse')
print(model.summary())

history = model.fit(train_X, train_y, epochs=20, batch_size=int(len(train_X)/5), validation_data=(test_X, test_y), verbose=2, shuffle=False)

# summarize history for loss
plt.plot(history.history['loss'])
plt.plot(history.history['val_loss'])
plt.title('model loss')
plt.ylabel('loss')
plt.xlabel('epoch')
plt.legend(['train', 'validation'], loc='upper left')
plt.show()

actual_val = list()
predicted_val = list()

#predict a sample from test
for i in range(len(test_X)):
	inp = test_X[i]
	actual = test_y[i]
	inp = inp.reshape(1,n_steps,n_features)
	predicted = model.predict(inp)
	actual = reshape(actual,(1,-1))
	predicted = reshape(predicted,(1,-1))
	actual = scaler.inverse_transform(actual)
	predicted = scaler.inverse_transform(predicted)
	actual = actual[0]
	predicted = predicted[0]
	actual_val.append(actual)
	predicted_val.append(predicted)
	if i%1000 == 0:
		print("Predicted output : ",predicted)
		print("Actual output : ",actual)


predicted_val = array(predicted_val)
actual_val = array(actual_val)

print(actual_val.shape,predicted_val.shape)

score, scores = evaluate_forecasts(actual_val, predicted_val)
print("TOTAL RMSE: ",score)
