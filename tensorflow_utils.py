import tensorflow as tf

from constants import *
from logger import *
from utils import *


def generic_cnn_model(prefix: str, input_shape: tuple, num_outputs: int):
    model = tf.keras.Sequential([
        tf.keras.layers.Conv2D(
            filters=32,
            kernel_size=16,
            activation=tf.nn.relu,
            name=f'{prefix}_Conv2D_1',
            input_shape=input_shape,
            data_format='channels_last',
        ),
        tf.keras.layers.MaxPool2D(
            pool_size=2,
            name=f'{prefix}_MaxPool2D_1',
        ),
        tf.keras.layers.Dropout(
            rate=0.4,
            name=f'{prefix}_Dropout_1',
        ),
        tf.keras.layers.Conv2D(
            filters=64,
            kernel_size=8,
            activation=tf.nn.relu,
            name=f'{prefix}_Conv2D_2',
        ),
        tf.keras.layers.MaxPool2D(
            pool_size=2,
            name=f'{prefix}_MaxPool2D_2',
        ),
        tf.keras.layers.Dropout(
            rate=0.2,
            name=f'{prefix}_Dropout_2',
        ),
        tf.keras.layers.Flatten(
            name=f'{prefix}_Flatten',
        ),
        tf.keras.layers.Dense(
            units=64,
            activation=tf.nn.relu,
            name=f'{prefix}_Dense_1',
        ),
        tf.keras.layers.Dense(
            units=num_outputs,
            activation=tf.nn.softmax,
            name=f'{prefix}_Output_layer',
        ),
    ])

    return model
