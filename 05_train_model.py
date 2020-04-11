# encoding=utf-8
import os
import time
import re
import math

import numpy as np

import tensorflow as tf

import utils
import key_label_dict


if __name__ == "__main__":
    AUTOTUNE = tf.data.experimental.AUTOTUNE
    image_count = 1756
    batch_size = 64
    steps_per_epoch = math.ceil(image_count/batch_size)
    tfrecord_filename = 'hiragana_ds_2019-05-04_16-34-09.tfrecord'

    ds = utils.load_tfrecord(tfrecord_filename)

    ds = ds.cache()
    ds = ds.apply(tf.data.experimental.shuffle_and_repeat(
        buffer_size=image_count,
    ))
    ds = ds.batch(batch_size).prefetch(buffer_size=AUTOTUNE)

    model = utils.generic_cnn_model('HRGN')
    model.compile(
        optimizer='adam',
        loss='sparse_categorical_crossentropy',
        metrics=['accuracy'],
    )

    model.fit(
        ds,
        epochs=16,
        steps_per_epoch=steps_per_epoch
    )

    model_weights_filename = f'hiragana_model_weights_{utils.datetime_now()}.h5'
    model.save_weights(model_weights_filename)

    model_filename = f'hiragana_model_{utils.datetime_now()}.h5'
    model.save(model_filename)
