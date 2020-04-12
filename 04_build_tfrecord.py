# encoding=utf-8
import os
import time
import re
import math

import numpy as np
import pandas

import utils
from tensorflow_utils import convert_to_tfrec
import key_label_dict

if __name__ == "__main__":
    cache_filename = 'image_paths.csv'
    df = pandas.read_csv(cache_filename)
    np_df = df.values

    all_labels = np_df[:, 0]
    all_image_paths = np_df[:, 1]

    tfrecord_filename = f'hiragana_ds_{int(time.time())}.tfrecord'

    convert_to_tfrec(all_image_paths, all_labels, tfrecord_filename)
