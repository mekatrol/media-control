import cv2
import mediapipe as mp
import csv
import os
import pyautogui
import numpy as np

from utils import resize_with_aspect_ratio

# Config
LABEL = ""
CSV_PATH = "hand_landmarks.csv"
SAVE_IMG_DIR = "cropped_images"
SAVE_IMG_DIR_CREATED = False
SAVE_CROPPED_IMAGES = False

KEY_LABEL_MAP = {
    ord("0"): "neutral",
    ord("1"): "fist",
    ord("2"): "high_five",
    ord("3"): "point",
    ord("4"): "peace",
    ord("5"): "okay",
    ord("6"): "thumbs_up",
    ord("7"): "thumbs_down"
}

HEADER = [f"{axis}{i}" for i in range(21)
          for axis in ['x', 'y', 'z']] + ["label"]


def collect_timed_samples(count, label):
    global image_count, SAVE_IMG_DIR_CREATED

    samples_captured = 0

    while samples_captured < count:
        ret, frame = cap.read()
        if not ret:
            continue

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = hands.process(rgb)

        if result.multi_hand_landmarks:
            hand_landmarks = result.multi_hand_landmarks[0]

            # Draw landmarks and bounding box
            mp_drawing.draw_landmarks(
                frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            h, w, _ = frame.shape
            xs = [lm.x * w for lm in hand_landmarks.landmark]
            ys = [lm.y * h for lm in hand_landmarks.landmark]
            x_min, x_max = int(min(xs)) - 20, int(max(xs)) + 20
            y_min, y_max = int(min(ys)) - 20, int(max(ys)) + 20
            x_min, y_min = max(x_min, 0), max(y_min, 0)
            x_max, y_max = min(x_max, w), min(y_max, h)
            cv2.rectangle(frame, (x_min, y_min),
                          (x_max, y_max), (255, 0, 255), 2)

            # Add label to frame
            cv2.putText(frame, f"Label: {label} ({samples_captured + 1}/{count})", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            # Save landmarks
            row = []
            for lm in hand_landmarks.landmark:
                row.extend([lm.x, lm.y, lm.z])
            row.append(label)
            csv_writer.writerow(row)

            # Save image
            if not SAVE_IMG_DIR_CREATED:
                os.makedirs(SAVE_IMG_DIR, exist_ok=True)
                SAVE_IMG_DIR_CREATED = True

            if SAVE_CROPPED_IMAGES:
                crop = frame[y_min:y_max, x_min:x_max]
                filename = f"{label}_{image_count:04}.jpg"
                filepath = os.path.join(SAVE_IMG_DIR, filename)
                cv2.imwrite(filepath, crop)

            image_count += 1
            samples_captured += 1

        # Display frame
        display_frame = resize_with_aspect_ratio(frame, *pyautogui.size())
        cv2.imshow("Capture", display_frame)

        # Wait until 1s from last sample
        if cv2.waitKey(5) & 0xFF == ord("q"):
            return


# Setup MediaPipe
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(static_image_mode=False,
                       max_num_hands=1, min_detection_confidence=0.5)
mp_drawing = mp.solutions.drawing_utils

# CSV setup
file_exists = os.path.exists(CSV_PATH)
csv_file = open(CSV_PATH, mode='a', newline='')
csv_writer = csv.writer(csv_file)
if not file_exists:
    csv_writer.writerow(HEADER)

# Webcam setup
cap = cv2.VideoCapture(0)
print("Press number key [0–9] to set label, 's' to save, 'q' to quit.")

image_count = 0

try:
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = hands.process(rgb)

        if result.multi_hand_landmarks:
            hand_landmarks = result.multi_hand_landmarks[0]
            mp_drawing.draw_landmarks(
                frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            # Compute bounding box from landmarks
            h, w, _ = frame.shape
            xs = [lm.x * w for lm in hand_landmarks.landmark]
            ys = [lm.y * h for lm in hand_landmarks.landmark]
            x_min, x_max = int(min(xs)) - 20, int(max(xs)) + 20
            y_min, y_max = int(min(ys)) - 20, int(max(ys)) + 20

            x_min, y_min = max(x_min, 0), max(y_min, 0)
            x_max, y_max = min(x_max, w), min(y_max, h)

            cv2.rectangle(frame, (x_min, y_min),
                          (x_max, y_max), (255, 0, 255), 2)

        cv2.putText(frame, f"Label: {LABEL}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        screen_width, screen_height = pyautogui.size()
        display_frame = resize_with_aspect_ratio(
            frame, screen_width, screen_height)

        cv2.imshow("Capture", display_frame)

        key = cv2.waitKey(1)

        # Update label on number key press
        if key in KEY_LABEL_MAP:
            LABEL = KEY_LABEL_MAP[key]
            print(f"Label set to: {LABEL}")

        elif key == ord("t") and LABEL:
            collect_timed_samples(1000, LABEL)

        elif key == ord("s") and result.multi_hand_landmarks and LABEL:
            # Save landmarks
            row = []
            for lm in hand_landmarks.landmark:
                row.extend([lm.x, lm.y, lm.z])
            row.append(LABEL)
            csv_writer.writerow(row)

            if SAVE_CROPPED_IMAGES:
                if not SAVE_IMG_DIR_CREATED:
                    os.makedirs(SAVE_IMG_DIR, exist_ok=True)
                    SAVE_IMG_DIR_CREATED = True
                crop = frame[y_min:y_max, x_min:x_max]
                filename = f"{LABEL}_{image_count:04}.jpg"
                filepath = os.path.join(SAVE_IMG_DIR, filename)
                cv2.imwrite(filepath, crop)
                print(f"Saved: {filepath}")

            image_count += 1

        elif key == ord("q"):
            break

finally:
    cap.release()
    csv_file.close()
    cv2.destroyAllWindows()
    hands.close()
    print(f"Saved to {CSV_PATH}")
