from utils import *
import pygame
from ui_components import *
from math import sin, cos, radians
from speech import Speaker, Listener
from hand_cursor import HandCursor
from vision import detect_gesture, move_mouse
import time
# weatherDescTempHumidity = getWe   atherDescTempHumidity(city, api_key)
weatherDescTempHumidity = ("light rain", 28, 66)
from client import do_jarvis

pygame.init()

winW, winH = 1280, 720
win = pygame.display.set_mode((winW, winH))

background = VideoBackground("Assets/Animations/video.mp4", winW, winH)

icon = pygame.image.load("Assets\Images\jarvisIcon.png")
pygame.display.set_icon(icon)
pygame.display.set_caption("J.A.R.V.I.S")   

speaker = Speaker()
listener = Listener()


handCursor = HandCursor(10, (255,255,255), winW, winH, 0.7)
selectedWidget = None
clickTime = timeLeftForClick = 1
prevTime = None
font = pygame.font.Font("Assets\Fonts\Roboto-Light.ttf", 24)


offsetX = -15    # +ve moves right, -ve moves left
offsetY = -30    # +ve moves down, -ve moves up
appsRadius = 250  # distance of icons from center

centerX, centerY = winW // 2 + offsetX, winH // 2 + offsetY

jarvisText = pygame.font.Font("Assets/Fonts/Roboto-BoldItalic.ttf", 64).render(
    "J.A.R.V.I.S", True, (255, 255, 255)
)

jarVis = JarVis((centerX, centerY), winH / 6, jarvisText, (0, 150, 150), (0, 150, 0))

sin60 = sin(radians(60))

appButtons = [
    AppButton((centerX + appsRadius, centerY), "Assets/Images/AppIconsnew/Clock.jpeg", "time_and_date"),
    AppButton((centerX + appsRadius / 2, centerY + appsRadius * sin60), "Assets/Images/AppIconsnew/Weather.png", "weather"),
    AppButton((centerX - appsRadius / 2, centerY + appsRadius * sin60), "Assets/Images/AppIconsnew/TodoList.jpeg", "show_todo"),
    AppButton((centerX - appsRadius, centerY), "Assets/Images/AppIcons/question.png", "help"),
    AppButton((centerX - appsRadius / 2, centerY - appsRadius * sin60), "Assets/Images/AppIconsnew/Jokes.jpeg", "joke"),
    AppButton((centerX + appsRadius / 2, centerY - appsRadius * sin60), "Assets/Images/AppIconsnew/Music.jpeg", "music"),
]



# Apps

apps = {
    "time_and_date": DateTimeWidget(
        (winW / 2, winH / 2), winW / 3, winH / 3, (50, 50, 50), 64, 32, speaker,bg="Assets\Images\BackgroundImages\Time.jpg"
    ),
    "weather": WeatherWidget(
        (winW / 2, winH / 2),
        winW / 3,
        winH / 3,
        (50, 50, 50),
        64,
        32,
        speaker,
        weatherDescTempHumidity,
        bg="Assets/Images/BackgroundImages/Weather.jpg"
    ),
    "joke": JokeWidget(
        (winW / 2, winH / 2), winW / 1.5, winH / 3, (50, 50, 50), 24, speaker,bg="Assets\Images\BackgroundImages\Jokes.jpg"
    ),
    "help": HelpWidget(
        (winW / 2, winH / 2), winW / 3, winH / 3, (50, 50, 50), 40, speaker,bg="Assets\Images\BackgroundImages\Jarvis_Interface_Guide_Background.jpg"
    ),
    "music": MusicWidget((winW / 2, winH / 2), winW / 3, winH / 3, (50, 50, 50), 40,bg="Assets\Images\BackgroundImages\Music.jpg"),
    "show_todo": TodoListWidget(
        (winW / 2, winH / 2),
        winW / 3,
        winH / 3,
        (50, 50, 50),
        (100, 100, 100),
        24,
        40,
        5,
        todoList,
        speaker,
        bg="Assets\Images\BackgroundImages\Todolist.jpg"
    ),
}

widgetSpeed = 100

def get_clicked_button(cursor_pos, delta_time):
    clicked = None
    for btn in [jarVis] + appButtons:
        if hasattr(btn, 'update_hover'):
            if btn.update_hover(cursor_pos, delta_time):
                clicked = btn
        elif btn.isOver(cursor_pos):
            clicked = btn
    return clicked
def hover_click(hand_pos, buttons, delta_time):
    hovered_button = None
    for btn in buttons:
        if hasattr(btn, 'update_hover'):
            btn.update_hover(hand_pos, delta_time)  # fix param order
        if btn.isOver(hand_pos):
            hovered_button = btn
    return hovered_button
def expandIcons():
    jarVis.setTarget((winW / 2, winH / 2), 1, widgetSpeed)
    for i, button in enumerate(appButtons):
        button.setTarget(
            (
                winW / 2 + appsRadius * cos(radians(60 * i)),
                winH / 2 + appsRadius * sin(radians(60 * i)),
            ),
            1,
            widgetSpeed,
        )


def condenseIcons():
    jarVis.setTarget((winH / 10, winH / 10), 0.4, widgetSpeed)
    for i, button in enumerate(appButtons):
        button.setTarget(((winH / 10), winH / 10 + 100 * (i + 1)), 0.6, widgetSpeed)


handCursor.enable()
running = True

activeApp = None
todoTaskHeard = False
listenText = ""

while running:
    offsetX = -15    # +ve moves right, -ve moves left
    offsetY = -30    # +ve moves down, -ve moves up
    appsRadius = 250  # distance of icons from center

    centerX, centerY = winW // 2 + offsetX, winH // 2 + offsetY

    jarvisText = pygame.font.Font("Assets/Fonts/Roboto-BoldItalic.ttf", 64).render(
    "J.A.R.V.I.S", True, (255, 255, 255)
)
    current_time = time.time()
    if prevTime is None:
        prevTime = current_time
    delta_time = current_time - prevTime
    prevTime = current_time
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    handCursor.updatePos(showImage=False)  # updates handCursor.position
    gesture = None
    if hasattr(handCursor, "landmark_list") and handCursor.landmark_list:
        gesture = detect_gesture(handCursor.landmark_list)  # detect gestures
        if handCursor.index_finger_tip:
        # Update pygame cursor position directly
            x = int(handCursor.index_finger_tip.x * winW)
            y = int(handCursor.index_finger_tip.y * winH)
            handCursor.position = (x, y)



    if activeApp in apps and apps[activeApp].running:
        appWidget = apps[activeApp]
        if getattr(appWidget, 'bgImage', None):
            bg_scaled = pygame.transform.scale(appWidget.bgImage, (winW, winH))
            win.blit(bg_scaled, (0, 0))
        elif getattr(appWidget, 'bg', None):
            bg_scaled = pygame.image.load(appWidget.bg)
            bg_scaled = pygame.transform.scale(bg_scaled, (winW, winH))
            win.blit(bg_scaled, (0, 0))
        elif isinstance(appWidget.bgCol, tuple):
            win.fill(appWidget.bgCol)

    else:
        background.draw(win)

    current_pos = tuple(handCursor.position) if handCursor.position else (-100, -100)
    clicked_button = get_clicked_button(current_pos, delta_time)
    # --- Handle clicks ---
    if clicked_button:
        if clicked_button == jarVis:
            # if activeApp in apps:
            #     apps[activeApp].stop((winW, winH), 0, widgetSpeed)
            # activeApp = "jarVis"
            # jarVis.color = jarVis.listenCol
            # listener.listen()
            # expandIcons()
            print("DO JARVIS")
            do_jarvis()
        else:
            if clicked_button.application != activeApp:
                if activeApp in apps:
                    apps[activeApp].stop((winW, winH), 0, widgetSpeed)
                activeApp = clicked_button.application
                condenseIcons()
                apps[activeApp].start((winW,0),0,(winW/2, winH/2),1,widgetSpeed)
    
    if activeApp == "jarVis" and listener.listening == False:  # Listening is complete
        print(listener.text)
        response, responseType = categorize(listener.text)
        print(response, responseType)
        jarVis.color = jarVis.defaultCol
        listenText = listener.text
        if responseType == speechResponseType:
            activeApp = None
            speaker.speak(response)
        elif responseType == actionResponseType:
            activeApp = response
            if activeApp in apps:
                appWidget = apps[activeApp]
                condenseIcons()
                appWidget.start((winW, 0), 0, (winW / 2, winH / 2), 1, widgetSpeed)
            else:
                if activeApp == "clear_todo":
                    todoList.clear()
                    speaker.speak("Cleared the todo list")
                elif activeApp == "add_todo":
                    speaker.speak("What would you like to add to your to do list?")
                else:
                    activeApp = None
        elif responseType == searchResponseType:
            activeApp = None
            speaker.speak("Opening your query...")
            open_website(response)
        else:
            speaker.speak(response)
            activeApp = None

    if (
        activeApp == "add_todo"
    ):  # Add todo requires an extra listen - thus pauses other app activations
        if not todoTaskHeard:
            if not speaker.speaking and not listener.listening:
                jarVis.color = jarVis.listenCol
                listener.listen()
                todoTaskHeard = True
        else:
            if not listener.listening:
                jarVis.color = jarVis.defaultCol
                print(listener.text)
                listenText = listener.text
                todoList.append(listener.text)
                todoTaskHeard = False
                activeApp = None
                speaker.speak("Added task to todo list")
    # Rendering
    jarVis.draw(win)
    for button in appButtons:
        button.draw(win)
    for appWidget in apps.values():
        appWidget.draw(win)
    if listenText:
        textSurf = font.render("You said: " + listenText, True, (255, 255, 255))
        win.blit(textSurf, (winW / 2 - textSurf.get_width(), winH - 40))
    handCursor.draw(win)

    pygame.display.update()

handCursor.disable()
pygame.quit()
