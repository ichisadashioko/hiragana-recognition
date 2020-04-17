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

from constants import *
from logger import *
from utils import *
from argtypes import *


@timeit
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

    # TODO modify "Modified Time" for two of these file have the same
    # modified time
    if os.path.exists(dataset_filepath):
        backup_filepath = backup_file_by_modified_date(dataset_filepath)
        info(f'Backup {dataset_filepath} at {backup_filepath}.')

    if os.path.exists(dataset_meta_filepath):
        backup_filepath = backup_file_by_modified_date(dataset_meta_filepath)
        info(f'Backup {dataset_meta_filepath} at {backup_filepath}.')

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

    # import tensorflow takes a lot of time so I put it here to improve
    # start up time
    import tensorflow as tf
    from tensorflow_utils import CharacterTFRecordDataset

    entries = []

    dataset_metadata = {
        'record_summary': {
            'number_of_records': 0,
        },
        'dataset': [
            # The data will be append to here to reflect the order in
            # the tfrecord file.

            # This record object does not contain the actual image and
            # we shouldn't store the image in here because the number
            # of images and their total size will easily eat all our
            # RAM (depend on the size of dataset).

            # Reference record format:
            # {'hash': 'MD5', 'character': 'あ', 'font_name': 'HGKyokashotai_Medium'}

            # I record these information only so that we can
            # somehow inpsect the dataset and check some of them to be
            # invalid. We can come back and skip/remove this entry next
            # time we process the data.
            # TODO create a web interface to inspect the dataset
        ],
        # record format for `invalid_records` same as `dataset` above
        # after we implement the web interface for inspection, the
        # selected invalid image will be moved from `dataset` above to
        # here
        'invalid_records': [],
        'known_unsupported_combination': {
            # record format {'character': 'あ', 'font_name': 'HGKyokashotai_Medium'}
            # we may still need to inspect all these combination that
            # have been filtered by our runtime.
            'not_in_cmap': [],
            'give_blank_image': [],
        }
    }

    with tf.io.TFRecordWriter(dataset_filepath) as tfrecord_writer:
        # create task list to have progress bar with `tqdm`
        # TODO shuffle dataset
        # TODO split dataset to small files if it is too large (>100MB)
        render_tasks = list(itertools.product(labels, font_list))
        pbar = tqdm(render_tasks)
        for c, font in pbar:
            pbar.set_description(f'{c} - {font.name}')

            if not c in font.supported_chars:
                warn(f'Skipping {c} with {font.name}!')
                dataset_metadata['known_unsupported_combination']['not_in_cmap'].append({
                    'character': c,
                    'font_name': font.name,
                })
                continue

            image = render_image(c, font, image_size)
            if image is None:
                dataset_metadata['known_unsupported_combination']['give_blank_image'].append({
                    'character': c,
                    'font_name': font.name,
                })
                continue

            buffer = io.BytesIO()
            image.save(buffer, format='PNG')
            encoded_image = buffer.getvalue()

            desc = f'{c} grayscale image created with font {font.name} at font size {font.size}.'
            ts = int(time.time())
            hash = hash_md5(f'{desc}{ts}'.encode('utf-8'))

            dataset_metadata['record_summary']['number_of_records'] += 1
            dataset_metadata['dataset'].append({
                'hash': hash,
                'character': c,
                'font_name': font.name,
            })

            record = CharacterTFRecordDataset.serialize_record(
                hash=hash,
                character=c,
                width=image_size,
                height=image_size,
                depth=1,
                image=encoded_image,
                font_size=font_size,
                font_name=font.name,
                description=desc,
            )

            tfrecord_writer.write(record)

    # https://docs.python.org/3/library/os.html#os.utime
    ts = time.time()
    os.utime(dataset_filepath, (ts, ts))

    with open(dataset_meta_filepath, mode='w', encoding='utf-8') as outfile:
        json.dump(dataset_metadata, outfile, ensure_ascii=False, indent='  ')

    os.utime(dataset_meta_filepath, (ts, ts))


if __name__ == "__main__":
    main()
