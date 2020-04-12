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
import warnings

from utils import backup_file_by_modified_date, DEFAULT_LABEL_FILE


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

    default_outfile = DEFAULT_LABEL_FILE

    parser.add_argument(
        '-o', '--outfile',
        type=str,
        default=default_outfile,
        required=False,
        help=(
            f'output file path. Default value is {repr(default_outfile)}. '
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
        warnings.warn(f'Output file {outfile} is already existed!')

        backup_path = backup_file_by_modified_date(outfile)
        warnings.warn(f'It has been backed up at {backup_path}.')

    lines = open(infile, mode='r', encoding='utf-8').readlines()
    content = ''.join(lines)
    characters = content.replace('\n', '')
    characters = [c for c in characters]

    with open(outfile, mode='w', encoding='utf-8') as out_stream:
        json.dump(characters, out_stream, indent=2, ensure_ascii=False)


if __name__ == '__main__':
    main()
