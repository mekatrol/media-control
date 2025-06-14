from typing import Optional
from gesture import HandsGesture
from hand import Hand
from hand_side import HandSide


class HandState:
    def __init__(self):
        self._gesture: Optional[HandsGesture] = None

        self._hands: dict[HandSide, Hand] = {
            HandSide.LEFT: Hand(HandSide.LEFT),
            HandSide.RIGHT: Hand(HandSide.RIGHT)
        }

    def __getitem__(self, side: HandSide) -> Hand:
        if not isinstance(side, HandSide):
            raise TypeError("side must be an instance of HandSide enum")
        return self._hands[side]

    def __setitem__(self, hand_side: HandSide, hand: Hand) -> None:
        if not isinstance(hand_side, HandSide):
            raise TypeError("hand_side must be an instance of HandSide enum")
        if not isinstance(hand, Hand):
            raise TypeError("hand must be an instance of Hand")
        if hand.side != hand_side:
            raise ValueError(
                "hand.side does not match the provided hand_side")
        self._hands[hand_side] = hand

    @property
    def gesture(self) -> Optional[HandsGesture]:
        return self._gesture

    @gesture.setter
    def gesture(self, value: Optional[HandsGesture]) -> None:
        if value is not None and not isinstance(value, HandsGesture):
            raise TypeError("gesture must be an instance of Gesture or None")
        self._gesture = value

    @property
    def hands(self) -> dict[HandSide, Hand]:
        return self._hands

    @property
    def hand_list(self) -> list[Hand]:
        # Returns hands as a list: [left, right]
        return [self._hands[HandSide.LEFT], self._hands[HandSide.RIGHT]]
