# encoding=utf-8
import os
import re
import time
import io
from contextlib import redirect_stdout

import numpy as np
import pandas

if __name__ == "__main__":
    csv_filename = '01_character_list.csv'
    df = pandas.read_csv(csv_filename, header=None)

    np_df = df.values

    label_dict = {label: key for key, label in np_df}
    key_dict = {key: label for key, label in np_df}

    py_dict_filename = 'key_label_dict.py'
    with open(py_dict_filename, 'w', encoding='utf-8') as f:
        f.write('# encoding=utf-8\n')

        f.write('key_dict = ')
        with io.StringIO() as buffer, redirect_stdout(buffer):
            print(key_dict)
            f.write(buffer.getvalue())

        f.write('label_dict = ')
        with io.StringIO() as buffer, redirect_stdout(buffer):
            print(label_dict)
            f.write(buffer.getvalue())
