import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import pyautogui
import random
import util
import time
import numpy as np

hover_start_time = 0
hover_threshold = 1.0  # seconds required to trigger hover click
hover_target = None

from pynput.mouse import Button, Controller
mouse = Controller()


screen_width, screen_height = pyautogui.size()

base_options = python.BaseOptions(
    model_asset_path="hand_landmarker.task"
)

options = vision.HandLandmarkerOptions(
    base_options=base_options,
    num_hands=1,
    min_hand_detection_confidence=0.7,
    min_tracking_confidence=0.7,
    min_hand_presence_confidence=0.7,
    running_mode=vision.RunningMode.VIDEO
)

hand_landmarker = vision.HandLandmarker.create_from_options(options)

prev_thumb_index_dist = None
def find_finger_tip(result):
    if result.hand_landmarks:
        return result.hand_landmarks[0][8]   # Index fingertip

    return None
screen_width, screen_height = pyautogui.size()

def move_mouse(index_finger_tip, winW, winH):
    if index_finger_tip is not None:
        x = int(index_finger_tip.x * winW)
        y = int(index_finger_tip.y * winH)
        # Clamp inside Pygame window
        x = max(0, min(x, winW))
        y = max(0, min(y, winH))
        return (x, y)
    return None

def is_left_click(landmark_list, thumb_index_dist):
             return thumb_index_dist < 100


def is_right_click(landmark_list, thumb_index_dist):
    return (
            util.get_angle(landmark_list[9], landmark_list[10], landmark_list[12]) < 50 and
            util.get_angle(landmark_list[5], landmark_list[6], landmark_list[8]) > 90  and
            thumb_index_dist > 50
    )


def is_double_click(landmark_list, thumb_index_dist):
    return (
            util.get_angle(landmark_list[5], landmark_list[6], landmark_list[8]) < 50 and
            util.get_angle(landmark_list[9], landmark_list[10], landmark_list[12]) < 50 and
            thumb_index_dist > 50
    )
def hover_click(hand_pos, buttons):
    """
    hand_pos : (x, y) of hand cursor
    buttons : list of AppButton or any object with isOver() method
    Returns: button clicked if hover is completed, else None
    """
    global hover_start_time, hover_target

    if hand_pos is None:
        hover_start_time = 0
        hover_target = None
        return None

    # check which button is currently hovered
    current_target = None
    for btn in buttons:
        if btn.isOver(hand_pos):
            current_target = btn
            break

    if current_target is None:
        # not hovering any button
        hover_start_time = 0
        hover_target = None
        return None

    if hover_target != current_target:
        # new hover target, reset timer
        hover_target = current_target
        hover_start_time = time.time()
        return None

    # calculate hover duration
    elapsed = time.time() - hover_start_time
    if elapsed >= hover_threshold:
        hover_start_time = 0  # reset after click
        return current_target  # trigger click

    return None

def is_screenshot(landmark_list, thumb_index_dist):
    return (
            util.get_angle(landmark_list[5], landmark_list[6], landmark_list[8]) < 50 and
            util.get_angle(landmark_list[9], landmark_list[10], landmark_list[12]) < 50 and
            thumb_index_dist < 50
    )


def detect_gesture(landmark_list):
    if len(landmark_list) < 21:
        return None

    # calculate thumb_index_dist
    thumb_index_dist = util.get_distance([landmark_list[4], landmark_list[8]])  # thumb tip to index tip

    if is_left_click(landmark_list, thumb_index_dist):
        return "left_click"
    elif is_right_click(landmark_list, thumb_index_dist):
        return "right_click"
    elif is_double_click(landmark_list, thumb_index_dist):
        return "double_click"
    elif is_screenshot(landmark_list, thumb_index_dist):
        return "screenshot"
    else:
        return None
    

def main():
    draw = mp.solutions.drawing_utils
    cap = cv2.VideoCapture(0)
    start_time = time.time()

    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            mp_image = mp.Image(
                image_format=mp.ImageFormat.SRGB,
                data=rgb
            )

            timestamp = int((time.time() - start_time) * 1000)

            result = hand_landmarker.detect_for_video(
                mp_image,
                timestamp
            )

            landmark_list = []

            if result.hand_landmarks:
                hand = result.hand_landmarks[0]

                for lm in hand:
                    landmark_list.append((lm.x, lm.y))

                    x = int(lm.x * frame.shape[1])
                    y = int(lm.y * frame.shape[0])
                    cv2.circle(frame, (x, y), 2, (0, 255, 0), -1)

            gesture = detect_gesture(landmark_list)

            if gesture:
                print(gesture)

            cv2.imshow('Frame', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        hand_landmarker.close()
        cap.release()
        cv2.destroyAllWindows()
