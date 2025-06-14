from typing import Optional
import mediapipe as mp
import cv2
import joblib
from digit import Digit
from hand_side import HandSide
from digit_direction import DigitDirection
from digit_type import DigitType
from gesture import HandGesture, HandsGesture
from hand_landmark import HandLandmark
from mediapipe.framework.formats.landmark_pb2 import NormalizedLandmarkList
from math import atan2, degrees
from hand_state import HandState
from math_helper import angle_between, vector
from hand import Hand
import numpy as np

# Threshold for "significantly" higher/lower
DELTA_VERTICAL_MARGIN = 0.1

VERTICAL_HAND_ANGLE_THRESHOLD = 15

GESTURE_CONFIDENCE_PROBABILITY_THRESHOLD = 0.3
GESTURE_USE_PROBABILITY = True

digit_names = {
    DigitType.THUMB:  "Thumb",
    DigitType.INDEX:  "Index",
    DigitType.MIDDLE: "Middle",
    DigitType.RING:   "Ring",
    DigitType.PINKY:  "Pinky",
}

tip_ids = {
    DigitType.THUMB: HandLandmark.THUMB_TIP.value,
    DigitType.INDEX: HandLandmark.INDEX_TIP.value,
    DigitType.MIDDLE: HandLandmark.MIDDLE_TIP.value,
    DigitType.RING: HandLandmark.RING_TIP.value,
    DigitType.PINKY: HandLandmark.PINKY_TIP.value,
}

base_ids = {
    DigitType.THUMB: HandLandmark.THUMB_MCP.value,
    DigitType.INDEX: HandLandmark.INDEX_PIP.value,
    DigitType.MIDDLE: HandLandmark.MIDDLE_PIP.value,
    DigitType.RING: HandLandmark.RING_PIP.value,
    DigitType.PINKY: HandLandmark.PINKY_PIP.value,
}


# Each digits (TIP, BASE) landmark indices
digit_points = {
    # Thumb: Tip, IP (middle), MCP (base)
    DigitType.THUMB:  (
        HandLandmark.THUMB_TIP.value,
        HandLandmark.THUMB_IP.value,
        HandLandmark.THUMB_MCP.value
    ),

    # Fingers: Tip, DIP (middle), PIP (base)
    DigitType.INDEX:  (
        HandLandmark.INDEX_TIP.value,
        HandLandmark.INDEX_DIP.value,
        HandLandmark.INDEX_PIP.value
    ),
    DigitType.MIDDLE: (
        HandLandmark.MIDDLE_TIP.value,
        HandLandmark.MIDDLE_DIP.value,
        HandLandmark.MIDDLE_PIP.value
    ),
    DigitType.RING:   (
        HandLandmark.RING_TIP.value,
        HandLandmark.RING_DIP.value,
        HandLandmark.RING_PIP.value
    ),
    DigitType.PINKY:  (
        HandLandmark.PINKY_TIP.value,
        HandLandmark.PINKY_DIP.value,
        HandLandmark.PINKY_PIP.value
    ),
}

# Load model
model = joblib.load("gesture_model.pkl")


class HandProcessor:
    def __init__(self,
                 max_num_hands=2,
                 min_detection_confidence=0.7,
                 min_tracking_confidence=0.7,
                 detection_width=640,
                 detection_height=480):

        self.hands = None
        self.max_num_hands = max_num_hands
        self.min_detection_confidence = min_detection_confidence
        self.min_tracking_confidence = min_tracking_confidence
        self.detection_width = detection_width
        self.detection_height = detection_height

    def __enter__(self):
        self.hands = mp.solutions.hands.Hands(
            max_num_hands=self.max_num_hands,
            min_detection_confidence=self.min_detection_confidence,
            min_tracking_confidence=self.min_tracking_confidence
        )
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.hands:
            self.hands.close()

    def upate_digit(self, landmarks: NormalizedLandmarkList, digit: Digit) -> None:
        tip_idx, dip_idx, base_idx = digit_points[digit.type]
        tip = landmarks.landmark[tip_idx]
        mid = landmarks.landmark[dip_idx]
        base = landmarks.landmark[base_idx]

        v1 = vector(base, mid)
        v2 = vector(mid, tip)

        colinear_tolerance_deg: float = 10.0
        digit.angle = angle_between(v1, v2)
        digit.colinear = digit.angle < colinear_tolerance_deg

        dx = tip.x - base.x
        dy = tip.y - base.y

        if abs(dy) > abs(dx):
            if dy < -0.02:
                digit.direction = DigitDirection.UP
            elif dy > 0.02:
                digit.direction = DigitDirection.DOWN
            else:
                digit.direction = DigitDirection.NEUTRAL
        else:
            if dx > 0.02:
                digit.direction = DigitDirection.RIGHT
            elif dx < -0.02:
                digit.direction = DigitDirection.LEFT
            else:
                digit.direction = DigitDirection.NEUTRAL

    def hand_rotation_angle(self, wrist, index_mcp, side: HandSide):
        # Calculates the in-plane rotation of the hand (roll) in degrees.
        dx = index_mcp.x - wrist.x
        dy = index_mcp.y - wrist.y

        if side == HandSide.RIGHT:
            dx = wrist.x - index_mcp.x
            dy = wrist.y - index_mcp.y

        angle_rad = atan2(dy, dx)
        angle_deg = degrees(angle_rad)

        # Normalise based on hand side
        if side == HandSide.LEFT:
            angle_deg += 77  # Emperically derived
        else:
            angle_deg -= 72

        return angle_deg  # Positive means rotated counterclockwise

    def draw_landmarks(self, frame, hand_landmarks, width, height):
        # Draw landmarks as circles
        for lm in hand_landmarks.landmark:
            x, y = int(lm.x * width), int(lm.y * height)
            cv2.circle(frame, (x, y), 5, (0, 255, 0), -1)

        # Draw connections as lines
        for connection in mp.solutions.hands.HAND_CONNECTIONS:
            start_idx, end_idx = connection
            start = hand_landmarks.landmark[start_idx]
            end = hand_landmarks.landmark[end_idx]
            start_point = (int(start.x * width), int(start.y * height))
            end_point = (int(end.x * width), int(end.y * height))
            cv2.line(frame, start_point, end_point, (0, 255, 0), 2)

    def process_frame(self, frame: cv2.VideoCapture) -> list:
        # Resize to detection frame size
        detection_frame = cv2.resize(
            frame, (self.detection_width, self.detection_height))

        # Convert colour format
        image_rgb = cv2.cvtColor(detection_frame, cv2.COLOR_BGR2RGB)

        # Get hand gesture details
        results = self.hands.process(image_rgb)

        return results

    def get_state(self, frame: cv2.VideoCapture, draw_landmarks=False) -> Optional[HandState]:
        results = self.process_frame(frame)

        # Return None if no results
        if not results.multi_hand_landmarks or not results.multi_handedness:
            return None

        # Get hand state for hand side
        hands = HandState()

        # Iterate combined ordered sets
        for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
            # Get hand "Left" or "Right"
            side_label = handedness.classification[0].label

            hand_side = None
            try:
                hand_side = HandSide(side_label.lower())
            except ValueError:
                # There was an error in processing, so return None to indicate failed processing
                return None

            # Get the hand state
            hand = hands[hand_side]
            hand.visible = True

            data = []
            for lm in hand_landmarks.landmark:
                data.extend([lm.x, lm.y, lm.z])

            if len(data) == 63:
                if GESTURE_USE_PROBABILITY:

                    probs = model.predict_proba([data])[0]
                    confidence = max(probs)
                    predicted_class = model.classes_[np.argmax(probs)]

                    if confidence >= GESTURE_CONFIDENCE_PROBABILITY_THRESHOLD:
                        hand.gesture = HandGesture(predicted_class)
                    else:
                        hand.gesture = HandGesture.NONE
                else:
                    hand.gesture = HandGesture(model.predict([data])[0])

            # Compute hand rotation angle
            wrist = hand_landmarks.landmark[HandLandmark.WRIST.value]
            index_mcp = hand_landmarks.landmark[HandLandmark.INDEX_MCP.value]

            hand.angle = self.hand_rotation_angle(wrist, index_mcp, hand_side)

            colinear_digit_count = 0
            for digit_type in DigitType:
                digit = hand[digit_type]

                self.upate_digit(hand_landmarks, digit)

                if digit.colinear:
                    colinear_digit_count += 1

            if self.is_wake_gesture(hands):
                hands.gesture = HandsGesture.WAKE

            if draw_landmarks:
                self.draw_landmarks(frame, hand_landmarks,
                                    self.detection_width, self.detection_height)

        return hands

    def is_wake_gesture(self, hands: dict[HandSide, Hand]):
        left_hand = hands[HandSide.LEFT]
        right_hand = hands[HandSide.RIGHT]

        # Both hands must be visible
        if not left_hand.visible or not right_hand.visible:
            return False

        # Both hands must be vertical
        if abs(left_hand.angle) > VERTICAL_HAND_ANGLE_THRESHOLD or abs(right_hand.angle) > VERTICAL_HAND_ANGLE_THRESHOLD:
            return False

        # All fingers must be up and colinear (dont care about thumbs)
        left_up_colinear = all(
            digit.direction == DigitDirection.UP and digit.colinear for digit_type, digit in left_hand.digits.items() if digit_type != DigitType.THUMB)

        right_up_colinear = all(
            digit.direction == DigitDirection.UP and digit.colinear for digit_type, digit in right_hand.digits.items() if digit_type != DigitType.THUMB)

        if not left_up_colinear or not right_up_colinear:
            return False

        return True
