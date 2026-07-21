import speech_recognition as sr
import pyttsx3
import threading
import sounddevice as sd

class Listener:
    def __init__(self) -> None:
        self.listening = False
        self.text = ""

    def _listen_in_thread(self):
        rec = sr.Recognizer()
        try:
            with sr.Microphone(device_index=1) as src:
                rec.adjust_for_ambient_noise(src, 0.2)
                print("Listening...")
                audio = rec.listen(src)
                self.text = rec.recognize_vosk(audio)[14:-3]
        except Exception as e:
            print(e)
            self.text = "Error"
        self.listening = False

    def listen(self):
        if self.listening:
            print("Listener is already listening")
            return

        self.listening = True
        thread = threading.Thread(target=self._listen_in_thread)
        thread.start()


class Speaker:
    def __init__(self) -> None:
        self.speaking = False

    def _speak_in_thread(self, text):
        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()
        self.speaking = False

    def speak(self, text):
        if self.speaking:
            print("Speaker is already speaking")
            return

        self.speaking = True
        thread = threading.Thread(target=self._speak_in_thread, args=(text,))
        thread.start()


print(sd.query_devices())