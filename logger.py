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


class TermColor:
    RESET_COLOR = '\033[0m'
    FG_BRIGHT_RED = '\033[91m'
    FG_BRIGHT_GREEN = '\033[92m'
    FG_BRIGHT_YELLOW = '\033[93m'
    FG_BRIGHT_BLUE = '\033[94m'
    FG_BRIGHT_MAGENTA = '\033[95m'


def info(*args, **kwargs):
    """Loging info to stdout."""
    # https://stackoverflow.com/a/287944/8364403
    print(f'[{TermColor.FG_BRIGHT_GREEN}INFO{TermColor.RESET_COLOR}] ', end='')
    print(*args, **kwargs)


def warn(*args, **kwargs):
    print(f'[{TermColor.FG_BRIGHT_YELLOW}WARN{TermColor.RESET_COLOR}] ', end='')
    print(*args, **kwargs)


def error(*args, **kwargs):
    print(f'[{TermColor.FG_BRIGHT_RED}ERROR{TermColor.RESET_COLOR}] ', end='')
    print(*args, **kwargs)


def debug(*args, **kwargs):
    print(f'[{TermColor.FG_BRIGHT_BLUE}DEBUG{TermColor.RESET_COLOR}] ', end='')
    print(*args, **kwargs)


def measure_exec_time(func: Callable):
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
