#!/usr/bin/env python3
# encoding=utf-8
import os
import json
import hashlib
from typing import Dict, List

import numpy as np
import PIL
import PIL.Image

def fetch_image_data(records: List[Dict], packed_image_filepath: str):
    sorted_records = [*records]
    sorted_records.sort(key=lambda record: record['seek_start'])

    with open(packed_image_filepath, mode='rb') as infile:
        last_seek_end = -1
        for record in sorted_records:
            seek_start: int = record['seek_start']
            seek_end: int = record['seek_end']
            image_data_size = seek_end - seek_start

            if last_seek_end != seek_start:
                infile.seek(seek_start)

            image_data = infile.read(image_data_size)
            record['image_data'] = image_data

            last_seek_end = seek_end

def main():
    metadata_filepath = 'metadata.json'
    packed_image_filepath = 'images.bin'
    labeling_filepath = 'japanese-characters.txt'

    if not os.path.exists(metadata_filepath):
        raise Exception(metadata_filepath + ' does not exist!')

    if not os.path.exists(packed_image_filepath):
        raise Exception(packed_image_filepath + ' does not exist!')

    if not os.path.exists(labeling_filepath):
        raise Exception(labeling_filepath + ' does not exist!')

    ####################################################################

    labeling_content = open(labeling_filepath, mode='rb').read()

    # hash label file for identifying if the trained model is compatible with a specific label file
    label_file_hash = hashlib.sha256(labeling_content).hexdigest()

    labeling_content = labeling_content.decode('utf-8')

    labeling_lines = labeling_content.splitlines()
    labeling_lines = list(filter(lambda x: len(x) > 0, labeling_lines))

    label_list = []
    for line in labeling_lines:
        rows = line.split('\t')
        if len(rows) > 1:
            main_label_chars = rows[0]
            sub_label_chars = rows[1]
            label_chars = main_label_chars + sub_label_chars
        else:
            main_label_chars = rows[0]
            sub_label_chars = ''
            label_chars = main_label_chars

        label_entry = {
            'label_chars': label_chars,
            'main_label_chars': main_label_chars,
            'sub_label_chars': sub_label_chars,
        }

        label_list.append(label_entry)

    label_to_index = {}

    for i in range(len(label_list)):
        label_chars = label_list[i]['label_chars']

        for c in label_chars:
            if c in label_to_index:
                raise Exception(f'Duplicated character {c}!')
            else:
                label_to_index[c] = i

    print(len(label_to_index.keys()))
    return

    ####################################################################

    metadata_content = open(metadata_filepath, mode='rb').read()
    metadata_content = metadata_content.decode('utf-8')

    dataset_metadata: Dict[str, List[dict]] = json.loads(metadata_content)
    records = dataset_metadata['records']
    fetch_image_data(records, packed_image_filepath)


    train_images = []
    train_labels = []

if __name__ == '__main__':
    main()