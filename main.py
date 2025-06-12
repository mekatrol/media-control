import cv2
import mediapipe as mp
from hands import Hands
from gesture import Gesture

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
mp_connections = mp.solutions.hands.HAND_CONNECTIONS

finger_names = ['Thumb', 'Index', 'Middle', 'Ring', 'Pinky']
tip_ids = [4, 8, 12, 16, 20]
base_ids = [2, 6, 10, 14, 18]  # Thumb MCP, others PIP


def draw_hand_landmarks_fullres(frame, hand_landmarks, width, height):
    # Draw landmarks as circles
    for lm in hand_landmarks.landmark:
        x, y = int(lm.x * width), int(lm.y * height)
        cv2.circle(frame, (x, y), 5, (0, 255, 0), -1)

    # Draw connections as lines
    for connection in mp_connections:
        start_idx, end_idx = connection
        start = hand_landmarks.landmark[start_idx]
        end = hand_landmarks.landmark[end_idx]
        start_point = (int(start.x * width), int(start.y * height))
        end_point = (int(end.x * width), int(end.y * height))
        cv2.line(frame, start_point, end_point, (0, 255, 0), 2)


cap = cv2.VideoCapture(0)

OUTPUT_WIDTH = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
OUTPUT_HEIGHT = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

DET_WIDTH, DET_HEIGHT = 640, 480

with Hands() as hands:

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Flip horizontally as person is facing screen
        frame = cv2.flip(frame, 1)

        frame_gesture_info = hands.get_state(frame, True)

        # Display text info: left hand on left, right hand on right
        for info in frame_gesture_info:
            x_pos = 20 if info["hand"] == "Left" else OUTPUT_WIDTH - 350
            y_base = 50

            cv2.putText(frame, f'Hand: {info["hand"]}', (x_pos, y_base),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            cv2.putText(frame, f'Gesture: {info["gesture"]}', (x_pos, y_base + 35),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            cv2.putText(frame, f'Up: {info["fingers_up"]}', (x_pos, y_base + 70),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            cv2.putText(frame, f'Rotation: {info["rotation_angle"]}', (x_pos, y_base + 105),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            for j, text in enumerate(info["directions"]):
                cv2.putText(frame, text, (x_pos, y_base + 140 + j * 25),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)

            for j, text in enumerate(info["extensions"]):
                cv2.putText(frame, text, (x_pos, y_base + 240 + j * 25),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)

        cv2.imshow("Gestures", frame)

        if cv2.waitKey(5) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()
