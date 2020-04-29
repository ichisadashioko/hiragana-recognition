#!/usr/bin/env python3
import os
import sys
import time
import re
import json
import base64
import argparse
from typing import List, Dict, Iterable, Any

import tornado
from tornado.ioloop import IOLoop
from tornado.web import Application, RequestHandler, StaticFileHandler
import numpy as np

from serializable import *
from argtypes import *
from utils import *
from logger import *
from constants import *

import tensorflow as tf  # noqa: E402
# disable GPU because it takes too long for loading
tf.config.experimental.set_visible_devices([], 'GPU')  # noqa: E402

from tensorflow_utils import *  # noqa: E402


class Dataset:
    def __init__(
        self,
        name: str,
        metadata_filepath: str,
        tfrecord_filepath: str,
        metadata: DatasetMetadata,
    ):
        self.name = name
        self.metadata_filepath = metadata_filepath
        self.tfrecord_filepath = tfrecord_filepath
        self.metadata = metadata


datasets: List[Dataset] = []
images_cache: List[Dict[str, str]] = []


def find_dataset(name: str) -> Dataset:
    for dataset in datasets:
        if name == dataset.name:
            return dataset

    return None


def dataset_not_found(handler: RequestHandler, name: str):
    handler.clear()
    handler.set_status(404)
    handler.write({
        'message': f'Cannot find dataset {repr(name)}!'
    })


def save_metadata(metadata: DatasetMetadata, fpath: str):
    if os.path.exists(fpath):
        backup_file_by_modified_date(fpath)

    with open(fpath, mode='w', encoding='utf-8') as outfile:
        universal_dump(metadata.__dict__, outfile)


@measure_exec_time
def load_image(tfrecord_filepath: str, hash: str) -> bytes:
    if not os.path.exists(tfrecord_filepath):
        error(f'{tfrecord_filepath} does not exist!')
        return

    try:
        raw_dataset = tf.data.TFRecordDataset(tfrecord_filepath)
        records: Iterable[Dict[str, Any]] = raw_dataset.map(TFRSerDes.read_record)  # noqa

        for record in records:
            hash_feature = record[TFRSerDes.HASH_KEY]
            hash_bytes: bytes = hash_feature.numpy()
            record_hash = hash_bytes.decode(TFRSerDes.ENCODING)
            if hash == record_hash:
                image_data: bytes = record[TFRSerDes.IMAGE_KEY].numpy()

                return image_data
    except Exception as ex:
        error(repr(ex))
        traceback.print_exc()


@measure_exec_time
def load_images(tfrecord_filepath: str, hash_list: List[str]) -> List[Dict[str, str]]:
    """Get multiple images from the TFRecord file.

    This method will be more efficient than retrieving one image at a
    time because before shuffling records with the same labels will be
    next to each others.
    """
    if not os.path.exists(tfrecord_filepath):
        error(f'{tfrecord_filepath} does not exist!')
        return []

    remain_hashes = [hash for hash in hash_list]
    images = []
    try:
        raw_dataset = tf.data.TFRecordDataset(tfrecord_filepath)
        records: Iterable[Dict[str, Any]] = raw_dataset.map(TFRSerDes.read_record)  # noqa

        for record in records:
            if len(remain_hashes) > 0:
                hash_feature = record[TFRSerDes.HASH_KEY]
                hash_bytes: bytes = hash_feature.numpy()
                record_hash = hash_bytes.decode(TFRSerDes.ENCODING)
                if record_hash in remain_hashes:
                    image_data: bytes = record[TFRSerDes.IMAGE_KEY].numpy()

                    image = {
                        'hash': record_hash,
                        'data': base64.encodebytes(image_data).decode('utf-8'),
                    }

                    images.append(image)
                    remain_hashes.remove(record_hash)
            else:
                break

    except Exception as ex:
        error(repr(ex))
        traceback.print_exc()

    return images


class ListAvailableDatasets(RequestHandler):
    def get(self):
        dataset_names: List[str] = list(map(lambda dataset: dataset.name, datasets))  # noqa
        # put dataset with name starts with alphabet first because when
        # we create multiple datasets with the same source, they will be
        # backup by appending modified time (Unix time) as prefix

        latest_datasets = list(filter(lambda x: x[0].isalpha(), dataset_names))
        remain_datasets = set(dataset_names) - set(latest_datasets)

        response_list = []
        response_list.extend(latest_datasets)
        response_list.extend(remain_datasets)
        self.write({'datasets': response_list})


class GetDatasetInfo(RequestHandler):
    def get(self, name: str):
        debug(f'Dataset name: {repr(name)}')

        dataset = find_dataset(name)

        if dataset is None:
            dataset_not_found(self, name)
            return

        self.write({
            'name': dataset.name,
            'metadata': {
                'source': dataset.metadata.source,
                'content': dataset.metadata.content,
                'labels': dataset.metadata.labels,
                'invalid_records': dataset.metadata.invalid_records,
                'invalid_fonts': dataset.metadata.invalid_fonts,
                'completed_labels': dataset.metadata.completed_labels,
            },
        })


class GetLabelInfo(RequestHandler):
    def get(self, name: str, label: str):

        debug(f'Getting info for {repr(label)} in {repr(name)}')

        dataset = find_dataset(name)

        if dataset is None:
            dataset_not_found(self, name)
            return

        records = []
        for record in dataset.metadata.records:
            if record['char'] == label:
                records.append(record)

        self.write({
            'dataset': name,
            'label': label,
            'records': records,
        })


class MarkRecordAsInvalid(RequestHandler):
    """Mark a record as invalid by its hash id."""

    def get(self, name: str, hash: str):

        info(f'Marking {hash} in {name} as invalid!')

        dataset = find_dataset(name)

        if dataset is None:
            dataset_not_found(self, name)
            return

        metadata = dataset.metadata
        records = metadata.records

        for record in records:
            if record['hash'] == hash:
                metadata.invalid_records.append(hash)
                save_metadata(metadata, dataset.metadata_filepath)

                self.write({
                    'record': record,
                })

                return

        self.clear()
        self.set_status(404)
        self.write({
            'message': f'Cannot find record with hash {repr(hash)}!'
        })


class MarkRecordAsValid(RequestHandler):

    def get(self, name: str, hash: str):
        dataset = find_dataset(name)

        if dataset is None:
            dataset_not_found(self, name)
            return

        metadata = dataset.metadata
        invalid_records = metadata.invalid_records
        metadata.invalid_records = list(filter(lambda x: x != hash, invalid_records))  # noqa
        save_metadata(metadata, dataset.metadata_filepath)

        self.write({
            'message': f'Marked {repr(hash)} as valid record.',
        })


class MarkFontAsInvalid(RequestHandler):

    def get(self, name: str, font: str):
        dataset = find_dataset(name)

        if dataset is None:
            dataset_not_found(self, name)
            return

        metadata = dataset.metadata
        if font not in metadata.invalid_fonts:
            metadata.invalid_fonts.append(font)
            save_metadata(metadata, dataset.metadata_filepath)

        self.write({
            'message': f'Marked {font} as invalid.',
        })


class MarkFontAsValid(RequestHandler):

    def get(self, name: str, font: str):
        dataset = find_dataset(name)

        if dataset is None:
            dataset_not_found(self, name)
            return

        metadata = dataset.metadata
        invalid_fonts = metadata.invalid_fonts
        metadata.invalid_fonts = list(filter(lambda x: x != font, invalid_fonts))  # noqa
        save_metadata(metadata, dataset.metadata_filepath)

        self.write({
            'message': f'Marked {font} as valid.',
        })


class MarkLabelAsCompleted(RequestHandler):

    def get(self, name: str, label: str):
        dataset = find_dataset(name)

        if dataset is None:
            dataset_not_found(self, name)
            return

        metadata = dataset.metadata
        if label not in metadata.completed_labels:
            metadata.completed_labels.append(label)
            save_metadata(metadata, dataset.metadata_filepath)

        self.write({
            'message': f'Marked label {repr(label)} as done.',
        })


class MarkLabelAsIncompleted(RequestHandler):

    def get(self, name: str, label: str):
        dataset = find_dataset(name)

        if dataset is None:
            dataset_not_found(self, name)
            return

        metadata = dataset.metadata
        completed_labels = metadata.completed_labels
        metadata.completed_labels = list(filter(lambda x: x != label, completed_labels))  # noqa
        save_metadata(metadata, dataset.metadata_filepath)

        self.write({
            'messsage': f'Marked label {repr(label)} as not fully inspected.',
        })


class GetImageWithHash(RequestHandler):
    """Pull out a single image from TFRecord file."""

    def get(self, name: str, hash: str):

        dataset = find_dataset(name)

        if dataset is None:
            dataset_not_found(self, name)
            return

        image = load_image(dataset.tfrecord_filepath, hash)

        if image is not None:
            base64_image = base64.encodebytes(image).decode('utf-8')
            self.write({
                'image': base64_image,
            })

        else:
            self.clear()
            self.set_status(404)

            message = f'Cannot find image with hash {repr(hash)} in dataset {name}!'
            warn(message)

            self.write({
                'message': message,
            })


class GetImagesByHashes(RequestHandler):

    def bad_request(self, message: str):
        self.clear()
        self.set_status(400)  # Bad Request
        self.write({'message': message})

    def post(self, name):
        """Get images from dataset with list of image's hashes.

        name : dataset's name
        """
        body = self.request.body
        # debug(f'Request body: {body}')
        if len(body) == 0:
            self.bad_request('Request body must be a list of string!')
            return

        try:
            data = tornado.escape.json_decode(body)
        except Exception as ex:
            error(ex)
            traceback.print_exc()

            self.bad_request('Body data is not valid JSON data!')
            return

        if not isinstance(data, list):
            self.bad_request('Body data is not a list!')
            return

        for o in data:
            if not isinstance(o, str):
                self.bad_request('The list must only contain string!')
                return

        dataset = find_dataset(name)

        if dataset is None:
            dataset_not_found(self, name)
            return

        images = load_images(dataset.tfrecord_filepath, data)
        debug('Retrieved', len(images), 'images from', len(data), 'hashes.')
        self.write({'images': images})


class IndexHandler(RequestHandler):
    def get(self):
        self.redirect('/index.html')


def make_app():
    return Application(
        handlers=[
            (r'/api/datasets', ListAvailableDatasets),
            (r'/api/datasets/([^/]+)', GetDatasetInfo),
            (r'/api/datasets/([^/]+)/([^/]+)', GetLabelInfo),
            (r'/api/images/([^/]+)', GetImagesByHashes),
            (r'/api/record/invalid/([^/]+)/([^/]+)', MarkRecordAsInvalid),
            (r'/api/record/valid/([^/]+)/([^/]+)', MarkRecordAsValid),
            (r'/api/font/invalid/([^/]+)/([^/]+)', MarkFontAsInvalid),
            (r'/api/font/valid/([^/]+)/([^/]+)', MarkFontAsValid),
            (r'/api/label/complete/([^/]+)/([^/]+)', MarkLabelAsCompleted),
            (r'/api/label/incomplete/([^/]+)/([^/]+)', MarkLabelAsIncompleted),
            (r'/images/([^/]+)/([^/]+)', GetImageWithHash),
            (r'/', IndexHandler),
            (r'/(.*)', StaticFileHandler, {'path': './static'}),
        ],
        debug=True,
    )


def main():
    parser = argparse.ArgumentParser(
        description='Tornado web server for inspecting dataset.',
    )

    parser.add_argument(
        'port',
        default=3000,
        type=valid_port_number,
        action='store',
        nargs='?',
        help='Port to listening at [default: 3000]',
    )

    parser.add_argument(
        '-fd', '--fonts',
        dest='fonts_dir',
        type=directory,
        default=FONTS_DIR,
        required=False,
        help=(
            f'The directory that contains TrueType (.ttf) or OpenType '
            f'(.otf) font files. Default look up directory is '
            f'{repr(FONTS_DIR)}.'
        ),
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
    port = args.port

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
                metadata_filepath=metadata_filepath,
                tfrecord_filepath=tfrecord_filepath,
                metadata=metadata,
            )

        except Exception as ex:
            error(repr(ex))
            warn(f'Skipping {name}!')
            continue

        datasets.append(dataset)

    app = make_app()
    app.listen(port)

    try:
        info(f'Server starting at http://localhost:{port}/index.html')
        IOLoop.current().start()
    except Exception as ex:
        warn(repr(ex))

    info('Shutting down server.')
    IOLoop.current().stop()


if __name__ == '__main__':
    main()
