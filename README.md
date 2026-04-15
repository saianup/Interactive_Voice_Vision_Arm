#  Voice + Vision Controlled Robotic Arm System



##  Project Overview

This project combines **computer vision, voice recognition, and robotic arm control** to create a system where a user can give voice commands (like “pick bottle”), and the robotic arm will detect the object, compute its position, and pick it.



##  Files Description

* `all_classes.py`
  → Main integrated code (Vision + Voice + IK + Arduino control)

* `ike_ang_sol.py`
  → Standalone inverse kinematics solver

* `object_det.py`
  → Object detection + 3D coordinate extraction using RealSense

* `voice_noiseless.py`
  → Wake word detection + speech-to-text

* `motor_fin.ino`
  → Arduino code for controlling servos of robotic arm



##  System Requirements

### Hardware Required

* Intel RealSense Camera
* ESP / Arduino board
* Robotic arm (3 DOF + gripper)
* Microphone



##  Software Requirements

Install the following on your system:

* Python (3.8 to 3.10 recommended)
* Arduino IDE
* VS Code (optional but recommended)



##  Required Python Libraries

Open Command Prompt and install the following:

```bash
pip install numpy
pip install opencv-python
pip install ultralytics
pip install pyrealsense2
pip install pyserial
pip install pvporcupine
pip install pyaudio
pip install openai-whisper
pip install sounddevice
pip install scipy
pip install librosa
```



###  Important Fix (PyAudio Issue)

If `pyaudio` fails:

```bash
pip install pipwin
pipwin install pyaudio
```



##  File Path Setup (VERY IMPORTANT)

You MUST update paths in code before running.

### Update YOLO model path:

In your Python files:

```python
model = YOLO("models/best.pt")
```


### Update Wake Word Path:

```python
WAKE_WORD_PATH = "wakeword/jarvis.ppn"
```


### Update Serial Port:

```python
ser = serial.Serial("COM13", 115200, timeout=1)
```

 Change `"COM13"` to your actual Arduino port


##  Arduino Setup

### Step 1: Open Arduino IDE

Open file:

```
motor_fin.ino
```


### Step 2: Select Board

* Go to **Tools → Board**
* Select your ESP / Arduino board


### Step 3: Select Port

* Go to **Tools → Port**
* Select correct COM port


### Step 4: Upload Code

Click **Upload**


##  Running the Project

### Step 1: Connect Everything

* Connect RealSense camera
* Connect Arduino board
* Ensure microphone is working


### Step 2: Run Main File

Open terminal in project folder:

```bash
python all_classes.py
```


##  How the System Works

### 1. Vision

* Camera detects objects using YOLO
* Depth is used to calculate 3D position
* Coordinates are converted to robot frame


### 2. Voice

* System listens for wake word: **"Jarvis"**
* Records audio after detection
* Converts speech to text


### 3. Command Processing

* Matches spoken object name with detected objects
* Extracts object position


### 4. Inverse Kinematics

* Converts (x, y, z) → joint angles
* Angles sent to Arduino


### 5. Arm Movement

* Arduino receives commands via serial
* Moves joints step-by-step
* Closes gripper


##  Example Commands

* "Jarvis pick bottle"
* "Jarvis grab cube"
* "Jarvis where is bottle"


##  Important Notes

* Make sure camera is stable and calibrated
* Ensure good lighting for detection
* Depth accuracy depends on surface quality
* Serial communication must match correct COM port


##  Common Errors & Fixes

### Problem: No objects detected

→ Check model path and camera connection


### Problem: Voice not detected

→ Check microphone and wake word file


### Problem: Arm not moving

→ Check COM port and Arduino upload


### Problem: Wrong positions

→ Adjust translation (tx, ty, tz) in code


