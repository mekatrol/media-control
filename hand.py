from typing import Optional
from hand_side import HandSide
from digit_type import DigitType
from digit import Digit
from gesture import Gesture


class Hand:
    def __init__(self, side: HandSide):
        self._side = side
        self._gesture: Optional[Gesture] = None
        self._angle: float = 0.0
        self._visible: bool = False
        self._digits: dict[DigitType, Digit] = {
            DigitType.PINKY:  Digit(DigitType.PINKY),
            DigitType.RING:   Digit(DigitType.RING),
            DigitType.MIDDLE: Digit(DigitType.MIDDLE),
            DigitType.INDEX:  Digit(DigitType.INDEX),
            DigitType.THUMB:  Digit(DigitType.THUMB)
        }

    def __getitem__(self, digit: DigitType) -> Digit:
        if not isinstance(digit, DigitType):
            raise TypeError("Key must be an instance of Digit enum")
        return self._digits[digit]

    def __setitem__(self, digit: DigitType, state: Digit) -> None:
        if not isinstance(digit, DigitType):
            raise TypeError("Key must be an instance of Digit enum")
        if not isinstance(state, Digit):
            raise TypeError("Value must be an instance of DigitState")
        if state.type != digit:
            raise ValueError(
                "DigitState.digit does not match the provided Digit key")
        self._digits[digit] = state

    @property
    def visible(self) -> bool:
        return self._visible

    @visible.setter
    def visible(self, value: bool) -> None:
        if not isinstance(value, bool):
            raise TypeError("visible must be a boolean")
        self._visible = value

    @property
    def side(self) -> HandSide:
        return self._side

    @property
    def gesture(self) -> Optional[Gesture]:
        return self._gesture

    @gesture.setter
    def gesture(self, value: Optional[Gesture]) -> None:
        if value is not None and not isinstance(value, Gesture):
            raise TypeError("gesture must be an instance of Gesture or None")
        self._gesture = value

    @property
    def digits(self) -> dict[DigitType, Digit]:
        return self._digits

    @property
    def angle(self) -> float:
        return self._angle

    @angle.setter
    def angle(self, value: float) -> None:
        # Allow ints to support e.g., `angle = 45`
        if not isinstance(value, (float, int)):
            raise TypeError("angle must be a float")
        self._angle = float(value)
