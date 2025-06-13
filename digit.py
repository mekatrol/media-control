from digit_direction import DigitDirection
from digit_type import DigitType


class Digit:
    def __init__(self, type: DigitType):
        self._type = type
        self._extended: bool = False
        self._angle: float = 0.0
        self._direction: DigitDirection = DigitDirection.NEUTRAL

    @property
    def type(self) -> 'DigitType':
        return self._type

    @type.setter
    def type(self, value: 'DigitType') -> None:
        if not isinstance(value, DigitType):
            raise TypeError("digit must be an instance of Digit enum")
        self._type = value

    @property
    def extended(self) -> bool:
        return self._extended

    @extended.setter
    def extended(self, value: bool) -> None:
        if not isinstance(value, bool):
            raise TypeError("extended must be a boolean")
        self._extended = value

    @property
    def direction(self) -> DigitDirection:
        return self._direction

    @direction.setter
    def direction(self, value: DigitDirection) -> None:
        if not isinstance(value, DigitDirection):
            raise TypeError("direction must be a DigitDirection")
        self._direction = value

    @property
    def angle(self) -> float:
        return self._angle

    @angle.setter
    def angle(self, value: float) -> None:
        # Allow ints to support e.g., `angle = 45`
        if not isinstance(value, (float, int)):
            raise TypeError("angle must be a float")
        self._angle = float(value)
