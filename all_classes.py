import pyrealsense2 as rs
import numpy as np
import cv2
from ultralytics import YOLO
import threading
import time
import math
import serial
import subprocess

import pvporcupine
import pyaudio
import struct
import whisper
import sounddevice as sd
from scipy.io.wavfile import write
import librosa

# ==============================
# DEBUG PRINT
# ==============================
def log(tag, msg):
    print(f"[{tag}] {msg}")

# ==============================
# TTS
# ==============================
def speak(text):
    text = text.replace("'", "")
    log("SPEAK", text)
    cmd = f'''PowerShell -Command "Add-Type –AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak('{text}')"'''
    subprocess.Popen(cmd, shell=True)

# ==============================
# SERIAL
# ==============================
ser = serial.Serial("COM13", 115200, timeout=1)
time.sleep(2)

# ==============================
# GLOBAL DETECTION STORAGE
# ==============================
detected_objects = {}
lock = threading.Lock()

# ==============================
# ARM CONTROL (UNCHANGED)
# ==============================
def send_to_arm(theta1, theta2, theta3):

    theta1 = int(max(0, min(180, theta1)))
    theta2 = int(max(0, min(180, theta2)))
    theta3 = int(max(0, min(180, theta3)))

    # Current assumption (starting from 0 or last position)
    # You can improve later with feedback

    def move_joint(joint, angle, prev_angle):

        diff = abs(angle - prev_angle)

        # Estimate time (VERY IMPORTANT)
        # Arduino delay = 35 ms per degree
        # So time ≈ diff * 0.035 sec
        move_time = diff * 0.04   # slightly higher for safety

        cmd = f"{joint} {angle}\n"
        ser.write(cmd.encode())

        print(f"[ARM] Moving J{joint} → {angle} (Δ={diff})")

        time.sleep(move_time + 0.5 + 2)  # buffer

        return angle

    # Track last angles (start with 0,0,180 home assumption)
    global last_angles

    if 'last_angles' not in globals():
        last_angles = [0, 0, 180]

    # ORDER: 1 → 3 → 2
    last_angles[0] = move_joint(1, theta1, last_angles[0])
    last_angles[2] = move_joint(3, theta3, last_angles[2])
    last_angles[1] = move_joint(2, theta2, last_angles[1])

    # Gripper close (no need long wait)
    ser.write(b"4 90\n")
    print("[ARM] Gripper CLOSE")
    time.sleep(1)

def go_home():

    global last_angles

    home = [0, 0, 150]

    def move_joint(joint, angle, prev_angle):
        diff = abs(angle - prev_angle)
        move_time = diff * 0.04

        ser.write(f"{joint} {angle}\n".encode())
        print(f"[ARM] HOME J{joint} → {angle}")

        time.sleep(move_time + 0.5)

        return angle
    
    last_angles[1] = move_joint(2, home[1], last_angles[1])
    last_angles[0] = move_joint(1, home[0], last_angles[0])
    last_angles[2] = move_joint(3, home[2], last_angles[2])
    ser.write(b"4 0\n")

# ==============================
# VISION THREAD (UNCHANGED)
# ==============================
def vision_thread():

    model = YOLO(r"C:\Users\dvsai\OneDrive - Anna University\Desktop\VLA_model\full_model\best.pt")

    pipeline = rs.pipeline()
    config = rs.config()

    config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
    config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)

    profile = pipeline.start(config)
    align = rs.align(rs.stream.color)

    intr = profile.get_stream(rs.stream.color)\
        .as_video_stream_profile().get_intrinsics()

    tx, ty, tz = -0.10, 0.2, 0.185
    t = np.array([tx, ty, tz])

    pitch, roll = np.radians(19), np.radians(4)

    R_pitch = np.array([
        [np.cos(pitch), 0, np.sin(pitch)],
        [0, 1, 0],
        [-np.sin(pitch), 0, np.cos(pitch)]
    ])

    R_roll = np.array([
        [1, 0, 0],
        [0, np.cos(roll), -np.sin(roll)],
        [0, np.sin(roll), np.cos(roll)]
    ])

    R_total = R_roll @ R_pitch

    while True:

        frames = pipeline.wait_for_frames()
        frames = align.process(frames)

        color_frame = frames.get_color_frame()
        depth_frame = frames.get_depth_frame()

        if not color_frame or not depth_frame:
            continue

        frame = np.asanyarray(color_frame.get_data())
        results = model(frame, conf=0.5, verbose=False)

        local_objects = {}

        for box in results[0].boxes:

            cls_id = int(box.cls[0])
            label_name = model.names[cls_id]

            # ignore garbage class
            if "box-tape-stapler-bottle-cube" in label_name:
                continue

            cx = int((box.xyxy[0][0] + box.xyxy[0][2]) / 2)
            cy = int((box.xyxy[0][1] + box.xyxy[0][3]) / 2)

            depth = depth_frame.get_distance(cx, cy)
            point = rs.rs2_deproject_pixel_to_point(intr, [cx, cy], depth)

            X = point[2]
            Y = -point[0]
            Z = -point[1]

            P_base = R_total @ np.array([X, Y, Z]) + t
            local_objects[label_name] = P_base

        with lock:
            detected_objects.clear()
            detected_objects.update(local_objects)

# ==============================
# IK (UNCHANGED)
# ==============================
def compute_ik(x,y,z):

    r = 0.185
    dx = x
    dy = y + 0.185
    d = math.sqrt(dx**2 + dy**2)

    k = (r**2)/(d**2)
    m = (r*math.sqrt(d**2-r**2))/(d**2)

    T1x = k*dx - m*dy
    T1y = -0.185 + (k*dy + m*dx)

    theta1 = abs(math.degrees(math.atan2(T1x,(T1y+0.185))))

    l1,l2 = 0.485,0.55
    n = math.sqrt(d**2-r**2)

    theta3 = ((l1**2+l2**2-n**2-z**2)/(2*l1*l2))
    theta3 = 180 - math.degrees(math.acos(theta3))

    m2 = math.sqrt(n**2+z**2)
    phi = math.atan2(z,n)
    alpha = math.acos((l1**2+m2**2-l2**2)/(2*l1*m2))

    theta2 = 90 - math.degrees(phi+alpha)

    return theta1,theta2,theta3

# ==============================
# VOICE SETUP
# ==============================
ACCESS_KEY = "+uRmK/oWc310TNIvmoNWsof5rGMjOGoCzzlIy6s41HTaURazFetErQ=="
WAKE_WORD_PATH = r"C:\Users\dvsai\OneDrive - Anna University\Desktop\Mini_Proj\Jarvis_en_windows_v4_0_0.ppn"

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

model_whisper = whisper.load_model("small")

# ==============================
# AUDIO
# ==============================
def record_audio():
    log("STATE", "Recording...")
    duration = 2.5
    recording = sd.rec(int(16000 * duration), samplerate=16000, channels=1)
    sd.wait()
    write("cmd.wav",16000,recording)

def transcribe():

    log("STATE", "Transcribing...")

    y,_ = librosa.load("cmd.wav", sr=16000)

    if np.mean(np.abs(y)) < 0.01:
        log("VOICE", "Silence detected")
        return ""

    result = model_whisper.transcribe(
        "cmd.wav",
        fp16=False,
        language="en"
    )

    text = result["text"].lower().strip()
    text = text.replace("jarvis","").strip()

    log("TEXT", text)
    return text

# ==============================
# COMMAND HANDLER (DYNAMIC)
# ==============================
def handle_command(text):

    with lock:
        objs = dict(detected_objects)

    log("VISION", f"Available: {list(objs.keys())}")

    if len(objs) == 0:
        speak("No objects detected")
        return

    target_class = None

    for obj in objs.keys():
        if obj in text or obj.split("-")[0] in text:
            target_class = obj
            break

    if target_class is None:
        speak("Object not found")
        return

    x,y,z = objs[target_class]

    if "where" in text:
        speak(f"{target_class} is at {x:.2f}, {y:.2f}, {z:.2f}")
        return

    if "pick" in text or "grab" in text:

        speak(f"Picking {target_class}")

        theta1,theta2,theta3 = compute_ik(x,y,z)

        send_to_arm(theta1, theta2, theta3)

        time.sleep(2)

        speak("Returning home")
        go_home()

# ==============================
# VOICE LOOP
# ==============================
def voice_loop():

    log("STATE", "Listening for wake word...")

    while True:

        pcm = audio_stream.read(porcupine.frame_length, exception_on_overflow=False)
        pcm = struct.unpack_from("h"*porcupine.frame_length, pcm)

        if porcupine.process(pcm) >= 0:

            log("WAKE", "Detected")
            speak("Yes")

            time.sleep(0.3)

            record_audio()
            text = transcribe()

            if text:
                handle_command(text)

# ==============================
# START
# ==============================
threading.Thread(target=vision_thread, daemon=True).start()
voice_loop()