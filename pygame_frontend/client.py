import requests
from clientFunctionalities import play_song
from textToSpeech import speak
import speech_recognition as sr

# Replace this with your friend's IP address
SERVER_IP = "127.0.0.1"
URL = f"http://{SERVER_IP}:8000/process"

# Initialize recognizer
r = sr.Recognizer()

def recognize_speech():
    """Listen to the microphone and return recognized text."""
    with sr.Microphone() as source:
        print("\n🎤 Listening...")
        r.adjust_for_ambient_noise(source, duration=0.5)
        try:
            audio = r.listen(source, timeout=5, phrase_time_limit=10)
        except sr.WaitTimeoutError:
            print("⌛ No speech detected, try again.")
            return None

    try:
        text = r.recognize_google(audio)
        print("🗣 You said:", text)
        return text
    except sr.UnknownValueError:
        print("❌ Could not understand audio.")
    except sr.RequestError as e:
        print("⚠️ Speech recognition request failed:", e)
    return None


def performTask(intent, params):
    if intent == 'play_song':
        song = params['song']
        artist = params['artist']
        play_song(song, artist)
    elif intent == 'tell_joke':
        speak(params['joke'])
    elif intent == 'get_weather':
        speak(params['forecast'])
    elif intent == 'calculate':
        speak(params['response'])
    elif intent == 'club_info':
        speak(params['info'])
    elif intent == 'general_question':
        speak(params['answer'])
        print(params['sources'])


# --- Main Loop ---
def do_jarvis():
    text = recognize_speech()
    if not text:
        print("SR failed")
        return

    if text.lower() in ["exit", "quit", "stop"]:
        print("👋 Exiting.")
        return

    try:
        # Send POST request to FastAPI server
        response = requests.post(URL, json={"text": text})

        if response.status_code == 200:
            data = response.json()
            print("\n--- Response from Server ---")
            print(f"Intent: {data['intent']}")
            print(f"Score: {data['score']}")
            print(f"Params: {data['params']}\n")

            performTask(data['intent'], data['params'])
        else:
            print("❌ Error:", response.status_code, response.text)
    except Exception as e:
        print("⚠️", e)
