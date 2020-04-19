import os
from typing import Callable
from functools import wraps

from constants import *


def dump_log(msg: str):
    if not os.path.exists(LOG_DIRECTORY):
        os.makedirs(LOG_DIRECTORY)

    with open(LOG_FILEPATH, mode='a+') as outfile:
        outfile.write(msg)
        outfile.write('\n')


class TerminateColor:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'


def info(*args, **kwargs):
    """Loging info to stdout."""
    # https://stackoverflow.com/a/287944/8364403
    print(f'[{TerminateColor.OKBLUE}INFO{TerminateColor.ENDC}] ', end='')
    print(*args, **kwargs)


def warn(*args, **kwargs):
    print(f'[{TerminateColor.WARNING}WARNING{TerminateColor.ENDC}] ', end='')
    print(*args, **kwargs)

def error(*args, **kwargs):
    print(f'[{TerminateColor.FAIL}ERROR{TerminateColor.ENDC}] ', end='')
    print(*args, **kwargs)

def timeit(func: Callable):
    """
    Decorator for measuring function execution time and log to file to
    visualize/profiling later.
    """
    # reference https://stackoverflow.com/a/739665/8364403
    @wraps(func)
    def wrapper(*args, **kwargs):
        # TODO log both start time and end time instead of only
        # execution time
        ts = str(time.time())
        retval = func(*args, **kwargs)
        te = str(time.time())
        dump_log(COLUMN_SEPARATOR.join((func.__name__, ts, te)))

        return retval

    return wrapper
