# encoding=utf-8
import os
import time
import re
import math

import numpy as np
import pandas

import utilities
import key_label_dict

if __name__ == "__main__":
    cache_filename = 'image_paths.csv'
    df = pandas.read_csv(cache_filename)
    np_df = df.values

    all_labels = np_df[:, 0]
    all_image_paths = np_df[:, 1]

    tfrecord_filename = f'hiragana_ds_{utilities.datetime_now()}.tfrecord'

    utilities.convert_to_tfrec(all_image_paths, all_labels, tfrecord_filename)
