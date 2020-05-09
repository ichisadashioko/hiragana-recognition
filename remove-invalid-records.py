#!/usr/bin/env python3
# encoding=utf-8

# After inspecting dataset and marking invalid records or fonts, we will
# need to remove them from the training/testing dataset.

import os
import time
import json
import argparse
from typing import List

from tqdm import tqdm
import tensorflow as tf  # noqa: E402
# disable GPU because it takes too long for loading
tf.config.experimental.set_visible_devices([], 'GPU')  # noqa: E402

from constants import *
from serializable import *
from argtypes import *
from logger import *
from utils import *
from tensorflow_utils import *


def list_datasets(datasets: List[Dataset]):
    for idx, ds in enumerate(datasets):
        print(f'{idx} - {ds.name}')


def remove_invalid_records(ds: Dataset, outfile: str):
    invalid_fonts = ds.metadata.invalid_fonts
    invalid_records = ds.metadata.invalid_records

    if os.path.exists(outfile):
        backup_file_by_modified_date(outfile)

    with tf.io.TFRecordWriter(outfile) as tfrecord_writer:
        # TODO shuffle records

        raw_dataset = tf.data.TFRecordDataset(ds.tfrecord_filepath)

        pbar = tqdm(raw_dataset)
        for raw_record in pbar:
            record = TFRSerDes.read_record(raw_record)

            hash_feature = record[TFRSerDes.HASH_KEY]
            hash_bytes: bytes = hash_feature.numpy()
            record_hash = hash_bytes.decode(TFRSerDes.ENCODING)

            font_name_feature = record[TFRSerDes.FONT_NAME_KEY]
            font_name_bytes: bytes = font_name_feature.numpy()
            font_name = font_name_bytes.decode(TFRSerDes.ENCODING)

            pbar.set_description(record_hash)

            if (font_name in invalid_fonts) or (record_hash in invalid_records):
                continue

            tfrecord_writer.write(raw_record.numpy())


def main():
    parser = argparse.ArgumentParser(
        description='Remove invalid records in the dataset.',
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
            tfrecord_filepath = os.path.join(dataset_dir, TFRECORD_FILENAME)

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
                tfrecord_filepath=tfrecord_filepath,
                metadata=metadata,
            )

        except Exception as ex:
            error(repr(ex))
            warn(f'Skipping {name}!')
            continue

        datasets.append(dataset)

    while True:
        list_datasets(datasets)
        option = input('Choose dataset to trim down (q to quit): ')

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
        remove_invalid_records(
            ds=ds,
            outfile=os.path.join(ds.path, INSPECTED_DATASET_FILENAME),
        )


if __name__ == '__main__':
    main()
