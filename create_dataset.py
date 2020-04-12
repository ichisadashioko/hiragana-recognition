# encoding=utf-8
import os
import time
import json
import argparse
from argparse import ArgumentTypeError
import traceback
import warnings

from tqdm import tqdm

from utils import DEFAULT_LABEL_FILE, fetch_font


def positive_int(string: str):
    # reference https://docs.python.org/3/library/argparse.html#type
    value = int(string)
    if value < 1:
        raise ArgumentTypeError(f'{repr(string)} is not a positive integer!')  # noqa

    return value


def directory(string: str):
    if not os.path.exists(string):
        raise ArgumentTypeError(f'{repr(string)} does not exist!')
    elif not os.path.isdir(string):
        raise ArgumentTypeError(f'{repr(string)} is not a directory!')

    return string


def json_labels(string: str):
    if not os.path.exists(string):
        raise ArgumentTypeError(f'{repr(string)} does not exist!')
    elif not os.path.isfile(string):
        raise ArgumentTypeError(f'{repr(string)} is not a file!')

    try:
        with open(string, mode='r', encoding='utf-8') as infile:
            characters = json.load(infile)

        if not isinstance(characters, list):
            raise ArgumentTypeError(f'{repr(string)} must contain a top-level array!')  # noqa

        for c in characters:
            if not isinstance(c, str):
                raise ArgumentTypeError(f'All objects in array must be string!')  # noqa

        return characters
    except ValueError:
        raise ArgumentTypeError(f'{repr(string)} is not a valid JSON file!')


def main():
    default_infile = DEFAULT_LABEL_FILE
    default_fonts_dir = 'fonts'
    default_font_size = 64
    default_image_size = 64

    parser = argparse.ArgumentParser(
        description=(
            f'Generate image dataset for characters in '
            f'{repr(default_infile)} from font files in the '
            f'{repr(default_fonts_dir)} directory.'
        ),
    )

    parser.add_argument(
        '-l', '--label-file',
        dest='labels',
        type=json_labels,
        default=default_infile,
        required=False,
        help=(
            f'the file contains list of characters to generate image'
            f'dataset for. Default file path to be read is '
            f'{repr(default_infile)}. The file must be a JSON file '
            'that contains an array of characters.'
        ),
    )

    parser.add_argument(
        '-f', '--fonts',
        dest='fonts_dir',
        type=directory,
        default=default_fonts_dir,
        required=False,
        help=(
            f'The directory that contains TrueType (.ttf) or OpenType '
            f'(.otf) font files. Default look up directory is '
            f'{repr(default_fonts_dir)}.'
        ),
    )

    parser.add_argument(
        '-is', '--image-size',
        dest='image_size',
        type=positive_int,
        default=default_image_size,
        required=False,
        help=(
            f'The size for the image in pixel(s). Default value is '
            f'{default_image_size} pixel(s).'
        ),
    )

    parser.add_argument(
        '-fs', '--font-size',
        dest='font_size',
        type=positive_int,
        default=default_font_size,
        required=False,
        help=(
            f'The font size for rendering the characters. '
            f'Default value is {default_font_size}.'
        )
    )

    args = parser.parse_args()
    labels = args.labels
    fonts_dir = args.fonts_dir
    image_size = args.image_size
    font_size = args.font_size

    if image_size < font_size:
        warnings.warn((
            f'You image size {image_size} may not enough to fit '
            f'character with font size {font_size}!'
        ))

    font_list = []
    file_list = os.listdir(fonts_dir)
    for filename in file_list:
        child_path = os.path.join(fonts_dir, filename)

        if not os.path.isfile(child_path):
            warnings.warn(f'Skipping directory {child_path}!')
            continue

        file_ext = os.path.splitext(filename)[1]
        file_ext = file_ext.lower()

        if (file_ext == '.ttf') or (file_ext == '.otf'):
            font = fetch_font(child_path, font_size=font_size)
            font_list.append(font)
        else:
            warnings.warn(f'Skipping unknown file type {child_path}!')
            continue

    print('Checking if fonts support all the label codepoint.')
    font_supportability_list = []
    for font in tqdm(font_list):
        unsupported_chars = []
        for label in labels:
            if not font.is_support(label):
                unsupported_chars.append(label)

        if not len(unsupported_chars) == 0:
            font_supportability_list.append(font.name, unsupported_chars)

    for font_name, unsupported_chars in font_supportability_list:
        print(f'{font_name}:', *unsupported_chars)


if __name__ == "__main__":
    main()
    # start_time = time.time()
    # for idx, kana in enumerate(kana_list):
    #     kana_start = time.time()

    #     kana_save_folder = f'{save_folder}/{kana}'
    #     kana_label = key_label_dict.key_dict[kana]

    #     image_count = 0
    #     failed_count = 0
    #     unsupported_fonts = []

    #     if not os.path.exists(kana_save_folder):
    #         os.makedirs(kana_save_folder)

    #     for font_dict in font_dicts:
    #         font = font_dict['font']
    #         font_size = font_dict['font_size']
    #         font_name = font_dict['font_name']

    #         pil_image = utils.draw_text(kana, font_dict)

    #         if pil_image is None:
    #             # print(f'{font_name} does not support {kana}')

    #             failed_count += 1
    #             unsupported_fonts.append(font_name)
    #             log_str = f'[ERROR]\t{int(time.time())}\t{font_name} does not support {kana}\n'
    #             with open(error_log_filename, 'a+', encoding='utf-8') as el:
    #                 el.write(log_str)
    #             continue

    #         image_filename = f'{kana}-{font_name}.png'
    #         image_filename = f'{kana_save_folder}/{image_filename}'
    #         with open(cache_filename, 'a', encoding='utf-8') as cf:
    #             cf.write(f'{kana_label},{image_filename}\n')

    #         image_count += 1
    #         pil_image.save(image_filename)

    #     with open(stats_log_filename, 'a', encoding='utf-8') as lf:
    #         lf.write(
    #             f'{kana},{image_count},{failed_count},{"|".join(unsupported_fonts)}\n')

    #     active_time = time.time() - start_time
    #     avg_time = active_time / (idx+1)
    #     kana_time = time.time() - kana_start
    #     remain_time = avg_time * (len(kana_list) - idx - 1)

    #     print(f'{idx+1}/{len(kana_list)}')
    #     print(f'ACTIVE_TIME: {utils.time_tostring(active_time)}')
    #     print(f'REMAIN_TIME: {utils.time_tostring(remain_time)}')
    #     print(f'KANA_TIME: {kana_time:.2f}s')
    #     print(f'AVG_TIME: {avg_time:.2f}s')
