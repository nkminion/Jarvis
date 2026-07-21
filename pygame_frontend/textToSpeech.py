import asyncio
import edge_tts
import sounddevice as sd
import soundfile as sf
import os

VOICE = "en-US-GuyNeural"

async def generate(text):
    communicate = edge_tts.Communicate(text, VOICE)
    await communicate.save("tts.mp3")

def speak(text):
    asyncio.run(generate(text))
    data, fs = sf.read("tts.mp3")
    sd.play(data, fs)
    sd.wait()
    os.remove("tts.mp3")

# speak("Hello! This is Edge TTS.")