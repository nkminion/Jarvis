import speech_recognition as sr
import time

# Initialize recognizer
r = sr.Recognizer()

def recognize_speech():
    with sr.Microphone() as source:
        print("🎤 Listening...")
        r.adjust_for_ambient_noise(source, duration=0.5)  # optional: reduce background noise
        audio = r.listen(source, timeout=5, phrase_time_limit=10)  # listen up to 10 seconds

    try:
        # Recognize speech using Google Web Speech API (online, accurate)
        text = r.recognize_google(audio)
        print("🗣 You said:", text)
    except sr.UnknownValueError:
        print("❌ Could not understand audio")
    except sr.RequestError as e:
        print("⚠️ Request failed; check your internet connection:", e)

# Example loop: run once every 15 seconds
while True:
    i = input()
    recognize_speech()
    print("⏳ Waiting 15 seconds before next recognition...")
