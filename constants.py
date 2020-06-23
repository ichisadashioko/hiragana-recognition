import os
import time

# `~!@#$%^&*,<>?'":;|\/
INVALID_FILENAME_CHARS = '`~!@#$%^&*,<>?\'":;|\\/'

LOG_DIRECTORY = 'log'
LOG_SUFFIX = '-runtime.log'
COLUMN_SEPARATOR = '\t'
LOG_HEADER = ('func_name', 'start_time', 'end_time')
MODULE_IMPORT_TIME = int(time.time())
LOG_FILEPATH = os.path.join(LOG_DIRECTORY, f'{MODULE_IMPORT_TIME}{LOG_SUFFIX}')

# start to be used in `generate-output-mapping.py`
LABEL_FILENAME = 'labels.json'

# start to be used in `create-dataset.py`
DATASETS_DIR = 'datasets'
SERIALIZED_DATASET_FILENAME = 'dataset.xformat'
METADATA_FILENAME = 'metadata.json'
INSPECTED_DATASET_FILENAME = 'inspected-dataset.tfrecord'
FONTS_DIR = 'fonts'
FONT_SIZE = 64
IMAGE_SIZE = 64
