# encoding=utf-8
import os
import time
import re
import io
from functools import partial

import tkinter as tk
import tkinter.font
from tkinter import ttk

import numpy as np
import cv2
import matplotlib.pyplot as plt

from PIL import Image

import tensorflow as tf
tf.enable_eager_execution()

import key_label_dict
import utils

pen = None
CANVAS_WIDTH = None
CANVAS_HEIGHT = None
canvas = None

result_label = None

model = None

class Pen():
    def __init__(self):
        self.down = False
        self.x = None
        self.y = None


def preprocess_image(img):
    if img is None:
        return None

    img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    # print(img.shape)

    non_zeros_indies = img.nonzero()
    try:
        max_x = non_zeros_indies[1][np.argmax(non_zeros_indies[1])]
        min_x = non_zeros_indies[1][np.argmin(non_zeros_indies[1])]

        max_y = non_zeros_indies[0][np.argmax(non_zeros_indies[0])]
        min_y = non_zeros_indies[0][np.argmin(non_zeros_indies[0])]
    except:
        # blank image encounter
        print('blank image')
        return None

    img = img[min_y:max_y, min_x:max_x]
    height, width = img.shape[:2]

    #=================== border padding ===================#
    pad_ratio = 0.1
    img = cv2.copyMakeBorder(
        src=img,
        top=int(pad_ratio * height),
        bottom=int(pad_ratio * height),
        left=int(pad_ratio * width),
        right=int(pad_ratio * width),
        borderType=cv2.BORDER_CONSTANT,
    )
    img = cv2.resize(img, (64, 64), cv2.INTER_CUBIC)
    img = img.astype(np.float) / 255.0
    return img


def predict_kana(img):
    global model

    if img is None or model is None:
        return None

    img = np.reshape(img, (-1, 64, 64, 1))
    hist = model.predict(img)
    # print(hist)
    results = hist[0]

    result_list = [[idx, value] for idx, value in enumerate(results)]
    result_list.sort(key=lambda x: x[1], reverse=True)
    map_result = []
    for result in result_list:
        if result[0] in key_label_dict.label_dict.keys():
            map_result.append([key_label_dict.label_dict[result[0]], result[1]])
    return map_result


def take_canvas_image():
    global canvas
    ps = canvas.postscript(colormode='color')
    img = Image.open(io.BytesIO(ps.encode('utf-8')))
    np_img = np.array(img)
    return np_img


def predict_pipeline(img):
    img = preprocess_image(img)
    result = predict_kana(img)
    return result


def key_press(event):
    global pen
    #=================== pen down ===================#
    if (event.keysym == 'Shift_L') or (event.keysym == 'Shift_R'):  # shift key
        pen.down = True


def key_release(event):
    global pen, CANVAS_WIDTH, CANVAS_HEIGHT
    # print(event)

    #=================== show image ===================#
    if event.char == 's':
        np_img = take_canvas_image()
        np_img = preprocess_image(np_img)
        if np_img is not None:
            # print(np_img.shape)
            plt.imshow(np_img)
            plt.colorbar()
            plt.show()

    #=================== clear canvas ===================#
    elif event.char == 'c':
        canvas.create_rectangle(
            0,
            0,
            CANVAS_WIDTH * 2,
            CANVAS_HEIGHT * 2,
            fill='black',
        )

    #=================== pen up ===================#
    elif (event.keysym == 'Shift_L') or (event.keysym == 'Shift_R'):  # shift key
        pen.down = False
        pen.x = None
        pen.y = None

    #=================== predict kana ===================#
    elif event.char == 'p':  # predict
        result_label.delete(0, tk.END)

        img = take_canvas_image()
        result = predict_pipeline(img)
        if result is None:
            pass
        else:
            # print(result)
            result_list = [
                f'{kana}-{confidence*100:.2f}%' for kana, confidence in result
            ]

            result_label.delete(0, tk.END)
            for result in result_list:
                result_label.insert(tk.END, result)


def mouse_move_event(event):
    global pen, canvas
    if pen.down:
        if (pen.x is None) or (pen.y is None):
            pen.x = event.x
            pen.y = event.y
        else:
            line_width = 10  # px line width
            canvas.create_line(
                pen.x,
                pen.y,
                event.x,
                event.y,
                width=line_width,
                fill='white',
            )
            # print(f'({pen.x},{pen.y}) ({event.x},{event.y})')
            pen.x = event.x
            pen.y = event.y


if __name__ == "__main__":
    app = tk.Tk()

    CANVAS_WIDTH = 640
    CANVAS_HEIGHT = 640

    pen = Pen()

    canvas = tk.Canvas(
        master=app,
        width=CANVAS_WIDTH,
        height=CANVAS_HEIGHT,
    )
    canvas.create_rectangle(
        0,
        0,
        CANVAS_WIDTH * 2,
        CANVAS_HEIGHT * 2,
        fill='black',
    )
    #=================== load the trained model ===================#
    # model_filename = 'hiragana_model_2019-05-04_17-05-26.h5'
    # model = tf.keras.models.load_model(model_filename)
    # model.summary()
    #===================  or load model_weights ===================#
    model_weights_filename = 'hiragana_model_weights_2019-05-04_17-05-26.h5'
    model = utils.generic_cnn_model('HRGN')
    model.load_weights(model_weights_filename)
    model.compile(
        optimizer='adam',
        loss='sparse_categorical_crossentropy',
        metrics=['accuracy'],
    )
    model.summary()
    #=================== warm up tensorflow ===================#
    img = np.ones((1, 64, 64, 1), dtype=np.float)
    model.predict(img)

    #=================== available kana ListBox ===================#
    kana_scrollbar = tk.Scrollbar(
        master=app,
    )
    available_kana = tk.Listbox(
        master=app,
        font=('MS Mincho', 16, tk.font.NORMAL),
        width=4,
    )
    available_kana.config(
        yscrollcommand=kana_scrollbar.set,
    )
    kana_scrollbar.config(
        command=available_kana.yview,
    )
    #=================== populate kana list ===================#
    for key in key_label_dict.key_dict.keys():
        available_kana.insert(tk.END, key)
    #=================== result output ===================#
    result_scrollbar = tk.Scrollbar(
        master=app,
    )
    result_label = tk.Listbox(
        master=app,
        bg='black',
        fg='white',
        font=('MS Mincho', 16, tk.font.NORMAL),
        width=10,
    )
    result_label.config(
        yscrollcommand=result_scrollbar.set,
    )
    result_scrollbar.config(
        command=result_label.yview,
    )
    #=================== tooltip ===================#
    tooltip_text = f'''Hold [Shift] then move mouse to draw.
    Press [c] to clear the canvas.
    Press [p] to predict the image.
    Press [s] to show the image will be fed into the CNN.'''
    tooltip_label = tk.Label(
        master=app,
        text=tooltip_text,
        bg='black',
        fg='white',
    )
    #=================== layout ===================#
    # the canvas
    canvas.grid(
        column=0,
        row=0,
        sticky=tk.N + tk.S + tk.E + tk.W,
    )
    # kana list
    available_kana.grid(
        column=1,
        row=0,
        sticky=tk.N + tk.S + tk.E + tk.W,
    )
    # scrollbar for kana list
    kana_scrollbar.grid(
        column=2,
        row=0,
        sticky=tk.N + tk.S + tk.E + tk.W,
    )
    # result list
    result_label.grid(
        column=3,
        row=0,
        sticky=tk.N + tk.S + tk.E + tk.W,
    )
    # scrollbar for result list
    result_scrollbar.grid(
        column=4,
        row=0,
        sticky=tk.N + tk.S + tk.E + tk.W,
    )
    # tooltip
    tooltip_label.grid(
        column=0,
        row=1,
        columnspan=4,
        sticky=tk.N + tk.S + tk.E + tk.W,
    )
    #=================== events ===================#
    canvas.bind('<Motion>', mouse_move_event)
    app.bind('<KeyRelease>', key_release)
    app.bind('<KeyPress>', key_press)
    #=================== application start ===================#
    app.mainloop()
