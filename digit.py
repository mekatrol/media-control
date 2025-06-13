from enum import Enum


class Digit(Enum):
    THUMB = 0
    INDEX = 1
    MIDDLE = 2
    RING = 3
    PINKY = 4


class DigitDirection(Enum):
    NEUTRAL = 0
    UP = 1
    DOWN = 2
    LEFT = 3
    RIGHT = 4
