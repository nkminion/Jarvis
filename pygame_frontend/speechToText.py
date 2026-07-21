# Modified from example code at 'https://github.com/alphacep/vosk-api/blob/master/python/example/test_microphone.py'

import queue
import sys
import sounddevice as sd

from vosk import Model, KaldiRecognizer
import numpy as np

class SpeechToTextConverter:
    def __init__(self, model_path) -> None:
        self.model = Model(model_path=model_path)
        self.q = queue.Queue()

        device_info = sd.query_devices(None, "input")
        # soundfile expects an int, sounddevice provides a float:
        self.samplerate = int(device_info["default_samplerate"])
        self.amplitude = 0
        self.rec = KaldiRecognizer(self.model, self.samplerate)

        self.stream = sd.RawInputStream(
            samplerate=self.samplerate,
            blocksize=8000,
            device=None,
            dtype="int16",
            channels=1,
            callback=self.callback,
        )
        self.transcribing = False
        self.open = True

    def callback(self, indata, frames, time, status):
        """This is called (from a separate thread) for each audio block."""
        if status:
            print(status, file=sys.stderr)
        
        audio_data = np.frombuffer(indata, dtype=np.int16)
        self.amplitude = np.mean(np.absolute(audio_data))
        self.q.put(bytes(indata))

    def startConverter(self):
        if self.open and not self.transcribing:
            self.stream.start()
            self.transcribing = True

    def stopConverter(self):
        if self.open and self.transcribing:
            self.stream.stop()
            self.transcribing = False

    def closeConverter(self):
        if self.open:
            if self.transcribing:
                self.stream.stop()
                self.transcribing = False
            self.stream.close()
            self.open = False

    def getText(self):
        if self.open and self.transcribing:
            data = self.q.get()
            if self.rec.AcceptWaveform(data):
                text = self.rec.Result()
                if text[0] == '{':
                    return text[14:-3]
