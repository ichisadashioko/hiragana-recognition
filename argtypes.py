# extension for argparse (argument types)
import os
import json
from argparse import ArgumentTypeError

from constants import *


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
