from enum import Enum
from typing import Optional
from digit import Digit
from digit_state import DigitState
from gesture import Gesture


class HandSide(Enum):
    LEFT = "left"
    RIGHT = "right"


class HandState:
    def __init__(self, side: HandSide):
        self._side = side
        self._gesture: Optional[Gesture] = None
        self._angle: float = 0.0
        self._digit_states: dict[Digit, DigitState] = {
            Digit.PINKY:  DigitState(Digit.PINKY),
            Digit.RING:   DigitState(Digit.RING),
            Digit.MIDDLE: DigitState(Digit.MIDDLE),
            Digit.INDEX:  DigitState(Digit.INDEX),
            Digit.THUMB:  DigitState(Digit.THUMB)
        }

    def __getitem__(self, digit: Digit) -> DigitState:
        if not isinstance(digit, Digit):
            raise TypeError("Key must be an instance of Digit enum")
        return self._digit_states[digit]

    def __setitem__(self, digit: Digit, state: DigitState) -> None:
        if not isinstance(digit, Digit):
            raise TypeError("Key must be an instance of Digit enum")
        if not isinstance(state, DigitState):
            raise TypeError("Value must be an instance of DigitState")
        if state.digit != digit:
            raise ValueError(
                "DigitState.digit does not match the provided Digit key")
        self._digit_states[digit] = state

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
    def digit_states(self) -> dict[Digit, DigitState]:
        # Optionally return a copy to protect internal state
        return self._digit_states.copy()

    @property
    def angle(self) -> float:
        return self._angle

    @angle.setter
    def angle(self, value: float) -> None:
        # Allow ints to support e.g., `angle = 45`
        if not isinstance(value, (float, int)):
            raise TypeError("angle must be a float")
        self._angle = float(value)
