# encoding=utf-8
import os
import time
import re
import math

from PIL import Image, ImageFont, ImageDraw
import numpy as np
import cv2

import tensorflow as tf


def normalize_filename(filename):
    return re.sub(r"[\\\/\.\#\%\$\!\@\(\)\[\]\s]+", "_", filename)


def datetime_now():
    return time.strftime('%Y-%m-%d_%H-%M-%S', time.gmtime())


def time_tostring(t):
    return time.strftime('%H:%M:%S', time.gmtime(t))


def fetch_font(font_file, font_size=64):
    font = ImageFont.truetype(font_file, font_size)
    font_name = '_'.join(font.getname())

    font_dict = dict()
    font_dict['font'] = font
    font_dict['font_name'] = normalize_filename(font_name)
    font_dict['font_size'] = font_size

    return font_dict


def fetch_fonts(font_folder, font_size=64):

    font_dicts = []
    font_files = os.listdir(font_folder)
    for font_file in font_files:
        font_path = f"{font_folder}/{font_file}"
        font_dict = fetch_font(font_path, font_size=font_size)
        font_dicts.append(font_dict)

    return font_dicts


def draw_text(text, font_dict, image_size=64):

    font = font_dict['font']
    font_size = font_dict['font_size']
    font_name = font_dict['font_name']

    canvas_size = int(image_size * 2)
    canvas = Image.new('L', (canvas_size, canvas_size), color=0)
    ctx = ImageDraw.Draw(canvas)

    # find the offset to draw the image
    text_offset = (canvas_size - font_size) / 2

    # draw the text
    ctx.text(
        (text_offset, text_offset),
        text,
        fill=255,
        font=font
    )

    np_img = np.array(canvas)
    non_zeros_indies = np_img.nonzero()

    # If the font does not support this character,
    # it will draw either none or a square
    # The try ... except block below is to deal with blank image
    try:
        max_x = non_zeros_indies[1][np.argmax(non_zeros_indies[1])]
        min_x = non_zeros_indies[1][np.argmin(non_zeros_indies[1])]

        max_y = non_zeros_indies[0][np.argmax(non_zeros_indies[0])]
        min_y = non_zeros_indies[0][np.argmin(non_zeros_indies[0])]
    except:
        # blank image encounter
        return None

    actual_width = max_x - min_x
    actual_height = max_y - min_y

    x_padding = (image_size - actual_width) / 2
    y_padding = (image_size - actual_height) / 2

    offset_x = min_x - x_padding
    offset_y = min_y - y_padding

    # centered-kanji image
    final_img = canvas.crop((
        offset_x, offset_y, offset_x + image_size,
        offset_y + image_size
    ))

    return final_img


# The following functions can be used to convert a value
# to a type compatible with tf.Example.
def _bytes_feature(value):
    """Returns a bytes_list from a string / byte."""
    return tf.train.Feature(bytes_list=tf.train.BytesList(value=[value]))


def _float_feature(value):
    """Returns a float_list from a float / double."""
    return tf.train.Feature(float_list=tf.train.FloatList(value=[value]))


def _int64_feature(value):
    """Returns an int64_list from a bool / enum / int / uint."""
    return tf.train.Feature(int64_list=tf.train.Int64List(value=[value]))


def convert_to_tfrec(all_image_paths, all_labels, filename):
    with tf.python_io.TFRecordWriter(filename) as tfrec_writer:
        idx = 0
        start_time = time.time()
        for image_path, label in zip(all_image_paths, all_labels):
            # image_raw = tf.read_file(image_path)
            image_raw = open(image_path, 'rb').read()

            feature = {
                'image_raw': _bytes_feature(image_raw),
                'label': _int64_feature(label),
            }

            example = tf.train.Example(
                features=tf.train.Features(feature=feature))

            tfrec_writer.write(example.SerializeToString())

            idx += 1
            if idx % 1000 == 0:
                active_time = time.time() - start_time
                avg_time = active_time / (idx)
                remain_time = avg_time * (len(all_image_paths) - idx)
                print(f'{idx}/{len(all_image_paths)}')
                print(f'ACTIVE_TIME: {time_tostring(active_time)}')
                print(f'REMAIN_TIME: {time_tostring(remain_time)}')
                print(f'AVG_TIME: {avg_time:.4f}s')
                print('='*32)
