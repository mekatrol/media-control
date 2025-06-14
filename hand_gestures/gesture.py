from enum import Enum, auto


class HandGesture(Enum):
    NONE = "none"
    NEUTRAL = "neutral"
    FIST = "fist"
    HIGH_FIVE = "high_five"
    POINT = "point"
    PEACE = "peace"
    OK = "okay"
    THUMBS_UP = "thumbs_up"
    THUMBS_DOWN = "thumbs_down"


class HandsGesture(Enum):
    NONE = auto()
    WAKE = auto()
