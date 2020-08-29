# encoding=utf-8
import os
import time
import re
import unicodedata
import traceback
import hashlib

from PIL import Image, ImageFont, ImageDraw
import numpy as np
import pandas as pd
from fontTools.ttLib import TTFont

from constants import *
from logger import *


def timestamp_to_datetime(ts: float):
    return time.strftime('%Y-%m-%d_%H-%M-%S', time.gmtime(ts))


@measure_exec_time
def normalize_filename(filename):
    """Replace invalid filename characters with underscore."""
    return re.sub(
        pattern=(
            '[' + re.escape(INVALID_FILENAME_CHARS)
            + re.escape('(){}[]') + r'\s' + ']+'
        ),
        repl='_',
        string=filename,
    ).strip('_')


def time_tostring(t):
    return time.strftime('%H:%M:%S', time.gmtime(t))


class Font:
    """
    Wrapper class for storing some data that we need to identify.

    For example:

    - the font name (not the file name)
    - the font size (pillow's ImageFont requires to be created with font
    size so I need to store that)
    - the ImageFont for using with pillow's drawing API
    - the font file path for using with `fonttools` to check if the font
    support a specific character or not. otherwise, it may give the tofu
    shape image.
    """

    def __init__(
        self,
        name: str,
        font: ImageFont.FreeTypeFont,
        size: int,
        path: str,
        supported_chars: list,
    ):
        self.name = name
        self.font = font
        self.size = size
        self.path = path
        self.supported_chars = supported_chars

    def __repr__(self):
        return repr((self.name, self.size, self.path))


@measure_exec_time
def fetch_font(font_file: str, font_size=64, characters=list()):
    pillow_font = ImageFont.truetype(font=font_file, size=font_size)
    font_name = '_'.join(pillow_font.getname())

    # TODO test if this code is working or not by rendering the
    # actual image (with some uncommon kanji)
    ft_font = TTFont(font_file)
    supported_chars = []
    for cmap in ft_font['cmap'].tables:
        if cmap.isUnicode():
            for c in characters:
                if ord(c) in cmap.cmap:
                    supported_chars.append(c)

    return Font(font_name, pillow_font, font_size, font_file, supported_chars)


@measure_exec_time
def render_image(c: str, font: Font, image_size=64) -> Image:
    pillow_font = font.font

    # we create a canvas at least twice as large as the font size to
    # prevent the character's pixel(s) from being cropped from drawing
    # on constrained size
    canvas_size = int(max(font.size*2, image_size))

    # the canvas is a grayscale image
    # background color is black (0)
    # text color is white (255)
    # you can experiment with other color spaces
    canvas = Image.new('L', (canvas_size, canvas_size), color=0)
    ctx = ImageDraw.Draw(canvas)
    # the variable names `canvax` and `ctx` are inspired from JavaScript
    # where we draw on HTMLCanvas

    # position the top-left position of the character's bounding box
    # (fontSize x fontSize square) on the canvas to draw the characters
    # https://pillow.readthedocs.io/en/stable/reference/ImageDraw.html#PIL.ImageDraw.PIL.ImageDraw.ImageDraw.text
    char_x = (canvas_size - font.size) / 2
    char_y = (canvas_size - font.size) / 2
    char_origin_pos = (char_x, char_y)

    ctx.text(
        xy=char_origin_pos,
        text=c,
        fill=255,
        font=font.font,
    )

    # if the image size is the canvas size then return the image without
    # centering or cropping because we did try to make an image twice
    # as large the font size
    if canvas_size == image_size:
        # I keep the pillow Image object instead of NumPy array so
        # that we can save the image to file using the pillow encoder
        # to encode to PNG without having to rely on something like
        # OpenCV. We can always convert to NumPy array later if we want.
        return canvas

    # we will center the character by find the non-zero pixels to
    # improve the model accuracy
    # TODO center input before using model in other platform (e.g.
    # Android - Java - Bitmap, Web - JavaScript - HTMLCanvas)

    # convert pillow Image to NumPy array
    np_img = np.asarray(canvas, dtype=np.uint8)

    # https://docs.scipy.org/doc/numpy/reference/generated/numpy.nonzero.html
    zero_ys, zero_xs = np_img.nonzero()[:2]  # `[:2]` just to be safe

    # there may be not any nonzero pixel(s) at all on the image because
    # the font may not support the character or there is not any glyph
    # for the character in the font or maybe for any reason I haven't
    # encounter
    if len(zero_xs) == 0:
        warn(f'{font.name} gives blank image for {repr(c)}!')
        return None

    min_x, max_x = min(zero_xs), max(zero_xs)
    min_y, max_y = min(zero_ys), max(zero_ys)
    # you can see the bounding box example here on Imgur
    # https://i.imgur.com/lDGHNgL.png

    # the character dimensions is caculated based on the nonzero pixels
    character_width = max_x - min_x
    character_height = max_y - min_y

    image_offset_x = min_x - int((image_size - character_width)/2)
    image_offset_y = min_y - int((image_size - character_height)/2)
    # here is the example for the character's bounding box (in green)
    # and the going to be exported image's bounding box (in blue)
    # https://i.imgur.com/Gq3mLex.png

    # Crop the final image (left, top, right, bottom)
    # https://pillow.readthedocs.io/en/stable/reference/Image.html#PIL.Image.Image.crop
    image_bounding_box = (
        image_offset_x,
        image_offset_y,
        image_offset_x+image_size,
        image_offset_y+image_size,
    )

    return canvas.crop(image_bounding_box)


@measure_exec_time
def backup_file_by_modified_date(infile: str):
    if not os.path.exists(infile):
        raise Exception(f'{infile} does not exist!')

    infile_abspath = os.path.abspath(infile)
    parent, basename = os.path.split(infile_abspath)

    if len(basename) == 0:
        raise Exception(f'Cannot backup root directory!')

    modified_time = int(os.path.getmtime(infile_abspath))
    backup_filename = f'{modified_time}-{basename}'
    backup_filepath = os.path.join(parent, backup_filename)
    os.rename(infile_abspath, backup_filepath)

    return backup_filepath


@measure_exec_time
def hash_md5(s: bytes):
    m = hashlib.md5()
    m.update(s)
    return m.digest().hex().upper()


@measure_exec_time
def hash_sha256(s: bytes):
    m = hashlib.sha256()
    m.update(s)
    return m.digest().hex().upper()
