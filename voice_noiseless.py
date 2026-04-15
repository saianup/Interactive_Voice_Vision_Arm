import pvporcupine
import pyaudio
import struct
import whisper
import numpy as np
import wave
import time
import sounddevice as sd
from scipy.io.wavfile import write
import librosa


ACCESS_KEY = "+uRmK/oWc310TNIvmoNWsof5rGMjOGoCzzlIy6s41HTaURazFetErQ=="
WAKE_WORD_PATH = r"C:\Users\dvsai\OneDrive - Anna University\Desktop\Mini_Proj\Jarvis_en_windows_v4_0_0.ppn"

SAMPLE_RATE = 16000
RECORD_SECONDS = 4

SILENCE_THRESHOLD = 0.01   # energy threshold
MIN_TEXT_LENGTH = 3        # ignore tiny outputs

print("Loading Whisper model...")
model = whisper.load_model("small")

porcupine = pvporcupine.create(
    access_key=ACCESS_KEY,
    keyword_paths=[WAKE_WORD_PATH]
)

pa = pyaudio.PyAudio()

audio_stream = pa.open(
    rate=porcupine.sample_rate,
    channels=1,
    format=pyaudio.paInt16,
    input=True,
    frames_per_buffer=porcupine.frame_length
)

print("Jarvis listening for wake word...")

def record_audio():

    print("Listening for command...")

    recording = sd.rec(
        int(RECORD_SECONDS * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=1
    )

    sd.wait()

    write("command.wav", SAMPLE_RATE, recording)

def transcribe():

    print("Transcribing...")

    # Load audio
    y, sr = librosa.load("command.wav", sr=None)

    # Compute energy to detect silence
    energy = np.mean(np.abs(y))

    if energy < SILENCE_THRESHOLD:
        print("Silence detected. Ignoring command.")
        return ""

    result = model.transcribe(
        "command.wav",
        fp16=False
    )

    text = result["text"].lower().strip()

    # Remove wake word if Whisper hears it again
    text = text.replace("jarvis", "").strip()

    # Ignore tiny garbage outputs
    if len(text) < MIN_TEXT_LENGTH:
        print("Low confidence speech. Ignoring.")
        return ""

    print("You said:", text)

    return text

while True:

    pcm = audio_stream.read(porcupine.frame_length)
    pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)

    keyword_index = porcupine.process(pcm)

    if keyword_index >= 0:

        print("\nWake word detected: Jarvis")

        time.sleep(0.3)

        record_audio()

        text = transcribe()

        if text == "":
            print("No valid command detected")
        else:
            print("Command captured:", text)

        print("----------------------------------")