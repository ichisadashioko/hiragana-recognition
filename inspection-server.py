import os
import sys
import time
import re
import json
import argparse

from tornado.ioloop import IOLoop
from tornado.web import Application, RequestHandler, StaticFileHandler

import numpy as np
import tensorflow as tf

from constants import *
from logger import *
from utils import *
from argtypes import *
from serializable import *

datasets = []


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


class IndexHandler(RequestHandler):
    def get(self):
        self.redirect('/index.html')


def make_app():
    return Application(
        handlers=[
            (r'/api/datasets', DatasetsApi),
            (r'/api/datasets/([^/]+)?', DatasetApi),
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
