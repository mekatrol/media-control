import cv2
import mediapipe as mp
import joblib
import numpy as np
import pyautogui

from utils import resize_with_aspect_ratio

# Load model
model = joblib.load("gesture_model.pkl")

# Setup MediaPipe
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(static_image_mode=False,
                       max_num_hands=2)  # Detect up to 2 hands
mp_drawing = mp.solutions.drawing_utils

# Webcam
cap = cv2.VideoCapture(0)
print("Running real-time prediction (2 hands). Press 'q' to quit.")

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb)

    display_frame = resize_with_aspect_ratio(frame, *pyautogui.size())

    if result.multi_hand_landmarks and result.multi_handedness:
        for idx, hand_landmarks in enumerate(result.multi_hand_landmarks):
            # Draw landmarks
            mp_drawing.draw_landmarks(
                display_frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            # Extract features (21 landmarks * 3 values)
            data = []
            for lm in hand_landmarks.landmark:
                data.extend([lm.x, lm.y, lm.z])

            if len(data) == 63:
                prediction = model.predict([data])[0]
                # "Left" or "Right"
                hand_label = result.multi_handedness[idx].classification[0].label

                # Display label near wrist landmark
                wrist = hand_landmarks.landmark[0]
                h, w, _ = display_frame.shape
                cx, cy = int(wrist.x * w), int(wrist.y * h)
                cv2.putText(display_frame, f"{hand_label}: {prediction}", (cx, cy - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

    cv2.imshow("Prediction", display_frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
hands.close()
