from typing import Tuple
import numpy as np
import cv2
import pyautogui
import math
from digit_direction import DigitDirection
from digit_type import DigitType
from hand import Hand
from hand_processor import HandProcessor, digit_names
from hand_side import HandSide


def draw_text_with_bg(
    img,
    text: str,
    org: Tuple[int, int],
    font: int,
    font_scale: float,
    text_color: Tuple[int, int, int],
    thickness: int,
    bg_color: Tuple[int, int, int] = (0, 0, 0),
    padding: int = 4
):
    text_size, baseline = cv2.getTextSize(text, font, font_scale, thickness)
    text_width, text_height = text_size
    x, y = map(int, org)

    # Rectangle coordinates
    rect_top_left = (int(x - padding), int(y - text_height - padding))
    rect_bottom_right = (int(x + text_width + padding),
                         int(y + baseline + padding))

    # Draw background rectangle
    cv2.rectangle(img, rect_top_left, rect_bottom_right, bg_color, cv2.FILLED)

    # Draw the text
    cv2.putText(img, text, (x, y), font, font_scale, text_color, thickness)


def resize_with_aspect_ratio(image, target_width, target_height):
    h, w = image.shape[:2]
    scale = min(target_width / w, target_height / h)
    new_w = int(w * scale)
    new_h = int(h * scale)
    resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)

    # Create black background
    result = np.zeros((target_height, target_width, 3), dtype=np.uint8)

    # Center the resized image
    x_offset = (target_width - new_w) // 2
    y_offset = (target_height - new_h) // 2
    result[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = resized

    return result


vertical_hand_angle_threshold = 15


def is_wake_state(hands: dict[HandSide, Hand]):
    left_hand = hands[HandSide.LEFT]
    right_hand = hands[HandSide.RIGHT]

    # Both hands must be visible
    if not left_hand.visible or not right_hand.visible:
        return False

    # Both hands must be vertical
    if math.fabs(left_hand.angle) > vertical_hand_angle_threshold or math.fabs(right_hand.angle) > vertical_hand_angle_threshold:
        return False

    # All fingers must be up and extended (dont care about thumbs)
    left_up_extended = all(
        digit.direction == DigitDirection.UP and digit.extended for digit_type, digit in left_hand.digits.items() if digit_type != DigitType.THUMB)

    right_up_extended = all(
        digit.direction == DigitDirection.UP and digit.extended for digit_type, digit in right_hand.digits.items() if digit_type != DigitType.THUMB)

    if not left_up_extended or not right_up_extended:
        return False

    return True


cv2.namedWindow("Hands", cv2.WINDOW_NORMAL)
cap = cv2.VideoCapture(0)

try:
    OUTPUT_WIDTH = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    OUTPUT_HEIGHT = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    DET_WIDTH, DET_HEIGHT = 640, 480

    with HandProcessor() as hand_processor:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            frame = cv2.flip(frame, 1)
            hands = hand_processor.get_state(frame, True)

            # optionally: use pyautogui.size() for dynamic
            screen_width, screen_height = pyautogui.size()
            display_frame = resize_with_aspect_ratio(
                frame, screen_width, screen_height)

            y_start = 25
            line_height = 25

            # Widest possible text
            text_size, baseline = cv2.getTextSize(
                'Gesture: Gesture.THUMBS_DOWN___', cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)

            text_width, text_heght = text_size

            if hands is not None:
                for i, hand in enumerate(hands.values()):
                    y = y_start
                    if hand.visible:
                        x = 20 if hand.side == HandSide.LEFT else screen_width - text_width

                        draw_text_with_bg(display_frame, f'Hand: {hand.side}', (x, y),
                                          cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                        y += line_height

                        draw_text_with_bg(display_frame, f'Gesture: {hand.gesture}', (x, y),
                                          cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                        y += line_height

                        draw_text_with_bg(display_frame, f'Rotation: {hand.angle:.1f}', (x, y),
                                          cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                        y += line_height

                        for j, digit in enumerate(hand.digits.values()):
                            draw_text_with_bg(display_frame, f'{digit_names[digit.type]}:', (x, y),
                                              cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
                            y += line_height

                            draw_text_with_bg(display_frame, f'extended: {digit.extended}', (x + 20, y),
                                              cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
                            y += line_height

                            draw_text_with_bg(display_frame, f'angle: {digit.angle:.1f}', (x + 20, y),
                                              cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
                            y += line_height

                y = y_start
                x = screen_width / 2
                draw_text_with_bg(display_frame, f'wake state: {is_wake_state(hands)}', (x, y),
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

            cv2.imshow("Hands", display_frame)

            if cv2.waitKey(5) & 0xFF == ord('q'):
                break

finally:
    cap.release()
    cv2.destroyAllWindows()
