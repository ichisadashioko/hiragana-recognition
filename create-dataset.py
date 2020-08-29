#!/usr/bin/env python3
# encoding=utf-8
import os
import io
import time
import argparse
import itertools

from tqdm import tqdm

from constants import *
from logger import *
from utils import *
from argtypes import *

@measure_exec_time
def main():

    parser = argparse.ArgumentParser(
        description=(
            f'Generate image dataset for characters in '
            f'{repr(LABEL_FILENAME)} from font files in the '
            f'{repr(FONTS_DIR)} directory.'
        ),
    )

    parser.add_argument('infile')

    parser.add_argument(
        '--fonts',
        dest='fonts_dir',
        type=directory,
        default=FONTS_DIR,
        required=False,
        help=(
            f'The directory that contains TrueType (.ttf) or OpenType '
            f'(.otf) font files. Default look up directory is '
            f'{repr(FONTS_DIR)}.'
        ),
    )

    parser.add_argument(
        '--out-dir',
        dest='out_dir',
        type=valid_filename,
        default=DATASETS_DIR,
        required=False,
        help=(
            'The directory to put the generated dataset. '
            f'Default is {repr(DATASETS_DIR)}.'
        ),
    )

    args = parser.parse_args()
    print(args)

    infile = args.infile

    if not os.path.exists(infile):
        raise Exception(infile + ' does not exist!')

    label_file_bs = open(infile, mode='rb').read()
    label_file_content = label_file_bs.decode('utf-8')
    label_file_lines = label_file_content.splitlines()
    label_file_lines = list(filter(lambda x : len(x) > 0, label_file_lines))

    # There may be multiple characters for each "class" but we only need to render the first character from the "class".
    # "class" is refered as classification categories in the model output.
    labels = [s[0] for s in label_file_lines]

    fonts_dir = args.fonts_dir
    out_dir = args.out_dir
    image_size = 64
    font_size = 64

    metadata_filepath = 'metadata.json'
    packed_image_filepath = 'images.bin'

    if os.path.exists(metadata_filepath):
        backup_file_by_modified_date(metadata_filepath)

    if os.path.exists(packed_image_filepath):
        backup_file_by_modified_date(packed_image_filepath)

    # ===== FETCH FONTS ===== #
    info('Fetching fonts!')
    font_list = []

    font_filenames = os.listdir(fonts_dir)
    otf_filenames = list(filter(lambda x: os.path.splitext(x)[1].lower() == '.otf', font_filenames))
    ttf_filenames = list(filter(lambda x: os.path.splitext(x)[1].lower() == '.ttf', font_filenames))

    font_filenames = [*otf_filenames, *ttf_filenames]

    # ===== CHECK UNICODE CODE POINT SUPPORT OF THE FONT ===== #

    pbar = tqdm(font_filenames)
    for filename in pbar:
        pbar.set_description(filename)
        child_path = os.path.join(fonts_dir, filename)

        font = fetch_font(
            font_file=child_path,
            font_size=font_size,
            characters=labels,
        )

        font_list.append(font)

    info('Checking if fonts support all the label codepoint.')
    font_supportability_list = []
    for font in tqdm(font_list):
        ns_chars = [c for c in labels if not c in font.supported_chars]

        if not len(ns_chars) == 0:
            font_supportability_list.append((font.name, ns_chars))

    for font_name, ns_chars in font_supportability_list:
        warn(f'{font_name}:', *ns_chars)

    render_tasks = list(itertools.product(labels, font_list))

    dataset_metadata = {
        'unsupported_combinations': [],
        'blank_combinations': [],
        'records': [],
    }

    # ===== GENERATE DATASET ===== #
    with open(packed_image_filepath, mode='wb') as outfile:
        pbar = tqdm(render_tasks)
        for c, font in pbar:
            pbar.set_description(f'{c} - {font.name}')
            if not c in font.supported_chars:
                warn(f'Skipping {c} with {font.name}!')
                dataset_metadata['unsupported_combinations'].append({
                    'char': c,
                    'font': font.name,
                })

                continue

            image = render_image(c, font, image_size)
            if image is None:
                dataset_metadata['blank_combinations'].append({
                    'char': c,
                    'font': font.name,
                })

                continue

            buffer = io.BytesIO()
            image.save(buffer, format='PNG')
            encoded_image = buffer.getvalue()

            desc = (
                f'{c} grayscale image created with font {font.name} at '
                f'font size {font.size}.'
            )

            image_data_hash = hash_md5(encoded_image)

            seek_start = outfile.tell()
            outfile.write(encoded_image)
            seek_end = outfile.tell()

            dataset_metadata['records'].append({
                'hash': image_data_hash,
                'char': c,
                'font': font.name,
                'width': image_size,
                'height': image_size,
                'font_size': font_size,
                'seek_start': seek_start,
                'seek_end': seek_end,
            })

    with open(metadata_filepath, mode='wb') as outfile:
        json_str = json.dumps(dataset_metadata, ensure_ascii=False, indent='\t')
        if not json_str[-1] == '\n':
            json_str = json_str + '\n'

        json_bs = json_str.encode('utf-8')
        outfile.write(json_bs)


if __name__ == "__main__":
    main()
