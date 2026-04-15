import pyrealsense2 as rs
import numpy as np
import cv2
from ultralytics import YOLO

model = YOLO(r"C:\Users\dvsai\OneDrive - Anna University\Desktop\VLA_model\full_model\best.pt")

pipeline = rs.pipeline()
config = rs.config()

config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)

profile = pipeline.start(config)

align = rs.align(rs.stream.color)

color_stream = profile.get_stream(rs.stream.color)
intr = color_stream.as_video_stream_profile().get_intrinsics()

print("Camera Intrinsics:")
print("fx:", intr.fx)
print("fy:", intr.fy)
print("cx:", intr.ppx)
print("cy:", intr.ppy)

tx = -0.10 
ty = 0.20
tz = 0.180

t = np.array([tx, ty, tz])

pitch_deg = 19
roll_deg = 4

pitch = np.radians(pitch_deg)
roll = np.radians(roll_deg)

R_pitch = np.array([
    [ np.cos(pitch), 0, np.sin(pitch)],
    [ 0,             1, 0            ],
    [-np.sin(pitch), 0, np.cos(pitch)]
])

R_roll = np.array([
    [1, 0,              0             ],
    [0, np.cos(roll),  -np.sin(roll)],
    [0, np.sin(roll),   np.cos(roll)]
])

R_total = R_roll @ R_pitch

try:

    while True:

        frames = pipeline.wait_for_frames()
        frames = align.process(frames)

        color_frame = frames.get_color_frame()
        depth_frame = frames.get_depth_frame()

        if not color_frame or not depth_frame:
            continue

        frame = np.asanyarray(color_frame.get_data())

        results = model(frame, conf=0.5)

        for box in results[0].boxes:

            x1, y1, x2, y2 = map(int, box.xyxy[0])

            # ✅ ONLY ADDITION
            cls_id = int(box.cls[0])
            class_name = model.names[cls_id]

            cx = int((x1 + x2) / 2)
            cy = int((y1 + y2) / 2)

            depth = depth_frame.get_distance(cx, cy)

            point = rs.rs2_deproject_pixel_to_point(intr, [cx, cy], depth)

            X_cam = point[0]
            Y_cam = point[1]
            Z_cam = point[2]

            X = Z_cam
            Y = -X_cam
            Z = -Y_cam
            
            P_cam = np.array([X, Y, Z])

            P_corrected = R_total @ P_cam

            P_base = P_corrected + t

            Xb, Yb, Zb = P_base

            # ✅ ONLY CHANGE HERE
            label = f"{class_name} | X:{Xb:.2f} Y:{Yb:.2f} Z:{Zb:.2f}"

            cv2.rectangle(frame, (x1, y1), (x2, y2), (0,255,0), 2)
            cv2.circle(frame, (cx,cy), 4, (0,0,255), -1)

            cv2.putText(frame, label, (x1, y1-10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6, (0,255,0), 2)

        cv2.imshow("YOLO RealSense 3D Detection", frame)

        if cv2.waitKey(1) & 0xFF == 27:
            break

finally:
    pipeline.stop()
    cv2.destroyAllWindows()