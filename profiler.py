# encoding=utf-8
import os
import time
import re
from typing import List, Type
from collections import defaultdict

import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import pandas as pd

from constants import *
from logger import *
from utils import *


class LogFile:
    def __init__(self, name: str, ts: float, log_data: pd.DataFrame):
        self.name = name
        self.ts = ts
        self.data = log_data

    def __repr__(self):
        return repr((timestamp_to_datetime(self.ts), self.name))


def list_log_files(log_files: List[LogFile]):
    for idx, log_file in enumerate(log_files):
        print(f'{idx} - {log_file}')


def plot_values_on_top_of_bars(
    ax: matplotlib.axes.Axes,
    bars: matplotlib.container.BarContainer,
    values: List[str],
    max_bar_height: float,
):
    # show values on top of bars
    # https://stackoverflow.com/a/53072924/8364403
    # https://stackoverflow.com/a/40491960/8364403
    text_height_delta = max_bar_height * .005
    for idx, bar in enumerate(bars):
        ax.text(
            x=bar.get_x() + bar.get_width()/2,
            y=bar.get_height() + text_height_delta,
            s=values[idx],
            ha='center',
        )


def plot_log(log: LogFile):
    np_data = log.data.to_numpy()

    func_data = {}

    for row in np_data:
        func_name, ts, te = row[:3]
        exec_time = te - ts
        if func_name in func_data:
            func_data[func_name]['num_calls'] += 1
            func_data[func_name]['total_exec_time'] += exec_time

            last_min = func_data[func_name]['min']
            func_data[func_name]['min'] = min(exec_time, last_min)

            last_max = func_data[func_name]['max']
            func_data[func_name]['max'] = max(exec_time, last_max)
        else:
            func_data[func_name] = {
                'num_calls': 1,
                'total_exec_time': exec_time,
                'min': exec_time,
                'max': exec_time,
            }

    for func_name in func_data:
        # calculate and average
        total_exec_time = func_data[func_name]['total_exec_time']
        num_calls = func_data[func_name]['num_calls']

        func_data[func_name]['avg'] = total_exec_time / num_calls

    fig = plt.figure(figsize=(12, 12))
    # use GridSpec for more organized layout
    # https://matplotlib.org/3.2.1/gallery/subplots_axes_and_figures/gridspec_multicolumn.html
    gs = GridSpec(2, 2, figure=fig)

    # Plot 1: total amount of time for each methods
    # https://matplotlib.org/tutorials/introductory/pyplot.html#plotting-with-categorical-variables
    ax = plt.subplot(gs.new_subplotspec((0, 0)))
    ax.set_title('total amount of execution time')
    names = []
    values = []
    for func_name in func_data:
        names.append(func_name)
        values.append(func_data[func_name]['total_exec_time'])

    bars = ax.bar(names, values)
    plot_values_on_top_of_bars(
        ax=ax,
        bars=bars,
        values=[f'{x:.2f}' for x in values],
        max_bar_height=max(values),
    )

    # Plot 2: number of calls for each methods
    ax = plt.subplot(gs.new_subplotspec((0, 1)))
    ax.set_title('number of calls')
    names = []
    values = []
    for func_name in func_data:
        names.append(func_name)
        values.append(func_data[func_name]['num_calls'])

    bars = ax.bar(names, values)
    plot_values_on_top_of_bars(
        ax=ax,
        bars=bars,
        values=[repr(x) for x in values],
        max_bar_height=max(values),
    )

    # Plot 3: plot max, min, and average for each methods
    # We use grouped barplot here.
    # https://python-graph-gallery.com/11-grouped-barplot/
    ax = plt.subplot(gs.new_subplotspec((1, 0), colspan=2))
    ax.set_title('max, min, and avg execution time')

    min_bars = []
    max_bars = []
    avg_bars = []
    group_labels = []

    for func_name in func_data:
        min_bars.append(func_data[func_name]['min'])
        max_bars.append(func_data[func_name]['max'])
        avg_bars.append(func_data[func_name]['avg'])
        group_labels.append(func_name)

    bar_width = .25
    # bar width * (number of group + 1) for x-axis spacing
    # 1 unit for spacing
    min_bars_xs = np.arange(len(min_bars)) * (bar_width * (3+1))
    avg_bars_xs = [bar_width + x for x in min_bars_xs]
    max_bars_xs = [bar_width + x for x in avg_bars_xs]

    bars = ax.bar(
        x=min_bars_xs,
        height=min_bars,
        color='#ff0000',
        width=bar_width,
        label='min',
    )
    plot_values_on_top_of_bars(
        ax=ax,
        bars=bars,
        values=[f'{x:.4f}' for x in min_bars],
        max_bar_height=max(max_bars),
    )

    bars = ax.bar(
        x=avg_bars_xs,
        height=avg_bars,
        color='#00ff00',
        width=bar_width,
        label='avg',
    )
    plot_values_on_top_of_bars(
        ax=ax,
        bars=bars,
        values=[f'{x:.4f}' for x in avg_bars],
        max_bar_height=max(max_bars),
    )

    bars = ax.bar(
        x=max_bars_xs,
        height=max_bars,
        color='#0000ff',
        width=bar_width,
        label='max',
    )
    plot_values_on_top_of_bars(
        ax=ax,
        bars=bars,
        values=[f'{x:.5f}' for x in max_bars],
        max_bar_height=max(max_bars),
    )

    # group label x position to middle bar
    ax.set_xticks(avg_bars_xs)
    ax.set_xticklabels(group_labels)
    ax.legend()

    plt.show()


def main():
    if not os.path.exists(LOG_DIRECTORY):
        info(f'There is not log to show!')
        return
    elif not os.path.isdir(LOG_DIRECTORY):
        raise Exception((
            f'We store logs in {repr(LOG_DIRECTORY)}! '
            'Please move your file somewhere else!'
        ))

    file_list = os.listdir(LOG_DIRECTORY)
    if len(file_list) == 0:
        info(f'There is not log to show!')
        return

    logs = []

    for filename in file_list:
        if not LOG_SUFFIX in filename:
            warn(f'Skipping file {filename}.')
            continue

        filepath = os.path.join(LOG_DIRECTORY, filename)
        support_log_format = True
        log_data = []
        try:
            # I don't use pandas because it will fill the empty value
            # of old log format instead of raise Exception.
            with open(filepath, mode='r') as infile:
                for line in infile:
                    line = line.replace('\n', '')
                    if len(line) == 0:
                        # empty line
                        continue

                    row = line.split(COLUMN_SEPARATOR)
                    if not len(row) == len(LOG_HEADER):
                        support_log_format = False
                        warn(f'Skipping {filepath}! Unsupported format!')
                        break

                    # format data
                    row = [row[0], float(row[1]), float(row[2])]
                    log_data.append(row)

            if not support_log_format:
                continue

            log_data = pd.DataFrame(
                data=log_data,
                columns=LOG_HEADER,
            )

        except:
            # traceback.print_exc() # keep this here for debugging
            warn(f'Skipping incompatible format {filename}!')
            continue

        ts = float(filename.replace(LOG_SUFFIX, ''))
        log_file = LogFile(filename, ts, log_data)
        logs.append(log_file)

    if len(logs) == 0:
        info(f'There is not log to show!')
        return

    logs.sort(key=lambda x: x.ts, reverse=True)

    # command line GUI
    while True:
        list_log_files(logs)
        option = input('Choose log file to view (q to quit):')
        if option == 'q':
            break

        try:
            index = int(option)
        except:
            continue
        if (index < 0) or not (index < len(logs)):
            continue

        info('Showing plot. Close it to come back here.')
        plot_log(logs[index])


if __name__ == '__main__':
    main()
