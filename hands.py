from enum import Enum
import mediapipe as mp
import cv2
from gesture import Gesture
from hand_landmark import HandLandmark
from mediapipe.framework.formats.landmark_pb2 import NormalizedLandmarkList
from math_helper import angle_between, vector

# Threshold for "significantly" higher/lower
DELTA_VERTICAL_MARGIN = 0.1

finger_names = ['Thumb', 'Index', 'Middle', 'Ring', 'Pinky']
tip_ids = [
    HandLandmark.THUMB_TIP.value,
    HandLandmark.INDEX_TIP.value,
    HandLandmark.MIDDLE_TIP.value,
    HandLandmark.RING_TIP.value,
    HandLandmark.PINKY_TIP.value
]

base_ids = [
    HandLandmark.THUMB_MCP.value,
    HandLandmark.INDEX_PIP.value,
    HandLandmark.MIDDLE_PIP.value,
    HandLandmark.RING_PIP.value,
    HandLandmark.PINKY_PIP.value
]


class Digit(Enum):
    THUMB = 0
    INDEX = 1
    MIDDLE = 2
    RING = 3
    PINKY = 4


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


class Hands:
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

    def process(self, frame: cv2.VideoCapture) -> list:
        # Resize to detection frame size
        detection_frame = cv2.resize(
            frame, (self.detection_width, self.detection_height))

        # Convert colour format
        image_rgb = cv2.cvtColor(detection_frame, cv2.COLOR_BGR2RGB)

        # Get hand gesture details
        results = self.hands.process(image_rgb)

        return results

    def get_state(self, frame: cv2.VideoCapture, draw_landmarks=False) -> list:
        results = self.process(frame)

        # None found then return empty list
        if not results.multi_hand_landmarks or not results.multi_handedness:
            return []

        # Create list
        frame_gesture_info = []

        # Iterate combined ordered sets
        for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
            # Get hand "Left" or "Right"
            hand_label = handedness.classification[0].label

            # Shorthand variable
            lm = hand_landmarks.landmark

            # Count fingers up (excluding thumb)
            fingers_up = 0
            fingers_extended = 0
            extensions = []
            for i in range(1, 5):
                tip = lm[tip_ids[i]]
                base = lm[base_ids[i]]
                if tip.y < (base.y - DELTA_VERTICAL_MARGIN):
                    fingers_up += 1

                extended = self.is_finger_straight(hand_landmarks, Digit(i))
                extensions.append(f"{finger_names[i]}: {extended}")

                if extended:
                    fingers_extended += 1

            thumb_tip = lm[HandLandmark.THUMB_TIP.value]
            thumb_base = lm[HandLandmark.THUMB_MCP.value]
            thumb_up = thumb_tip.y < thumb_base.y - DELTA_VERTICAL_MARGIN
            thumb_down = thumb_tip.y > thumb_base.y + DELTA_VERTICAL_MARGIN

            # If there are no fingers up then is a fist, thumbs up, or thumbs down
            if fingers_extended == 0:
                if thumb_up:
                    gesture = Gesture.THUMBS_UP
                elif thumb_down:
                    gesture = Gesture.THUMBS_DOWN
                else:
                    gesture = Gesture.FIST
            else:
                print('xxxxx')
                gesture = {
                    0: Gesture.FIST,
                    1: Gesture.ONE,
                    2: Gesture.TWO,
                    3: Gesture.THREE,
                    4: Gesture.FOUR,
                }.get(fingers_extended, "Unknown")

            # Finger directions (all fingers including thumb)
            directions = []
            for i in range(5):
                tip = lm[tip_ids[i]]
                base = lm[base_ids[i]]
                dx = tip.x - base.x
                dy = tip.y - base.y

                if abs(dy) > abs(dx):
                    if dy < -0.02:
                        direction = "Up"
                    elif dy > 0.02:
                        direction = "Down"
                    else:
                        direction = "Neutral"
                else:
                    if dx > 0.02:
                        direction = "Right"
                    elif dx < -0.02:
                        direction = "Left"
                    else:
                        direction = "Neutral"

                directions.append(f"{finger_names[i]}: {direction}")

            frame_gesture_info.append({
                "hand": hand_label,
                "gesture": gesture,
                "directions": directions,
                "landmarks": hand_landmarks,
                "fingers_up": fingers_up,
                "extensions": extensions
            })

            if draw_landmarks:
                self.draw_landmarks(frame, hand_landmarks,
                                    self.detection_width, self.detection_height)

        return frame_gesture_info
