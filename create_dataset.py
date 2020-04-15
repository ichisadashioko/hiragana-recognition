# encoding=utf-8
import os
import io
import time
import json
import argparse
from argparse import ArgumentTypeError
import traceback
import warnings
import itertools

from tqdm import tqdm

from utils import *


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


def valid_filename(string: str):
    for c in INVALID_FILENAME_CHARS:
        if c in string:
            raise ArgumentTypeError(f'Filename contains {c} character!')

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
        '-fd', '--fonts',
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

    parser.add_argument(
        '-od', '--out-dir',
        dest='out_dir',
        type=directory,
        default='.',
        required=False,
        help=(
            'The directory to put the generated dataset. '
            'Default is current directory.'
        ),
    )

    parser.add_argument(
        '-base', '--dataset_basename',
        dest='dataset_basename',
        type=valid_filename,
        default=DEFAULT_DATASET_BASENAME,
        required=False,
        help=(
            f'Set the dataset output filename (basename). '
            f'Default to {DEFAULT_DATASET_BASENAME}.'
        ),
    )

    args = parser.parse_args()
    labels = args.labels
    fonts_dir = args.fonts_dir
    image_size = args.image_size
    font_size = args.font_size

    out_dir = args.out_dir
    dataset_basename = args.dataset_basename

    # the TFRecord file
    dataset_filename = dataset_basename + DATASET_EXTENSION
    dataset_filepath = os.path.join(out_dir, dataset_filename)
    # meta data for the TFRecord file because TFRecord doesn't store
    # some meta data that we will need for training (e.g. total number
    # of records)
    dataset_meta_filename = dataset_basename + DATASET_META_FILE_SUFFIX
    dataset_meta_filepath = os.path.join(out_dir, dataset_meta_filename)

    if os.path.exists(dataset_filepath):
        backup_filepath = backup_file_by_modified_date(dataset_filepath)
        info(f'Backup {dataset_filepath} at {backup_filepath}.')

    if image_size < font_size:
        warn((
            f'You image size {image_size} may not enough to fit '
            f'character with font size {font_size}!'
        ))

    font_list = []
    info('Fetching fonts!')
    file_list = os.listdir(fonts_dir)
    for filename in tqdm(file_list):
        child_path = os.path.join(fonts_dir, filename)

        if not os.path.isfile(child_path):
            warn(f'Skipping directory {child_path}!')
            continue

        file_ext = os.path.splitext(filename)[1]
        file_ext = file_ext.lower()

        if (file_ext == '.ttf') or (file_ext == '.otf'):
            font = fetch_font(
                font_file=child_path,
                font_size=font_size,
                characters=labels,
            )
            font_list.append(font)
        else:
            warn(f'Skipping unknown file type {child_path}!')
            continue

    info('Checking if fonts support all the label codepoint.')
    font_supportability_list = []
    for font in tqdm(font_list):
        ns_chars = [c for c in labels if not c in font.supported_chars]

        if not len(ns_chars) == 0:
            font_supportability_list.append((font.name, ns_chars))

    for font_name, ns_chars in font_supportability_list:
        warn(f'{font_name}:', *ns_chars)

    # DEPRECATED
    # I will I will go with put all the images in zip files because
    # saving hundreds of thousand images to disk gave me too much
    # trouble to deal with them later. Removing them is a real pain
    # that will take many hours.

    # I will create a directory for each fonts and put all the images
    # generated by that font in that directory.
    # ------------------------------------------------------------------

    # After trying to find a way to stream bytes data directly into zip
    # entry, I cannot find any API from `zipfile` to achieve that.
    # `zipfile` requires a physical file on disk to be feed into a zip.
    # Writing file to a temporary location and feed it back to `zipfile`
    # seems to cost a lot of time so I will give up on this method for
    # now. TODO Create a zip compressor that will accept bytes as input.

    # I will go with `TFRecord` this time. TFRecord is suitable for
    # sequential access only. So afer creating a TFRecord we will not
    # know how many records does it have. Shuffling the dataset after
    # every training iteration does not make sense to me because I
    # think I don't think it's possible (validate if shuffling works
    # with TFRecord - https://stackoverflow.com/a/35658968/8364403).
    # So we will have shuffle the dataset before creating the TFRecord.

    # I intended to use zip format because we can take a look inside
    # its data for inspection with the help of many tools. But now I
    # decided to use TFRecord, I need to find a way to inspect the data.
    # I am talking about hundreds of thousand of images. And if there is
    # any defective images, I need to able to remove them easily. TODO

    entries = []

    # create task list to have progress bar with `tqdm`
    render_tasks = list(itertools.product(labels, font_list))
    pbar = tqdm(render_tasks)
    for c, font in pbar:
        pbar.set_description(f'{c} - {font.name}')

        if not c in font.supported_chars:
            warn(f'Skipping {c} with {font.name}!')
            continue

        image = render_image(c, font, image_size)
        if image is None:
            continue

        # buffer = io.BytesIO()
        # image.save(buffer, format='PNG')
        # encoded_image = buffer.getvalue()


if __name__ == "__main__":
    main()
