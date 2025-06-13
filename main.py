import cv2
from hand_processor import HandProcessor
from hand_state import HandSide

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

            if hands is not None:

                # Display text info: left hand on left, right hand on right
                for hand in hands.values():
                    x_pos = 20 if hand.side == HandSide.LEFT else OUTPUT_WIDTH - 350
                    y_base = 50

                    cv2.putText(frame, f'Hand: {hand.side}', (x_pos, y_base),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

                    cv2.putText(frame, f'Gesture: {hand.gesture}', (x_pos, y_base + 35),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

                    cv2.putText(frame, f'Rotation: {hand.angle}', (x_pos, y_base + 105),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

                    j = 0
                    for digit in hand.digit_states.values():
                        cv2.putText(frame, f'{digit.extended}', (x_pos, y_base + 140 + j * 25),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)

                        cv2.putText(frame, f'{digit.angle}', (x_pos, y_base + 240 + j * 25),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)

                        j += 1

            cv2.imshow("Hands", frame)

            if cv2.waitKey(5) & 0xFF == ord('q'):
                break

finally:
    cap.release()
    cv2.destroyAllWindows()
