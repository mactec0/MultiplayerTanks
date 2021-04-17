from string import ascii_letters
from threading import Thread
from random import randint
from time import sleep
from math import sqrt

from const.const import MAP_W


def get_random_string(n=32):
    return ''.join([ascii_letters[randint(0, len(ascii_letters)-1)]
                   for x in range(n)])


def clamp(v, lo, hi):
    return max(lo, min(v, hi))


def distance(x1, y1, x2, y2):
    return sqrt((x1-x2)**2 + (y1-y2)**2)


def lerp(a, b, t):
    return a * (1 - t) + b * t


def _task_callback(callback, args, t):
    sleep(t)
    callback(args)


def schedule_task(callback, args, t):
    thread = Thread(target=_task_callback, args=(callback, args, t, ))
    thread.start()


def normalize(x):
    while x < 0:
        x += MAP_W
    while x >= MAP_W:
        x -= MAP_W
    return x


def get_border_positions(x, margin):
    x = normalize(x)
    positions = [x]

    if x < margin:
        positions.append(x + MAP_W)
    if x >= MAP_W - margin:
        positions.append(x - MAP_W)

    return positions
