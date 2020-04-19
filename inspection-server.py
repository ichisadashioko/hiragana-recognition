import os
import sys
import time
import re
import json
import base64
import argparse
from typing import List, Dict, Iterable, Any

from tornado.ioloop import IOLoop
from tornado.web import Application, RequestHandler, StaticFileHandler

import numpy as np
import tensorflow as tf

from constants import *
from logger import *
from utils import *
from argtypes import *
from serializable import *
from tensorflow_utils import *

datasets = []
images_cache: List[Dict[str, str]] = []


class Dataset:
    def __init__(
        self,
        name: str,
        metadata_filepath: str,
        tfrecord_filepath: str,
        dataset_metadata: DatasetMetadata,
    ):
        self.name = name
        self.metadata_filepath = metadata_filepath
        self.tfrecord_filepath = tfrecord_filepath
        self.dataset_metadata = dataset_metadata


class DatasetsApi(RequestHandler):
    def get(self):
        dataset_names = list(map(lambda dataset: dataset.name, datasets))
        self.write({'datasets': dataset_names})


class DatasetApi(RequestHandler):
    def get(self, name: str):
        debug(f'Dataset name: {repr(name)}')

        for dataset in datasets:
            if name == dataset.name:
                self.write({
                    'name': dataset.name,
                    'metadata': {
                        'source': dataset.dataset_metadata.source,
                        'content': dataset.dataset_metadata.content,
                        'labels': dataset.dataset_metadata.labels,
                    },
                })

                return

        self.clear()
        self.set_status(404)
        self.write({
            'message': f'Cannot find dataset {repr(name)}!'
        })


class LabelInfoApi(RequestHandler):
    def get(self, dataset_name: str, label: str):

        debug(f'Getting info for {repr(label)} in {repr(dataset_name)}')

        for dataset in datasets:
            if dataset_name == dataset.name:
                records = []
                for record in dataset.dataset_metadata.records:
                    if record['char'] == label:
                        records.append(record)

                self.write({
                    'dataset': dataset_name,
                    'label': label,
                    'records': records,
                })
                return

        self.clear()
        self.set_status(404)
        self.write({
            'message': f'Cannot find dataset {repr(name)}!'
        })


@measure_exec_time
def load_image(tfrecord_filepath: str, image_hash: str) -> bytes:
    if not os.path.exists(tfrecord_filepath):
        error(f'{tfrecord_filepath} does not exist!')
        return

    try:
        raw_dataset = tf.data.TFRecordDataset(tfrecord_filepath)
        records: Iterable[Dict[str, Any]] = raw_dataset.map(
            TFRSerDes.read_record
        )

        for record in records:
            hash_feature = record[TFRSerDes.HASH_KEY]
            hash_bytes: bytes = hash_feature.numpy()
            record_hash = hash_bytes.decode(TFRSerDes.ENCODING)
            if image_hash == record_hash:
                image_data: bytes = record[TFRSerDes.IMAGE_KEY].numpy()

                return image_data
    except Exception as ex:
        error(repr(ex))
        traceback.print_exc()


class ImageHandler(RequestHandler):
    def get(self, dataset_name, image_hash):
        for dataset in datasets:
            if dataset_name == dataset.name:

                image = load_image(dataset.tfrecord_filepath, image_hash)

                if image is not None:
                    base64_image = base64.encodebytes(image).decode('utf-8')
                    self.write({
                        'image': base64_image,
                    })

                else:
                    self.clear()
                    self.set_status(404)

                    message = f'Cannot find image with hash {repr(image_hash)} in dataset {dataset_name}!'
                    warn(message)

                    self.write({
                        'message': message,
                    })

                return

        self.clear()
        self.set_status(404)
        self.write({
            'message': f'Cannot find dataset {repr(dataset_name)}!'
        })


class IndexHandler(RequestHandler):
    def get(self):
        self.redirect('/index.html')


def make_app():
    return Application(
        handlers=[
            (r'/api/datasets', DatasetsApi),
            (r'/api/datasets/([^/]+)', DatasetApi),
            (r'/api/datasets/([^/]+)/([^/]+)', LabelInfoApi),
            (r'/images/([^/]+)/([^/]+)', ImageHandler),
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
            dataset_metadata = DatasetMetadata.parse_obj(json_obj)

            dataset = Dataset(
                name=name,
                metadata_filepath=metadata_filepath,
                tfrecord_filepath=tfrecord_filepath,
                dataset_metadata=dataset_metadata,
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
