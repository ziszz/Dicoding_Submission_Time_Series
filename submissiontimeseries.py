# -*- coding: utf-8 -*-
"""SubmissionTimeSeries.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1r7zsdOOJ3LU85qLwCUOstrMyeheSmYqr
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import tensorflow as tf
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler

df = pd.read_csv('AEP_hourly.csv')
df.info()

df

dates = df['Datetime'].values
label = df['AEP_MW'].values
label = label.reshape(-1,1)

plt.figure(figsize=(18,5))
plt.plot(dates, label)
plt.title('AEP_MW')

scaler = MinMaxScaler()
scaled_label = scaler.fit_transform(label)
scaled_label = scaled_label.reshape(1,-1)
scaled_label = np.hstack(scaled_label)

X_train, X_test, y_train, y_test = train_test_split(dates, scaled_label, test_size=0.2, random_state=1, shuffle=False)

def windowed_dataset(series, window_size, batch_size, shuffle_buffer):
    series = tf.expand_dims(series, axis=-1)
    ds = tf.data.Dataset.from_tensor_slices(series)
    ds = ds.window(window_size + 1, shift=1, drop_remainder=True)
    ds = ds.flat_map(lambda w: w.batch(window_size + 1))
    ds = ds.shuffle(shuffle_buffer)
    ds = ds.map(lambda w: (w[:-1], w[-1:]))
    return ds.batch(batch_size).prefetch(1)

skala_data = (max(scaled_label) - min(scaled_label)) * 0.1
print(skala_data)

class myCallback(tf.keras.callbacks.Callback):
    def on_epoch_end(self, epoch, logs={}):
        if (logs.get('mae') < skala_data) and (logs.get('val_mae') < skala_data):
            self.model.stop_training = True;
            print('\nMae telah dibawah 10% dari skala data yaitu {}'.format(skala_data))

callbacks = myCallback()

train_set = windowed_dataset(y_train, window_size=90, batch_size=100, shuffle_buffer=1000)
val_set = windowed_dataset(y_test, window_size=90, batch_size=100, shuffle_buffer=1000)

model = tf.keras.models.Sequential([
    tf.keras.layers.LSTM(60, return_sequences=True),
    tf.keras.layers.LSTM(60),
    tf.keras.layers.Dense(512, activation='relu'),
    tf.keras.layers.Dropout(0.5),
    tf.keras.layers.Dense(256, activation='relu'),
    tf.keras.layers.Dropout(0.5),
    tf.keras.layers.Dense(1),
    ])

optimizer = tf.keras.optimizers.SGD(learning_rate=1.000e-01, momentum=0.9)
model.compile(
    loss=tf.keras.losses.Huber(),
    optimizer=optimizer,
    metrics=['mae']
    )
hist = model.fit(
    train_set,
    epochs=100,
    validation_data=val_set,
    verbose=2,
    callbacks=[callbacks],
    )

plt.figure(figsize=(18,5))

plt.subplot(1,2,1)
plt.plot(hist.history['mae'])
plt.plot(hist.history['val_mae'])
plt.title('Model Mae')
plt.xlabel('Epochs')
plt.ylabel('Mae')
plt.legend(['train', 'test'], loc='upper left')

plt.subplot(1,2,2)
plt.plot(hist.history['loss'])
plt.plot(hist.history['val_loss'])
plt.title('Model Loss')
plt.xlabel('Epochs')
plt.ylabel('Loss')
plt.legend(['train', 'test'], loc='upper left')

plt.show()