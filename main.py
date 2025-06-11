import cv2
import mediapipe as mp

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

with mp_hands.Hands(
    max_num_hands=2,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
) as hands:

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)  # Mirror full-res frame for display

        # Resize for detection
        small_frame = cv2.resize(frame, (DET_WIDTH, DET_HEIGHT))
        image_rgb = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        results = hands.process(image_rgb)

        frame_gesture_info = []

        if results.multi_hand_landmarks and results.multi_handedness:
            for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
                # "Left" or "Right"
                hand_label = handedness.classification[0].label

                lm = hand_landmarks.landmark

                # Count fingers up (excluding thumb)
                fingers_up = 0
                for i in range(1, 5):
                    tip = lm[tip_ids[i]]
                    base = lm[base_ids[i]]
                    if tip.y < base.y:
                        fingers_up += 1

                # Thumb up/down detection (only if other fingers folded)
                thumb_tip = lm[4]
                thumb_base = lm[2]
                thumb_up = thumb_tip.y < thumb_base.y - 0.05
                thumb_down = thumb_tip.y > thumb_base.y + 0.05

                if fingers_up == 0:
                    if thumb_up:
                        gesture = "Thumbs Up 👍"
                    elif thumb_down:
                        gesture = "Thumbs Down 👎"
                    else:
                        gesture = "Neutral Thumb"
                else:
                    gesture = {
                        0: "Fist",
                        1: "One ☝️",
                        2: "Peace ✌️",
                        3: "Three 🤟",
                        4: "Four ✋",
                    }.get(fingers_up, "Unknown")

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
                    "landmarks": hand_landmarks,  # Use normalized landmarks for drawing scaled manually
                })

        # Draw landmarks and connections on full-res frame
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                draw_hand_landmarks_fullres(
                    frame, hand_landmarks, OUTPUT_WIDTH, OUTPUT_HEIGHT)

        # Display text info: left hand on left, right hand on right
        for info in frame_gesture_info:
            x_pos = 20 if info["hand"] == "Left" else OUTPUT_WIDTH - 350
            y_base = 50

            cv2.putText(frame, f'Hand: {info["hand"]}', (x_pos, y_base),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(frame, f'Gesture: {info["gesture"]}', (x_pos, y_base + 35),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            for j, text in enumerate(info["directions"]):
                cv2.putText(frame, text, (x_pos, y_base + 70 + j * 25),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)

        cv2.imshow("Two Hands - Gesture + Directions", frame)

        if cv2.waitKey(5) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()
