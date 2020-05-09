# I put all tensorflow utilities in this file so that some file don't
# use tensorflow module would not have to wait for importing the huge
# tensorflow module.

# I think `tensorflow_utils` is more readable than `tensorflowutils` or
# `tfutils`

import tensorflow as tf

from constants import *
from logger import *
from utils import *

# http://web.archive.org/web/20200322091949/https://www.tensorflow.org/tutorials/load_data/tfrecord
# The following functions can be used to convert a value to a type
# compatible with tf.Example.


@measure_exec_time
def _bytes_feature(value):
    """Returns a bytes_list from a string / byte."""
    if isinstance(value, type(tf.constant(0))):
        # BytesList won't unpack a string from an EagerTensor.
        value = value.numpy()
    return tf.train.Feature(bytes_list=tf.train.BytesList(value=[value]))


@measure_exec_time
def _float_feature(value):
    """Returns a float_list from a float / double."""
    return tf.train.Feature(float_list=tf.train.FloatList(value=[value]))


@measure_exec_time
def _int64_feature(value):
    """Returns an int64_list from a bool / enum / int / uint."""
    return tf.train.Feature(int64_list=tf.train.Int64List(value=[value]))


class TFRSerDes:
    """TFRecord serializer/deserializer

    naming source: https://en.wikipedia.org/wiki/SerDes
    """
    ENCODING = 'utf-8'
    # a unique hash for each record by apply <> hashing a set of
    # properties and the timestamp at the creation time. This way we
    # can easily identify each records.
    HASH_KEY = 'HASH'
    CHARACTER_KEY = 'CHARACTER'
    IMAGE_WIDTH_KEY = 'WIDTH'
    IMAGE_HEIGHT_KEY = 'HEIGHT'
    IMAGE_DEPTH_KEY = 'DEPTH'
    IMAGE_KEY = 'PNG_IMAGE'
    FONT_SIZE_KEY = 'FONT_SIZE'
    FONT_NAME_KEY = 'FONT_NAME'
    DESCRIPTION_KEY = 'DESCRIPTION'

    FEATURE_DESC = {
        HASH_KEY: tf.io.FixedLenFeature([], tf.string),
        CHARACTER_KEY: tf.io.FixedLenFeature([], tf.string),
        IMAGE_WIDTH_KEY: tf.io.FixedLenFeature([], tf.int64),
        IMAGE_HEIGHT_KEY: tf.io.FixedLenFeature([], tf.int64),
        IMAGE_DEPTH_KEY: tf.io.FixedLenFeature([], tf.int64),
        IMAGE_KEY: tf.io.FixedLenFeature([], tf.string),
        FONT_SIZE_KEY: tf.io.FixedLenFeature([], tf.int64),
        FONT_NAME_KEY: tf.io.FixedLenFeature([], tf.string),
        DESCRIPTION_KEY: tf.io.FixedLenFeature([], tf.string),
    }

    @classmethod
    @measure_exec_time
    def serialize_record(
        cls,
        hash: str,
        character: str,
        width: int,
        height: int,
        depth: int,
        image: bytes,
        font_size: int,
        font_name: str,
        description: str,
    ) -> bytes:
        encoded_hash = hash.encode(cls.ENCODING)
        encoded_character = character.encode(cls.ENCODING)
        encoded_font_name = font_name.encode(cls.ENCODING)
        encoded_desc = description.encode(cls.ENCODING)

        # create a dictionary mappin the feature name to the
        # tf.Example-compatible data type.
        feature_dict = {
            cls.HASH_KEY: _bytes_feature(encoded_hash),
            cls.CHARACTER_KEY: _bytes_feature(encoded_character),
            cls.IMAGE_WIDTH_KEY: _int64_feature(width),
            cls.IMAGE_HEIGHT_KEY: _int64_feature(height),
            cls.IMAGE_DEPTH_KEY: _int64_feature(depth),
            cls.IMAGE_KEY: _bytes_feature(image),
            cls.FONT_SIZE_KEY: _int64_feature(font_size),
            cls.FONT_NAME_KEY: _bytes_feature(encoded_font_name),
            cls.DESCRIPTION_KEY: _bytes_feature(encoded_desc),
        }

        # create a Features message using tf.train.Example
        example_proto = tf.train.Example(
            features=tf.train.Features(feature=feature_dict),
        )

        return example_proto.SerializeToString()

    @classmethod
    @measure_exec_time
    def read_record(cls, example_proto):
        # Parse the input tf.Example proto using the feature description
        # dictionary
        # TODO Why we only use `parse_single_example`? There is also
        # `parse_sequence_example` method. Check to see if that makes
        # any improvement.
        return tf.io.parse_single_example(example_proto, cls.FEATURE_DESC)


def convert_to_tfrec(all_image_paths, all_labels, filename):
    with tf.python_io.TFRecordWriter(filename) as tfrec_writer:
        idx = 0
        start_time = time.time()
        for image_path, label in zip(all_image_paths, all_labels):
            # image_raw = tf.read_file(image_path)
            image_raw = open(image_path, 'rb').read()

            feature = {
                'image_raw': _bytes_feature(image_raw),
                'label': _int64_feature(label),
            }

            example = tf.train.Example(
                features=tf.train.Features(feature=feature))

            tfrec_writer.write(example.SerializeToString())

            idx += 1
            if idx % 1000 == 0:
                active_time = time.time() - start_time
                avg_time = active_time / (idx)
                remain_time = avg_time * (len(all_image_paths) - idx)
                print(f'{idx}/{len(all_image_paths)}')
                print(f'ACTIVE_TIME: {time_tostring(active_time)}')
                print(f'REMAIN_TIME: {time_tostring(remain_time)}')
                print(f'AVG_TIME: {avg_time:.4f}s')
                print('='*32)


def load_tfrecord(filename: str):
    tfrec_ds = tf.data.TFRecordDataset(filename)

    def _parse_image_function(example_proto):
        # Create a dictionary describing the features
        image_feature_description = {
            'image_raw': tf.FixedLenFeature([], tf.string),
            'label': tf.FixedLenFeature([], tf.int64),
        }
        # Parse the input tf.Example proto using the dictionary above
        return tf.parse_single_example(example_proto, image_feature_description)

    ds = tfrec_ds.map(_parse_image_function)

    def preprocess_image(tf_image):
        tf_image = tf.image.decode_png(tf_image, channels=1)
        tf_image = tf.image.resize_images(tf_image, [64, 64])
        tf_image = tf_image / 255.0
        return tf_image

    def preprocess_image_label_tfrecord(tfrec_features):
        image_raw = tfrec_features['image_raw']
        label = tfrec_features['label']
        return preprocess_image(image_raw), label

    ds = ds.map(preprocess_image_label_tfrecord)

    return ds


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
