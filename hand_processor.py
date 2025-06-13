from typing import Optional
import mediapipe as mp
import cv2
from digit import Digit, DigitDirection
from gesture import Gesture
from hand_landmark import HandLandmark
from mediapipe.framework.formats.landmark_pb2 import NormalizedLandmarkList
from math import atan2, degrees
from math_helper import angle_between, vector
from hand_state import HandSide, HandState

# Threshold for "significantly" higher/lower
DELTA_VERTICAL_MARGIN = 0.1

digit_names = {
    Digit.THUMB:  "Thumb",
    Digit.INDEX:  "Index",
    Digit.MIDDLE: "Middle",
    Digit.RING:   "Ring",
    Digit.PINKY:  "Pinky",
}

tip_ids = {
    Digit.THUMB: HandLandmark.THUMB_TIP.value,
    Digit.INDEX: HandLandmark.INDEX_TIP.value,
    Digit.MIDDLE: HandLandmark.MIDDLE_TIP.value,
    Digit.RING: HandLandmark.RING_TIP.value,
    Digit.PINKY: HandLandmark.PINKY_TIP.value,
}

base_ids = {
    Digit.THUMB: HandLandmark.THUMB_MCP.value,
    Digit.INDEX: HandLandmark.INDEX_PIP.value,
    Digit.MIDDLE: HandLandmark.MIDDLE_PIP.value,
    Digit.RING: HandLandmark.RING_PIP.value,
    Digit.PINKY: HandLandmark.PINKY_PIP.value,
}


# Each digits (TIP, BASE) landmark indices
DIGIT_POINTS = {
    # Thumb: Tip, IP (middle), MCP (base)
    Digit.THUMB:  (
        HandLandmark.THUMB_TIP.value,
        HandLandmark.THUMB_IP.value,
        HandLandmark.THUMB_MCP.value
    ),

    # Fingers: Tip, DIP (middle), PIP (base)
    Digit.INDEX:  (
        HandLandmark.INDEX_TIP.value,
        HandLandmark.INDEX_DIP.value,
        HandLandmark.INDEX_PIP.value
    ),
    Digit.MIDDLE: (
        HandLandmark.MIDDLE_TIP.value,
        HandLandmark.MIDDLE_DIP.value,
        HandLandmark.MIDDLE_PIP.value
    ),
    Digit.RING:   (
        HandLandmark.RING_TIP.value,
        HandLandmark.RING_DIP.value,
        HandLandmark.RING_PIP.value
    ),
    Digit.PINKY:  (
        HandLandmark.PINKY_TIP.value,
        HandLandmark.PINKY_DIP.value,
        HandLandmark.PINKY_PIP.value
    ),
}


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

    def is_finger_straight(self, landmarks: NormalizedLandmarkList, digit: Digit, threshold_deg: float = 10.0) -> float:
        tip_idx, dip_idx, base_idx = DIGIT_POINTS[digit]
        tip = landmarks.landmark[tip_idx]
        mid = landmarks.landmark[dip_idx]
        base = landmarks.landmark[base_idx]

        v1 = vector(base, mid)
        v2 = vector(mid, tip)

        angle = angle_between(v1, v2)

        return angle < threshold_deg

    def hand_rotation_angle(self, wrist, index_mcp):
        # Calculates the in-plane rotation of the hand (roll) in degrees.
        dx = index_mcp.x - wrist.x
        dy = index_mcp.y - wrist.y

        angle_rad = atan2(dy, dx)
        angle_deg = degrees(angle_rad)

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

    def get_state(self, frame: cv2.VideoCapture, draw_landmarks=False) -> Optional[dict[HandSide, HandState]]:
        results = self.process_frame(frame)

        # Return None if no results
        if not results.multi_hand_landmarks or not results.multi_handedness:
            return None

        # Get hand state for hand side
        hands_state: dict[HandSide, HandState] = {
            HandSide.LEFT: HandState(HandSide.LEFT),
            HandSide.RIGHT: HandState(HandSide.RIGHT)
        }

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
            hand_state = hands_state[hand_side]

            # Shorthand variable
            lm = hand_landmarks.landmark

            # Compute hand rotation angle
            wrist = lm[HandLandmark.WRIST.value]
            index_mcp = lm[HandLandmark.INDEX_MCP.value]

            hand_state.angle = self.hand_rotation_angle(wrist, index_mcp)

            digits_extended = 0
            for digit in Digit:
                digit_state = hand_state[digit]

                digit_state.extended = self.is_finger_straight(
                    hand_landmarks, digit)

                if digit_state.extended:
                    digits_extended += 1

                tip = lm[tip_ids[digit]]
                base = lm[base_ids[digit]]

                dx = tip.x - base.x
                dy = tip.y - base.y

                if abs(dy) > abs(dx):
                    if dy < -0.02:
                        digit_state.direction = DigitDirection.UP
                    elif dy > 0.02:
                        digit_state.direction = DigitDirection.DOWN
                    else:
                        digit_state.direction = DigitDirection.NEUTRAL
                else:
                    if dx > 0.02:
                        digit_state.direction = DigitDirection.RIGHT
                    elif dx < -0.02:
                        digit_state.direction = DigitDirection.LEFT
                    else:
                        digit_state.direction = DigitDirection.NEUTRAL

            thumb_tip = lm[HandLandmark.THUMB_TIP.value]
            thumb_base = lm[HandLandmark.THUMB_MCP.value]
            thumb_up = thumb_tip.y < thumb_base.y - DELTA_VERTICAL_MARGIN
            thumb_down = thumb_tip.y > thumb_base.y + DELTA_VERTICAL_MARGIN

            if digits_extended == 0:
                if thumb_up:
                    hand_state.gesture = Gesture.THUMBS_UP
                elif thumb_down:
                    hand_state.gesture = Gesture.THUMBS_DOWN
                else:
                    hand_state.gesture = Gesture.FIST
            else:
                hand_state.gesture = {
                    0: Gesture.FIST,
                    1: Gesture.ONE,
                    2: Gesture.TWO,
                    3: Gesture.THREE,
                    4: Gesture.FOUR,
                }.get(digits_extended, Gesture.NONE)

            if draw_landmarks:
                self.draw_landmarks(frame, hand_landmarks,
                                    self.detection_width, self.detection_height)

        return hands_state
