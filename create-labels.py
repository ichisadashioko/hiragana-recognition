# encoding=utf-8

# Because we are going to represent the output as a array of numbers,
# we need to generate mapping between the indices and the characters.
# Otherwise, we may lose track of which indicies belong to which characters.
# I will use JSON format to save the mapping output.

import os
import re
import time
import json
import argparse

from constants import *
from logger import *
from utils import *
from serializable import *


def main():
    parser = argparse.ArgumentParser(
        description=(
            'Generate JSON mapping between output indicies and '
            'character representations for categorical classification '
            'problem.'
        ),
    )

    parser.add_argument(
        'infile',
        type=str,
        help=(
            'the input text file contains all the characters that you '
            'want to represent in the output'
        ),
    )

    parser.add_argument(
        '-o', '--outfile',
        type=str,
        default=LABEL_FILENAME,
        required=False,
        help=(
            f'output file path. Default value is {repr(LABEL_FILENAME)}. '
            f'The output file will be back up (rename) if it is '
            f'already existed!'
        ),
    )

    args = parser.parse_args()

    infile = args.infile
    outfile = args.outfile

    if not os.path.exists(infile):
        raise Exception(f'{infile} does not exist!')

    if os.path.exists(outfile):
        warn(f'Output file {outfile} is already existed!')

        backup_path = backup_file_by_modified_date(outfile)
        warn(f'It has been backed up at {backup_path}.')

    lines = open(infile, mode='r', encoding='utf-8').readlines()
    content = ''.join(lines)
    characters = content.replace('\n', '')
    characters = [c for c in characters]

    label_file = LabelFile(
        source=os.path.basename(infile),
        content=content,
        labels=characters,
    )

    with open(outfile, mode='w', encoding='utf-8') as out_stream:
        json.dump(
            obj=label_file.__dict__,
            fp=out_stream,
            indent=2,
            ensure_ascii=False,
        )


if __name__ == '__main__':
    main()
