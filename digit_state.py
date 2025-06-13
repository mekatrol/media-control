from digit import Digit, DigitDirection


class DigitState:
    def __init__(self, digit: 'Digit'):
        self._digit = digit
        self._extended: bool = False
        self._angle: float = 0.0
        self._direction: DigitDirection = DigitDirection.NEUTRAL

    @property
    def digit(self) -> 'Digit':
        return self._digit

    @digit.setter
    def digit(self, value: 'Digit') -> None:
        if not isinstance(value, Digit):
            raise TypeError("digit must be an instance of Digit enum")
        self._digit = value

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
