#!/usr/bin/env python3
# encoding=utf-8
import os
import time
import json
import argparse
from typing import List, Dict

from tqdm import tqdm
import numpy as np
import cv2
import tensorflow as tf

from constants import *
from serializable import *
from argtypes import *
from logger import *
from utils import *
from tensorflow_utils import *

char2index: Dict[str, int] = {}


def list_datasets(datasets: List[Dataset]):
    for idx, ds in enumerate(datasets):
        print(f'{idx} - {ds.name}')


@measure_exec_time
def process_image_data(image_data: bytes, width: int, height: int, channels: int):
    buf = np.frombuffer(image_data, dtype=np.uint8)
    image = cv2.imdecode(buf, cv2.IMREAD_UNCHANGED)
    image = image.reshape([height, width, channels])
    return image


@measure_exec_time
def process_record(record):
    # TensorFlow is implemented in C/C++ and Python wrapper is generated
    # at building time so typing is nearly non-existence when working
    # with TensorFlow.
    image_data = record[TFRSerDes.IMAGE_KEY].numpy()
    image_width = record[TFRSerDes.IMAGE_WIDTH_KEY].numpy()
    image_height = record[TFRSerDes.IMAGE_HEIGHT_KEY].numpy()
    image_depth = record[TFRSerDes.IMAGE_DEPTH_KEY].numpy()

    # TODO AttributeError: 'Tensor' object has no attribute 'numpy'
    # encoded_char: bytes = record[TFRSerDes.CHARACTER_KEY].numpy()
    # char = encoded_char.decode(TFRSerDes.ENCODING)

    # TODO TensorFlow is building execution graph so external references
    # are not allowed.
    # We may have to train the model in Jupyter Notebook where most of
    # TensorFlow features are executed eagerly.
    char = record[TFRSerDes.CHARACTER_KEY].numpy().decode(TFRSerDes.ENCODING)

    label = char2index[char]

    return process_image_data(image_data, image_width, image_height, image_depth), label


def train(
    ds: Dataset,
    optimizer='adam',
    loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True),
    epochs=10,
):
    global char2index

    char2index = {}
    for i in range(len(ds.metadata.labels)):
        char2index[ds.metadata.labels[i]] = i

    dataset_filepath = os.path.join(ds.path, INSPECTED_DATASET_FILENAME)
    if not os.path.exists(dataset_filepath):
        warn(f'Cannot find inspected dataset!')
        return

    raw_dataset = tf.data.TFRecordDataset(dataset_filepath)
    train_dataset = raw_dataset.map(TFRSerDes.read_record)

    xs = []
    ys = []

    info('Processing dataset...')
    for record in tqdm(train_dataset):
        x, y = process_record(record)
        xs.append(x)
        ys.append(y)

    info('Done loading dataset.')

    xs = np.array(xs, dtype=np.uint8)
    ys = np.array(ys)

    model_basename = ds.name

    if type(optimizer) == str:
        model_basename += f'_{optimizer}'

    if type(loss) == str:
        model_basename += f'_{loss}'

    num_outputs = len(ds.metadata.labels)
    # TODO input shape is hard-coded for simplicity
    input_shape = (IMAGE_SIZE, IMAGE_SIZE, 1)

    model = generic_cnn_model(
        prefix=ds.name,
        input_shape=input_shape,
        num_outputs=num_outputs,
    )

    model.compile(
        optimizer=optimizer,
        loss=loss,
        metrics=['accuracy'],
    )

    model.fit(
        x=(xs.astype(np.float32) / 255.0),
        y=ys,
        epochs=epochs,
    )


def main():
    parser = argparse.ArgumentParser(
        description='Train image recognition model.',
    )

    parser.add_argument(
        '--datasets-dir',
        dest='datasets_dir',
        type=directory,
        default=DATASETS_DIR,
        required=False,
        help=(
            'The directory that you used to store the dataset. '
            f'Default is {repr(DATASETS_DIR)}.'
        ),
    )

    args = parser.parse_args()
    datasets_dir = args.datasets_dir
    datasets = []

    dataset_dirs = os.listdir(datasets_dir)
    for name in dataset_dirs:
        try:
            dataset_dir = os.path.join(datasets_dir, name)

            metadata_filepath = os.path.join(dataset_dir, METADATA_FILENAME)
            serialized_dataset_filepath = os.path.join(dataset_dir, SERIALIZED_DATASET_FILENAME)

            json_obj = json.load(open(
                metadata_filepath,
                mode='r',
                encoding='utf-8',
            ))

            metadata = DatasetMetadata.parse_obj(json_obj)

            dataset = Dataset(
                name=name,
                path=dataset_dir,
                metadata_filepath=metadata_filepath,
                serialized_dataset_filepath=serialized_dataset_filepath,
                metadata=metadata,
            )

        except Exception as ex:
            error(repr(ex))
            warn(f'Skipping {name}!')
            continue

        datasets.append(dataset)

    while True:
        list_datasets(datasets)
        option = input('Choose dataset to train model (q to quit): ')

        if option == 'q':
            break

        try:
            index = int(option)
        except:
            continue

        if (index < 0) or not (index < len(datasets)):
            continue

        info(f'Starting to remove invalid records from {datasets[index].name}')
        ds = datasets[index]
        train(ds)


if __name__ == '__main__':
    main()
