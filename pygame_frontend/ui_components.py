import pygame
from pygame import mixer
from abc import ABC, abstractmethod
from utils import *
import cv2
import os
import math
import random
import time
import numpy as np

mixer.init()

# ---------- Global Theme ----------
NEON_CYAN = (0, 200, 200)
NEON_CYAN_BRIGHT = (0, 255, 230)
DARK_BG = (6, 12, 20)
CARD_BG = (12, 20, 28)
TEXT_WHITE = (240, 245, 250)

# ---------- Video background with optional vignette ----------
class VideoBackground:
    def __init__(self, video_path, width, height, apply_vignette=True):
        self.cap = cv2.VideoCapture(video_path)
        self.width = width
        self.height = height
        self.scale = 1.0
        self.apply_vignette = apply_vignette

    def draw(self, win):
        ret, frame = self.cap.read()
        if not ret:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = self.cap.read()
            if not ret:
                surf = pygame.Surface((self.width, self.height))
                surf.fill(DARK_BG)
                win.blit(surf, (0, 0))
                return
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = cv2.resize(frame, (self.width, self.height))
        frame = (frame * 0.85).astype('uint8')

        if self.apply_vignette:
            rows, cols, _ = frame.shape
            X_kernel = cv2.getGaussianKernel(cols, cols/2)
            Y_kernel = cv2.getGaussianKernel(rows, rows/2)
            kernel = Y_kernel * X_kernel.T
            mask = 255 * kernel / np.linalg.norm(kernel)
            for c in range(3):
                frame[:, :, c] = frame[:, :, c] * (0.6 + 0.4 * mask/255.0)

        surf = pygame.surfarray.make_surface(frame.swapaxes(0,1))
        win.blit(surf, (0, 0))


# ---------- Base Widget ----------
class Widget(ABC):
    def __init__(self, center) -> None:
        self.center = tuple(center)
        self.scale = 1.0
        self.speed = 0
        self.targetPos = self.center
        self.targetScale = self.scale
        self.moving = False

    @abstractmethod
    def draw(self, win):
        self._move()

    @abstractmethod
    def isOver(self, pos):
        if self.moving or pos is None:
            return False
        return True

    def click(self):
        pass

    def _move(self):
        if not self.moving:
            return

        if self.center == self.targetPos:
            self.scale = self.targetScale
            self.speed = 0
            self.moving = False
            return

        cX, cY = self.center
        tX, tY = self.targetPos
        dX, dY = tX - cX, tY - cY
        d = math.hypot(dX, dY)
        if d < 0.5:
            self.center = self.targetPos
            self.scale = self.targetScale
            self.moving = False
            return

        sX, sY = dX / d * self.speed, dY / d * self.speed
        newX, newY = cX + sX, cY + sY
        self.scale += (self.targetScale - self.scale) * min(0.18, self.speed / (d + 1))

        if (sX > 0 and newX > tX) or (sX < 0 and newX < tX):
            newX = tX
        if (sY > 0 and newY > tY) or (sY < 0 and newY < tY):
            newY = tY

        self.center = (newX, newY)

    def setTarget(self, targetPos, targetScale, speed):
        if self.moving and self.targetPos == targetPos and abs(self.targetScale - targetScale) < 1e-6:
            return
        self.targetPos = tuple(targetPos)
        self.targetScale = targetScale
        self.speed = max(0.8, speed)
        self.moving = True


# ---------- JarVis Core ----------
class JarVis(Widget):
    def __init__(self, center, radius, textSurface, defaultCol=NEON_CYAN, listenCol=NEON_CYAN_BRIGHT) -> None:
        super().__init__(center)
        self.radius = radius
        self.defaultCol = defaultCol
        self.listenCol = listenCol
        self.textSurface = textSurface
        self.color = defaultCol
        self.glow_color = NEON_CYAN_BRIGHT
        self.pulse_speed = 0.0022

    def isOver(self, pos):
        if not super().isOver(pos):
            return False
        r = self.radius * self.scale
        return (pos[0] - self.center[0])**2 + (pos[1] - self.center[1])**2 <= r*r

    def draw(self, win):
        super().draw(win)
        t = pygame.time.get_ticks()
        pulse = (math.sin(t * self.pulse_speed) + 1) / 2.0

        glow_count = 8
        base_glow_radius = int(self.radius * self.scale * 1.1)
        for i in range(glow_count, 0, -1):
            rr = int(base_glow_radius + i * 6 + pulse * 6)
            alpha = int(24 + (i / glow_count) * 180 * (0.6 + 0.4 * pulse))
            s = pygame.Surface((rr*2, rr*2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*self.glow_color, alpha), (rr, rr), rr)
            pos = (int(self.center[0] - rr), int(self.center[1] - rr))
            win.blit(s, pos, special_flags=pygame.BLEND_ADD)

        core_radius = int(self.radius * self.scale)
        pygame.draw.circle(win, (14, 20, 28), self.center, core_radius + 8)
        pygame.draw.circle(win, self.color, self.center, core_radius)
        pygame.draw.circle(win, (6, 10, 14), self.center, int(core_radius*0.78), 3)
        pygame.draw.circle(win, NEON_CYAN, self.center, int(core_radius*0.78), 1)

        if self.textSurface:
            width = max(1, int(self.textSurface.get_width() * self.scale))
            height = max(1, int(self.textSurface.get_height() * self.scale))
            textSurface = pygame.transform.smoothscale(self.textSurface, (width, height))
            win.blit(textSurface, (self.center[0] - width/2, self.center[1] - height/2))


# ---------- AppButton (with rotating neon-blue ring) ----------
class AppButton(Widget):
    iconSize = 84

    def __init__(self, center, iconPath, appString, scale=1.0) -> None:
        super().__init__(center)
        self.icon_path = iconPath
        self.icon = pygame.image.load(iconPath).convert_alpha() if iconPath and os.path.exists(iconPath) else None
        self.base_icon_size = AppButton.iconSize
        self.original_image = self._make_icon_surface(self.base_icon_size)
        self.application = appString
        self.target_scale = scale
        self.current_scale = scale
        self.hovered = False
        self.hover_progress = 0.0  # 0.0 to 1.0, shows hover loader
        self.hover_start_time = None
        self.hover_threshold = 1.0  # seconds needed to activate hover click

        self.float_phase = random.random() * math.pi * 2
        self.float_amp = 6
        self.float_speed = 0.0012

        self.glow_color = NEON_CYAN_BRIGHT
        self.base_pulse_speed = 0.0024
        self.rotation_speed = 0.25  # rotation multiplier for neon ring
        self.last_hover_time = None

    def _make_icon_surface(self, size):
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        if self.icon:
            img = pygame.transform.smoothscale(self.icon, (size, size))
            surf.blit(img, (0, 0))
        else:
            font = pygame.font.Font(None, int(size*0.8))
            text = font.render("?", True, (220, 220, 220))
            surf.blit(text, ((size-text.get_width())/2, (size-text.get_height())/2))
        return surf

    def isOver(self, pos):
        if not super().isOver(pos):
            return False
        radius = (self.base_icon_size/2) * self.scale * 0.9
        return (pos[0] - self.center[0])**2 + (pos[1] - self.center[1])**2 <= radius*radius

    def update(self, cursor_pos):
        if cursor_pos and self.isOver(cursor_pos):
            self.hovered = True
            self.target_scale = 1.18
        else:
            self.hovered = False
            self.target_scale = 1.0
        self.current_scale += (self.target_scale - self.current_scale) * 0.14
    
    def update_hover(self, cursor_pos, delta_time):
        hovering = cursor_pos is not None and isinstance(cursor_pos, (list, tuple)) and self.isOver(cursor_pos)
        if hovering:
            self.hover_progress += delta_time / self.hover_threshold
            self.hover_progress = min(self.hover_progress, 1.0)
        else:
            self.hover_progress = 0.0
        self.target_scale = 1.18 if hovering else 1.0
        return self.hover_progress >= 1.0  # True when loader is full    
    def draw(self, win):
        super().draw(win)
        t = pygame.time.get_ticks()
        pulse = (math.sin(t * self.base_pulse_speed + self.float_phase) + 1) / 2.0
        hover_boost = 0.8 if self.hovered else 0.0
        total_pulse = pulse * (0.6 + hover_boost)
        float_offset = math.sin(t * self.float_speed + self.float_phase) * self.float_amp

        icon_draw_size = max(2, int(self.base_icon_size * self.scale * (1.0 + 0.06 * total_pulse) * self.current_scale))

        # ---------- Rotating Neon Ring ----------
        ring_radius = int(icon_draw_size * 0.8)
        outer_ring_radius = ring_radius + 20
        ring_surface = pygame.Surface((outer_ring_radius*2, outer_ring_radius*2), pygame.SRCALPHA)
        num_segments = 180
        rotation_angle = (t * self.rotation_speed) % 360

        for i in range(num_segments):
            angle = math.radians(i * 2 + rotation_angle)
            x = outer_ring_radius + math.cos(angle) * ring_radius
            y = outer_ring_radius + math.sin(angle) * ring_radius
            alpha = 180 if i % 3 == 0 else 70
            pygame.draw.circle(ring_surface, (*self.glow_color, alpha), (int(x), int(y)), 2)

        win.blit(ring_surface, (int(self.center[0] - outer_ring_radius), int(self.center[1] - outer_ring_radius + float_offset)), special_flags=pygame.BLEND_ADD)

        # icon itself
        icon_surf = pygame.transform.smoothscale(self.original_image, (icon_draw_size, icon_draw_size))
        win.blit(icon_surf, (int(self.center[0] - icon_draw_size / 2), int(self.center[1] - icon_draw_size / 2 + float_offset)))

        if self.hover_progress > 0:
            loader_radius = int(self.base_icon_size * self.scale * 0.9)
            loader_thickness = 5
            start_angle = -90
            end_angle = start_angle + int(360 * self.hover_progress)
            rect = pygame.Rect(self.center[0]-loader_radius-5, self.center[1]-loader_radius-5,
                            2*(loader_radius+5), 2*(loader_radius+5))
            pygame.draw.arc(win, NEON_CYAN_BRIGHT, rect, 
                            math.radians(start_angle), math.radians(end_angle), loader_thickness)


# ---------- Generic App (panel) ----------
class App(Widget):
    def __init__(self, center, width, height, bgCol=None, bgImagePath=None, bg=None) -> None:
        super().__init__(center)
        self.width = width
        self.height = height
        self.running = False
        self.bgCol = bgCol
        self.bgImage = None
        if bgImagePath and os.path.exists(bgImagePath):
            self.bgImage = pygame.image.load(bgImagePath).convert_alpha()
        elif bg:
            self.bgImage = pygame.image.load(bg).convert_alpha()

        # panel style
        self.corner_radius = 12

    def draw(self, win):
        if not self.moving and not self.running:
            return False

        width, height = int(self.width * self.scale), int(self.height * self.scale)
        x, y = int(self.center[0] - width / 2), int(self.center[1] - height / 2)

        # panel background
        panel = pygame.Surface((width, height), pygame.SRCALPHA)
        panel.fill((0,0,0,0))
        # rounded rectangle (approx)
        pygame.draw.rect(panel, (*CARD_BG, 230), (0, 0, width, height), border_radius=self.corner_radius)

        if self.bgImage:
            bg = pygame.transform.smoothscale(self.bgImage, (width, height))
            panel.blit(bg, (0,0))
        elif isinstance(self.bgCol, tuple):
            pygame.draw.rect(panel, (*self.bgCol, 210), (0,0,width,height), border_radius=self.corner_radius)

        # subtle inner vignette
        vignette = pygame.Surface((width, height), pygame.SRCALPHA)
        for i in range(20):
            alpha = int(12 * (i/20.0))
            pygame.draw.rect(vignette, (0,0,0,alpha), (i, i, width-2*i, height-2*i), border_radius=max(0, self.corner_radius - i))
        panel.blit(vignette, (0,0), special_flags=pygame.BLEND_RGBA_SUB)

        win.blit(panel, (x, y))
        super().draw(win)
        return True

    def isOver(self, pos):
        if not super().isOver(pos):
            return False
        if not self.running:
            return False
        width, height = self.width * self.scale, self.height * self.scale
        xLeft = self.center[0] - width / 2
        yTop = self.center[1] - height / 2
        return xLeft < pos[0] < xLeft + width and yTop < pos[1] < yTop + height

    @abstractmethod
    def start(self):
        if self.running:
            return False
        self.running = True
        return True

    @abstractmethod
    def stop(self):
        if not self.running:
            return False
        self.running = False
        return True


# ---------- Specific Apps (DateTime / Weather / Joke / Help / Music / Todo) ----------
class DateTimeWidget(App):
    def __init__(self, center, width, height, bgCol, bigFontSize, smallFontSize, speaker, bg=None):
        super().__init__(center, width, height, bgCol, bgImagePath=bg)
        self.bigFont = pygame.font.Font("Assets/Fonts/Roboto-Light.ttf", bigFontSize)
        self.smallFont = pygame.font.Font("Assets/Fonts/Roboto-Light.ttf", smallFontSize)
        self.speaker = speaker

    def draw(self, win):
        canDraw = super().draw(win)
        if not canDraw:
            return
        width, height = int(self.width * self.scale), int(self.height * self.scale)
        cx, cy = int(self.center[0]), int(self.center[1])
        day, date, time = dayDateTime()
        timeText = self.bigFont.render(time, True, TEXT_WHITE)
        dateText = self.smallFont.render(f"{date} - {day}", True, TEXT_WHITE)

        # center aligned
        win.blit(timeText, (cx - timeText.get_width()//2, cy - timeText.get_height()))
        win.blit(dateText, (cx - dateText.get_width()//2, cy + 8))

    def start(self, spawnPos, spawnScale, targetPos, targetScale, speed):
        if not super().start():
            return
        self.center = tuple(spawnPos)
        self.scale = spawnScale
        self.setTarget(targetPos, targetScale, speed)
        day, date, time = dayDateTime()
        self.speaker.speak(f"Today is {day}, {date}, and the current time is {time}.")

    def stop(self, despawnPos, despawnScale, speed):
        self.setTarget(despawnPos, despawnScale, speed)
        super().stop()


class WeatherWidget(App):
    def __init__(self, center, width, height, bgCol, bigFontSize, smallFontSize, speaker, weatherDescTempHumidity, bg=None):
        super().__init__(center, width, height, bgCol, bgImagePath=bg)
        self.bigFont = pygame.font.Font("Assets/Fonts/Roboto-Light.ttf", bigFontSize)
        self.smallFont = pygame.font.Font("Assets/Fonts/Roboto-Light.ttf", smallFontSize)
        self.speaker = speaker
        self.weatherDescTempHumidity = weatherDescTempHumidity

    def draw(self, win):
        canDraw = super().draw(win)
        if not canDraw:
            return
        cx, cy = int(self.center[0]), int(self.center[1])
        desc, temp, humidity = self.weatherDescTempHumidity
        statsText = self.bigFont.render(f"{temp}°C   {humidity}%", True, TEXT_WHITE)
        descText = self.smallFont.render(desc, True, TEXT_WHITE)

        win.blit(statsText, (cx - statsText.get_width()//2, cy - statsText.get_height()))
        win.blit(descText, (cx - descText.get_width()//2, cy + 6))

    def start(self, spawnPos, spawnScale, targetPos, targetScale, speed):
        if not super().start():
            return
        self.center = tuple(spawnPos)
        self.scale = spawnScale
        self.setTarget(targetPos, targetScale, speed)

        desc, temp, humidity = self.weatherDescTempHumidity
        # NOTE: define 'city' in your outer scope, or change the speak line below
        try:
            weatherText = f"The weather in {city} is currently {desc}. The temperature is {temp} degrees Celsius, and the humidity is at {humidity} percent."
        except NameError:
            weatherText = f"The weather is currently {desc}, temperature {temp}°C and humidity {humidity}%."
        self.speaker.speak(weatherText)

    def stop(self, despawnPos, despawnScale, speed):
        self.setTarget(despawnPos, despawnScale, speed)
        super().stop()


class JokeWidget(App):
    def __init__(self, center, width, height, bgCol, fontSize, speaker, bg=None):
        super().__init__(center, width, height, bgCol, bgImagePath=bg)
        self.font = pygame.font.Font("Assets/Fonts/Roboto-Light.ttf", fontSize)
        self.speaker = speaker
        self.jokeText = ""

    def draw(self, win):
        canDraw = super().draw(win)
        if not canDraw:
            return
        cx, cy = int(self.center[0]), int(self.center[1])
        lines = self._wrap_text(self.jokeText, self.font, int(self.width * 0.9))
        y = cy - (len(lines) * self.font.get_linesize())//2
        for line in lines:
            text = self.font.render(line, True, TEXT_WHITE)
            win.blit(text, (cx - text.get_width()//2, y))
            y += self.font.get_linesize()

    def _wrap_text(self, text, font, maxw):
        words = text.split()
        lines = []
        cur = ""
        for w in words:
            test = (cur + " " + w).strip()
            if font.size(test)[0] > maxw and cur:
                lines.append(cur)
                cur = w
            else:
                cur = test
        if cur:
            lines.append(cur)
        return lines

    def start(self, spawnPos, spawnScale, targetPos, targetScale, speed):
        if not super().start():
            return
        self.center = tuple(spawnPos)
        self.scale = spawnScale
        self.setTarget(targetPos, targetScale, speed)
        setup, payoff = getJoke()
        self.jokeText = f"{setup} {payoff}"
        self.speaker.speak(self.jokeText)

    def stop(self, despawnPos, despawnScale, speed):
        self.setTarget(despawnPos, despawnScale, speed)
        super().stop()


class HelpWidget(App):
    def __init__(self, center, width, height, bgCol, fontSize, speaker, bg=None):
        super().__init__(center, width, height, bgCol, bgImagePath=bg)
        self.font = pygame.font.Font("Assets/Fonts/Roboto-Light.ttf", fontSize)
        self.speaker = speaker

    def draw(self, win):
        canDraw = super().draw(win)
        if not canDraw:
            return
        cx, cy = int(self.center[0]), int(self.center[1])
        lines = [
            "1. Use hand to control cursor",
            "2. Hover an icon to select",
            "3. Click central J.A.R.V.I.S. to speak"
        ]
        y = cy - (len(lines) * self.font.get_linesize())//2
        for line in lines:
            text = self.font.render(line, True, TEXT_WHITE)
            win.blit(text, (cx - text.get_width()//2, y))
            y += self.font.get_linesize()

    def start(self, spawnPos, spawnScale, targetPos, targetScale, speed):
        if not super().start():
            return
        self.center = tuple(spawnPos)
        self.scale = spawnScale
        self.setTarget(targetPos, targetScale, speed)
        helpText = "Move your hand around to control the cursor. Hover over any button to click on it. If you click the Jarvis button, you can issue voice commands."
        self.speaker.speak(helpText)

    def stop(self, despawnPos, despawnScale, speed):
        self.setTarget(despawnPos, despawnScale, speed)
        super().stop()


class MusicWidget(App):
    def __init__(self, center, width, height, bgCol, fontSize, bg=None):
        super().__init__(center, width, height, bgCol, bgImagePath=bg)
        self.font = pygame.font.Font("Assets/Fonts/Roboto-Light.ttf", fontSize)
        self.songName = None

    def draw(self, win):
        canDraw = super().draw(win)
        if not canDraw:
            return
        cx, cy = int(self.center[0]), int(self.center[1])
        nameText = self.font.render(self.songName or "No song playing", True, TEXT_WHITE)
        win.blit(nameText, (cx - nameText.get_width()//2, cy - nameText.get_height()//2))

    def start(self, spawnPos, spawnScale, targetPos, targetScale, speed):
        if not super().start():
            return
        self.center = tuple(spawnPos)
        self.scale = spawnScale
        self.setTarget(targetPos, targetScale, speed)
        self.songName, song_path = getSong()
        if song_path and os.path.exists(song_path):
            mixer.music.load(song_path)
            mixer.music.play(-1)

    def stop(self, despawnPos, despawnScale, speed):
        self.setTarget(despawnPos, despawnScale, speed)
        mixer.music.stop()
        super().stop()


class TodoListWidget(App):
    def __init__(self, center, width, height, bgCol, fgCol, fontSize, blocksize, offset, todolist, speaker, bg=None):
        super().__init__(center, width, height, bgCol, bgImagePath=bg)
        self.fgCol = fgCol
        self.font = pygame.font.Font("Assets/Fonts/Roboto-Light.ttf", fontSize)
        self.blockSize = blocksize
        self.offset = offset
        self.todolist = list(todolist)
        self.speaker = speaker

    def draw(self, win):
    # Call parent draw (handles moving/visibility)
        canDraw = super().draw(win)
        if not canDraw:
            return

    # Calculate scaled dimensions
        width = int(self.width * self.scale)
        height = int(self.height * self.scale)
        x = int(self.center[0] - width / 2)
        y = int(self.center[1] - height / 2)

    # Scaled block size and offset
        blockSize = max(1, int(self.blockSize * self.scale))
        offset = max(1, int(self.offset * self.scale))

    # Determine maximum number of visible tasks
        max_visible = height // (blockSize + offset)
        if max_visible <= 0:
            return  # nothing to draw yet

    # Draw each visible task
        for i, task in enumerate(self.todolist[:max_visible]):
            bx = x + 8
            by = y + i * (blockSize + offset) + 8
            bw = width - 16
            bh = blockSize
            rect = pygame.Rect(bx, by, bw, bh)
            pygame.draw.rect(win, self.fgCol, rect, border_radius=8)
            taskText = self.font.render(task, True, TEXT_WHITE)
            win.blit(taskText, (bx + 12, by + bh//2 - taskText.get_height()//2))
    def getIndex(self, pos):
        width, height = self.width * self.scale, self.height * self.scale
        xLeft = self.center[0] - width / 2
        yTop = self.center[1] - height / 2
        blockSize, offset = self.blockSize * self.scale, self.offset * self.scale
        for i in range(len(self.todolist)):
            top = yTop + i * (blockSize + offset)
            if top < pos[1] < top + blockSize and xLeft < pos[0] < xLeft + width:
                return i

    def start(self, spawnPos, spawnScale, targetPos, targetScale, speed):
        if not super().start():
            return
        self.center = tuple(spawnPos)
        self.scale = spawnScale
        self.setTarget(targetPos, targetScale, speed)
        self.speaker.speak("Opening to-do list")

    def stop(self, despawnPos, despawnScale, speed):
        self.setTarget(despawnPos, despawnScale, speed)
        super().stop()
