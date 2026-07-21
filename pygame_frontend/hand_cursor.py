import cv2
import pygame
from time import time

import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision


class HandCursor:
    cap = None

    def __init__(self, radius, color, winW, winH, imageFraction=1, clickTime=1) -> None:
        self.enabled = False
        self.position = None
        self.radius = radius
        self.color = color
        self.winW = winW
        self.winH = winH
        self.imageFraction = imageFraction
        self.clickTime = clickTime

        self.imgW = 0
        self.imgH = 0
        self.remainingClickTime = clickTime
        self.prevTime = None
        self.selectedWidget = None

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

        self.hand_landmarker = vision.HandLandmarker.create_from_options(options)

        # Gesture-related attributes
        self.landmark_list = []
        self.index_finger_tip = None
        self.frame = None

    def enable(self):
        self.enabled = True

        self.cap = cv2.VideoCapture(0)
        success, img = self.cap.read()
        if success:
            self.imgH, self.imgW, _ = img.shape

    def disable(self):
        self.enabled = False
        self.position = None
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()
        self.cap = None
        self.imgW = self.imgH = 0
    
    def shouldClick(self, widget):
        if widget != self.selectedWidget:
            self.selectedWidget = widget
            self.remainingClickTime = self.clickTime
            self.prevTime = time()
            return False
        else:
            currentTime = time()
            self.remainingClickTime -= currentTime - self.prevTime
            if self.remainingClickTime > 0:
                self.prevTime = currentTime
                return False
            else:
                self.selectedWidget = self.prevTime = None
                return True

    def updatePos(self, showImage=False):
        if not self.enabled or self.cap is None:
            return

        success, img = self.cap.read()
        if not success:
            return

        self.frame = cv2.flip(img, 1)
        rgb = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)

        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=rgb
        )

        timestamp = int(time() * 1000)

        result = self.hand_landmarker.detect_for_video(
            mp_image,
            timestamp
        )

        self.position = None
        self.landmark_list = []
        self.index_finger_tip = None

        if result.hand_landmarks:
            hand = result.hand_landmarks[0]

            # Middle fingertip (landmark 12)
            self.index_finger_tip = hand[12]

            # Store all landmarks
            for lm in hand:
                self.landmark_list.append((lm.x, lm.y))

            # Compute cursor position
            minFrac = (1 - self.imageFraction) / 2
            maxFrac = 1 - minFrac

            bx = min(max(minFrac, self.index_finger_tip.x), maxFrac)
            by = min(max(minFrac, self.index_finger_tip.y), maxFrac)

            sx = (bx - minFrac) / (maxFrac - minFrac)
            sy = (by - minFrac) / (maxFrac - minFrac)

            self.position = (
                int(sx * self.winW),
                int(sy * self.winH)
            )

            if showImage:
                # Draw every landmark
                for lm in hand:
                    x = int(lm.x * self.imgW)
                    y = int(lm.y * self.imgH)
                    cv2.circle(self.frame, (x, y), 2, (0, 255, 0), -1)

                # Highlight the tracked fingertip
                ix = int(self.index_finger_tip.x * self.imgW)
                iy = int(self.index_finger_tip.y * self.imgH)
                cv2.circle(self.frame, (ix, iy), 15, (255, 0, 0), cv2.FILLED)

        if showImage:
            cv2.imshow("Hand Cursor", self.frame)

    def draw(self, win):
        if self.position:
            pygame.draw.circle(win, self.color, self.position, self.radius)
