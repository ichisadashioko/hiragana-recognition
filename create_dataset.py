# encoding=utf-8
import os
import time
import re
import math

import numpy as np

import utils
import key_label_dict

from PIL import Image, ImageFont, ImageDraw

if __name__ == "__main__":
    font_folder = 'E:/programming/week-based-kanji-classifier/all_fonts'
    font_dicts = utils.fetch_fonts(font_folder)

    kana_list = key_label_dict.key_dict.keys()

    cache_filename = 'image_paths.csv'
    error_log_filename = f'kana_error_{int(time.time())}.log'
    stats_log_filename = f'kana_log_{int(time.time())}.csv'
    save_folder = 'kana_images'

    with open(stats_log_filename, 'w', encoding='utf-8') as lf:
        lf.write('kana,image_count,failed_count,unsupported_fonts\n')

    with open(cache_filename, 'w', encoding='utf-8') as cf:
        cf.write('label,path\n')

    start_time = time.time()
    for idx, kana in enumerate(kana_list):
        kana_start = time.time()

        kana_save_folder = f'{save_folder}/{kana}'
        kana_label = key_label_dict.key_dict[kana]

        image_count = 0
        failed_count = 0
        unsupported_fonts = []

        if not os.path.exists(kana_save_folder):
            os.makedirs(kana_save_folder)

        for font_dict in font_dicts:
            font = font_dict['font']
            font_size = font_dict['font_size']
            font_name = font_dict['font_name']

            pil_image = utils.draw_text(kana, font_dict)

            if pil_image is None:
                # print(f'{font_name} does not support {kana}')

                failed_count += 1
                unsupported_fonts.append(font_name)
                log_str = f'[ERROR]\t{int(time.time())}\t{font_name} does not support {kana}\n'
                with open(error_log_filename, 'a+', encoding='utf-8') as el:
                    el.write(log_str)
                continue

            image_filename = f'{kana}-{font_name}.png'
            image_filename = f'{kana_save_folder}/{image_filename}'
            with open(cache_filename, 'a', encoding='utf-8') as cf:
                cf.write(f'{kana_label},{image_filename}\n')

            image_count += 1
            pil_image.save(image_filename)

        with open(stats_log_filename, 'a', encoding='utf-8') as lf:
            lf.write(f'{kana},{image_count},{failed_count},{"|".join(unsupported_fonts)}\n')

        active_time = time.time() - start_time
        avg_time = active_time / (idx+1)
        kana_time = time.time() - kana_start
        remain_time = avg_time * (len(kana_list) - idx - 1)

        print(f'{idx+1}/{len(kana_list)}')
        print(f'ACTIVE_TIME: {utils.time_tostring(active_time)}')
        print(f'REMAIN_TIME: {utils.time_tostring(remain_time)}')
        print(f'KANA_TIME: {kana_time:.2f}s')
        print(f'AVG_TIME: {avg_time:.2f}s')
