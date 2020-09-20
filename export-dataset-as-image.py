#!/usr/bin/env python3
# encoding=utf-8
import os
import io
import gc
import json
import math
import collections
import traceback
from typing import Dict, List

from tqdm import tqdm

import numpy as np
import PIL
import PIL.Image

import utils

def find_appropriate_width(n: int):
    x = math.sqrt(n)
    return math.ceil(x)

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


def free_image_data_for_memory(records: List[Dict]):
    for record in records:
        if 'image_data' in record:
            del record['image_data']

    gc.collect()

def main():
    metadata_filepath = 'metadata.json'
    packed_image_filepath = 'images.bin'

    if not os.path.exists(metadata_filepath):
        raise Exception(metadata_filepath + ' does not exist!')

    if not os.path.exists(packed_image_filepath):
        raise Exception(packed_image_filepath + ' does not exist!')

    metadata_bs = open(metadata_filepath, mode='rb').read()
    metadata_json_str = metadata_bs.decode('utf-8')
    dataset_metadata: Dict[str, List[dict]] = json.loads(metadata_json_str)
    records = dataset_metadata['records']

    categorized_records = collections.defaultdict(list)

    unicode_codepoints = []

    for record in records:
        char = record['char']
        categorized_records[char].append(record)
        unicode_codepoints.append(ord(char))

    tmp = map(lambda x: len(repr(x)), unicode_codepoints)
    num_pads = max(tmp)

    export_dir_filepath = 'exported_images'
    if os.path.exists(export_dir_filepath):
        utils.backup_file_by_modified_date(export_dir_filepath)

    os.makedirs(export_dir_filepath)

    categories = list(categorized_records.keys())
    pbar = tqdm(categories)
    for category in pbar:
        records = categorized_records[category]
        num_images = len(records)

        pbar.set_description(f'{category} - {num_images}')

        num_rows = find_appropriate_width(num_images)
        num_cols = math.ceil(num_images / num_rows)
        image_width = 64
        image_height = 64
        canvas_width = num_rows * image_width
        canvas_height = num_cols * image_height
        canvas = np.zeros(shape=(canvas_height, canvas_width), dtype=np.uint8)

        # make pattern to detect empty image slots that are not filled
        for i in range(canvas_height):
            for j in range(canvas_width):
                if (i % 2) == 0:
                    if (j % 2) == 0:
                        canvas[i,j] = 255
                else:
                    if (j % 2) != 0:
                        canvas[i,j] = 255

        fetch_image_data(records, packed_image_filepath)

        image_idx = 0
        for record in records:
            row = image_idx % num_rows
            col = math.floor(image_idx / num_rows)

            image_data: bytes = record['image_data']
            buffer = io.BytesIO(image_data)
            pil_image = PIL.Image.open(buffer)
            np_image = np.array(pil_image, dtype=np.uint8)

            top = col * image_height
            bottom = (col + 1) * image_width
            left = row * image_width
            right = (row+1) * image_width

            canvas[top:bottom, left:right] = np_image

            image_idx += 1

        free_image_data_for_memory(records)

        buffer = io.BytesIO()
        pil_image = PIL.Image.fromarray(canvas)
        pil_image.save(buffer, format='PNG')

        del canvas
        gc.collect()

        label_char = category
        unicode_codepoint = ord(label_char)
        basename = repr(unicode_codepoint).zfill(num_pads) + '_' + label_char
        image_filepath = os.path.join(export_dir_filepath, basename + '.png')
        records_metadata_filepath = os.path.join(export_dir_filepath, basename + '.json')

        open(image_filepath, mode='wb').write(buffer.getvalue())
        with open(records_metadata_filepath, mode='wb') as outfile:
            json_str = json.dumps(records, ensure_ascii=False, indent='\t')
            if json_str[-1] != '\n':
                json_str += '\n'

            json_bs = json_str.encode('utf-8')

            outfile.write(json_bs)

if __name__ == '__main__':
    main()
