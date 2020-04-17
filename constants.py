import os
import time

# `~!@#$%^&*,<>?'":;|\/
INVALID_FILENAME_CHARS = '`~!@#$%^&*,<>?\'":;|\\/'
DEFAULT_LABEL_FILE = 'labels.json'
DEFAULT_DATASET_BASENAME = 'dataset'
DATASET_EXTENSION = '.tfrecord'
DATASET_META_FILE_SUFFIX = '.meta.json'

LOG_DIRECTORY = 'log'
LOG_SUFFIX = '-runtime.log'
COLUMN_SEPARATOR = '\t'
LOG_HEADER = ('func_name', 'start_time', 'end_time')
MODULE_IMPORT_TIME = int(time.time())
LOG_FILEPATH = os.path.join(LOG_DIRECTORY, f'{MODULE_IMPORT_TIME}{LOG_SUFFIX}')
