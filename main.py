# imports ---------------------
from concurrent.futures import process
from locale import normalize
from PIL import ImageGrab, Image
import cv2
import numpy as np
import time
import tkinter as tk
from tkinter import ttk
from io import BytesIO
import AppKit
import webbrowser
import os
from datetime import datetime

# global variables -----------------------
board_coordinates = None
state_check_interval = 1  # milliseconds
check_redundancies = 4


# functions --------------------------
def get_screenshot():
    return ImageGrab.grab()

def PIL_to_cv2(pil_img):
    pil_img = pil_img.convert('RGB')
    open_cv_img = np.array(pil_img)
    open_cv_img = open_cv_img[:, :, ::-1].copy()
    return open_cv_img

def crop_image(image, left, top, right, bottom):
    return image[top:bottom, left:right]

def mse(imageA, imageB):
	err = np.sum((imageA.astype("float") - imageB.astype("float")) ** 2)
	err /= float(imageA.shape[0] * imageA.shape[1])
	return err

def is_board_onscreen():
    threshold = 15900000000.0

    ss = get_screenshot()
    ss = PIL_to_cv2(ss)

    white_starting_img = cv2.imread('assets/white_start.png')
    black_starting_img = cv2.imread('assets/black_start.png')

    white_result = cv2.matchTemplate(ss, white_starting_img, cv2.TM_CCOEFF)
    black_result = cv2.matchTemplate(ss, black_starting_img, cv2.TM_CCOEFF)

    if np.amax(white_result) > np.amax(black_result):
        result = white_result
    else:
        result = black_result

    return np.amax(result) > threshold

def get_board():
    global board_coordinates

    ss = get_screenshot()
    ss = PIL_to_cv2(ss)

    if board_coordinates != None:

        left = board_coordinates['left']
        top = board_coordinates['top']
        right = board_coordinates['right']
        bottom = board_coordinates['bottom']

        board_img = crop_image(ss, left, top, right, bottom)
        return board_img

    white_starting_img = cv2.imread('assets/white_start.png')
    black_starting_img = cv2.imread('assets/black_start.png')

    white_result = cv2.matchTemplate(ss, white_starting_img, cv2.TM_CCOEFF)
    black_result = cv2.matchTemplate(ss, black_starting_img, cv2.TM_CCOEFF)

    if np.amax(white_result) > np.amax(black_result):
        result = white_result
        starting_image = white_starting_img
    else:
        result = black_result
        starting_image = black_starting_img

    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

    height, width = starting_image.shape[:2]

    top_left = max_loc
    bottom_right = (top_left[0] + width, top_left[1] + height)

    left = top_left[0]
    top = top_left[1]
    right = bottom_right[0]
    bottom = bottom_right[1]

    board_coordinates = {
        'left': left,
        'top': top,
        'right': right,
        'bottom': bottom
    }

    board_img = crop_image(ss, left, top, right, bottom)
    return board_img

def process_board(img):
    img = img.copy()
    img[(img != 0) & (img != 255)] = 177
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return img

# GUI & Logic --------------------------------
def check_state_change():
    root.after(state_check_interval, check_state_change)

    previous_board = board_states[-1]
    previous_processed = process_board(previous_board)

    current_boards = []
    for i in range(check_redundancies):
        current_boards.append(get_board())

    current_processed = process_board(current_boards[0])
    min_mse = mse(previous_processed, current_processed)
    min_board = current_boards[0]

    for i in current_boards:
        current_processed = process_board(i)
        ith_mse = mse(previous_processed, current_processed)
        if ith_mse < min_mse:
            min_mse = ith_mse
            min_board = i

    mse_threshold = 1
    if min_mse < mse_threshold:
        print('no new state')
        return

    #last_board = i
    #board_states.append(last_board)
    print('new state')
    AppKit.NSBeep()
    AppKit.NSBeep()
    board_states.append(min_board)

def end_game():
    root.destroy()
    board_imgs = [Image.fromarray(b) for b in board_states]
    game_gif = BytesIO()
    board_imgs[0].save(game_gif, save_all = True, append_images = board_imgs[1:],
                        duration = 1000, loop = 0, format = 'GIF')
    game_gif.seek(0)
    open('gifs/' + datetime.now().strftime("%d%m%Y%H%M%S") + '.gif', 'wb').write(game_gif.read())
    webbrowser.open('file://' + os.path.realpath('view.html'))


def start_game():
    button.configure(text = 'End Game', command = end_game)
    board_states.append(get_board())
    root.after(state_check_interval, check_state_change)



# MAIN -----------------------------------
board_states = []

while not is_board_onscreen():
    print('remove me')
    time.sleep(0.1)

# GUI 
root = tk.Tk()
root.geometry('150x60')
root.resizable(False, False)
root.title('Button Demo')
button = ttk.Button(root, text = "Start Game", command = start_game)
button.grid(row=1, column=1, ipady=10, ipadx=10, padx=10)

root.mainloop()
