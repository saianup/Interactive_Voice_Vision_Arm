#include <ESP32Servo.h>

Servo servo1;  
Servo servo2;  
Servo servo3;  
Servo gripper;  

// Servo pins
int servoPin1 = 18;
int servoPin2 = 19;
int servoPin3 = 21;
int gripperPin = 22;   // change if needed

// Current angles
int angle1 = 0;
int angle2 = 0;
int angle3 = 0;

// Speed control (bigger = slower)
int speedDelay = 35;


// -------- Smooth Movement Function --------
void moveServoSmooth(Servo &servo, int &currentAngle, int targetAngle) {

  if (targetAngle > currentAngle) {
    for (int pos = currentAngle; pos <= targetAngle; pos++) {
      servo.write(pos);
      delay(speedDelay);
    }
  } 
  else {
    for (int pos = currentAngle; pos >= targetAngle; pos--) {
      servo.write(pos);
      delay(speedDelay);
    }
  }

  currentAngle = targetAngle;
}


// -------- Setup --------
void setup() {

  Serial.begin(115200);

  servo1.attach(servoPin1);
  servo2.attach(servoPin2);
  servo3.attach(servoPin3);
  gripper.attach(gripperPin);

  Serial.println("=== 4 Servo Robot Arm Control ===");
  Serial.println("Format: joint angle");
  Serial.println("1,2,3 → arm joints");
  Serial.println("4 → gripper");
  Serial.println("Example: 1 90");
}


// -------- Main Loop --------
void loop() {

  if (Serial.available() > 0) {

    int joint = Serial.parseInt();
    int angle = Serial.parseInt();

    if (joint >= 1 && joint <= 4 && angle >= 0 && angle <= 180) {

      switch (joint) {

        case 1:
          moveServoSmooth(servo1, angle1, angle);
          break;

        case 2:
          moveServoSmooth(servo2, angle2, angle);
          break;

        case 3: {

          int mappedAngle;

          if (angle <= 90) {
            mappedAngle = map(angle, 0, 90, 0, 65);
          }
          else {
            mappedAngle = map(angle, 90, 180, 65, 135);
          }

          moveServoSmooth(servo3, angle3, mappedAngle);

          break;
        }

        case 4:
          // Gripper control (instant)
          if (angle == 0) {
            gripper.write(0);
            Serial.println("Gripper OPEN");
          }
          else if (angle == 90) {
            gripper.write(90);
            Serial.println("Gripper CLOSE");
          }
          else {
            Serial.println("Use 0 for OPEN or 90 for CLOSE");
          }
          break;
      }

      Serial.print("Moved Joint ");
      Serial.print(joint);
      Serial.print(" to ");
      Serial.print(angle);
      Serial.println("°");
    }

    else {
      Serial.println("Invalid input! Use: joint(1–4) angle");
    }

    while (Serial.available() > 0) Serial.read();

    Serial.print("Current Angles -> S1: ");
    Serial.print(angle1);
    Serial.print("°, S2: ");
    Serial.print(angle2);
    Serial.print("°, S3: ");
    Serial.print(angle3);
    Serial.println("°");

    Serial.println("Enter next command (ex: 2 120):");
  }
}
