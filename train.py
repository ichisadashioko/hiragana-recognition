#!/usr/bin/env python3
# encoding=utf-8
import os
import io
import json
import hashlib
from typing import Dict, List

import numpy as np
import PIL
import PIL.Image

import tensorflow as tf

def fetch_image_data(records: List[Dict], packed_image_filepath: str):
    sorted_records = [*records]
    sorted_records.sort(key=lambda record: record['seek_start'])

    with open(packed_image_filepath, mode='rb') as infile:
        last_seek_end = -1
        for record in sorted_records:
            seek_start: int = record['seek_start']
            seek_end: int = record['seek_end']
            image_data_size = seek_end - seek_start

            if last_seek_end != seek_start:
                infile.seek(seek_start)

            image_data = infile.read(image_data_size)
            record['image_data'] = image_data

            last_seek_end = seek_end

def main():
    metadata_filepath = 'metadata.json'
    packed_image_filepath = 'images.bin'
    labeling_filepath = 'japanese-characters.txt'

    if not os.path.exists(metadata_filepath):
        raise Exception(metadata_filepath + ' does not exist!')

    if not os.path.exists(packed_image_filepath):
        raise Exception(packed_image_filepath + ' does not exist!')

    if not os.path.exists(labeling_filepath):
        raise Exception(labeling_filepath + ' does not exist!')

    ####################################################################

    labeling_content = open(labeling_filepath, mode='rb').read()

    # hash label file for identifying if the trained model is compatible with a specific label file
    label_file_hash = hashlib.sha256(labeling_content).hexdigest()

    labeling_content = labeling_content.decode('utf-8')

    labeling_lines = labeling_content.splitlines()
    labeling_lines = list(filter(lambda x: len(x) > 0, labeling_lines))

    label_list = []
    for line in labeling_lines:
        rows = line.split('\t')
        if len(rows) > 1:
            main_label_chars = rows[0]
            sub_label_chars = rows[1]
            label_chars = main_label_chars + sub_label_chars
        else:
            main_label_chars = rows[0]
            sub_label_chars = ''
            label_chars = main_label_chars

        label_entry = {
            'label_chars': label_chars,
            'main_label_chars': main_label_chars,
            'sub_label_chars': sub_label_chars,
        }

        label_list.append(label_entry)

    label_to_index = {}

    num_outputs = len(label_list)

    for i in range(num_outputs):
        label_chars = label_list[i]['label_chars']

        for c in label_chars:
            if c in label_to_index:
                raise Exception(f'Duplicated character {c}!')
            else:
                label_to_index[c] = i

    ####################################################################

    metadata_content = open(metadata_filepath, mode='rb').read()
    metadata_content = metadata_content.decode('utf-8')

    dataset_metadata: Dict[str, List[dict]] = json.loads(metadata_content)
    records = dataset_metadata['records']
    fetch_image_data(records, packed_image_filepath)

    train_images = []
    train_labels = []

    input_shape = (64, 64, 1)

    for record in records:
        label_char = record['char']
        image_bs: bytes = record['image_data']

        label_idx = label_to_index[label_char]
        train_labels.append(label_idx)

        buffer = io.BytesIO(image_bs)
        pil_image = PIL.Image.open(buffer)
        np_image = np.array(pil_image, dtype=np.uint8)
        np_image = np.reshape(np_image, input_shape)
        train_images.append(np_image)

    train_images = np.array(train_images)
    train_labels = np.array(train_labels)

    ####################################################################

    model = tf.keras.Sequential([
        tf.keras.layers.Conv2D(
            filters=32,
            kernel_size=16,
            activation=tf.keras.activations.relu,
            input_shape=input_shape,
            data_format='channels_last',
        ),
        tf.keras.layers.MaxPool2D(
            pool_size=2,
        ),
        tf.keras.layers.Dropout(
            rate=0.4,
        ),
        ################################################################
        tf.keras.layers.Conv2D(
            filters=64,
            kernel_size=8,
            activation=tf.keras.activations.relu,
        ),
        tf.keras.layers.MaxPool2D(
            pool_size=2,
        ),
        ################################################################
        tf.keras.layers.Flatten(),
        tf.keras.layers.Dense(
            units=64,
            activation=tf.keras.activations.relu,
        ),
        tf.keras.layers.Dense(
            units=num_outputs,
            activation=tf.keras.activations.relu,
        ),
    ])

    optimizer = tf.keras.optimizers.Adam(
        learning_rate=0.001,
        beta_1=0.9,
        beta_2=0.999,
        epsilon=1e-07,
        amsgrad=False,
    )

    loss_fn = tf.keras.losses.SparseCategoricalCrossentropy(
        from_logits=True,
    )

    model.compile(
        optimizer=optimizer,
        loss=loss_fn,
        metrics=['accuracy'],
    )

    model.summary()

if __name__ == '__main__':
    main()
