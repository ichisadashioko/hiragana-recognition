#!/usr/bin/env python3
# encoding=utf-8
import os
import time
import json
import collections
from typing import Dict, List
from datetime import datetime

import tkinter as tk
from tkinter import ttk

import PIL
import PIL.Image
import PIL.ImageTk

import logger


def logts(*args, **kwargs):
    """print() with timestamp"""
    ts = datetime.now().strftime('%Y-%m-%d_%H:%M:%S.%f')
    print(logger.TermColor.FG_BRIGHT_GREEN + '[' + ts + '] ' + logger.TermColor.RESET_COLOR, end='')
    print(*args, **kwargs)


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

    # === CHECK FOR DUPLICATED IMAGES === #
    records = dataset_metadata['records']
    image_hash_counter = collections.defaultdict(list)
    for record in records:
        image_hash_counter[record['hash']].append(record)

    records_with_duplicated_image = []

    hashes_with_duplicated_images = []
    for image_hash in image_hash_counter:
        _records = image_hash_counter[image_hash]
        if len(_records) > 1:
            records_with_duplicated_image.append(_records)
            hashes_with_duplicated_images.append(image_hash)

    if len(records_with_duplicated_image) > 0:
        logger.warn('There are duplicated images in the dataset!')
        logger.info('Opening GUI to resolve duplicated images. Close the program when you are done.')

        # === UNPACK IMAGES FOR INSPECTION === #
        records_to_be_unpacked = []
        for duplicated_entry in records_with_duplicated_image:
            for record in duplicated_entry:
                records_to_be_unpacked.append(record)

        # sort records by seek position for efficient seeking to unpack the images
        records_to_be_unpacked.sort(key=lambda record: record['seek_start'])

        with open(packed_image_filepath, mode='rb') as infile:
            for record in records_to_be_unpacked:
                seek_start: int = record['seek_start']
                seek_end: int = record['seek_end']
                image_data_size = seek_end - seek_start

                infile.seek(seek_start)
                bs = infile.read(image_data_size)
                record['image_bytes'] = bs # TODO high memory usage

        app = tk.Tk()
        app.geometry('1600x900')

        duplicated_entries_dropdown = ttk.Combobox(
            app,
            values=hashes_with_duplicated_images,
        )

        def render_duplicated_images():
            pass

        def on_duplicated_entries_dropdown_value_selected(event: tk.Event):
            selected_value = duplicated_entries_dropdown.get()
            logts(selected_value)

        duplicated_entries_dropdown.grid(column=0, row=0)
        duplicated_entries_dropdown.bind('<<ComboboxSelected>>', on_duplicated_entries_dropdown_value_selected)
        duplicated_entries_dropdown.pack(fill=tk.X, expand=True)

        app.mainloop()


if __name__ == '__main__':
    main()
