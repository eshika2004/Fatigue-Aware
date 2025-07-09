# recorder.py
import cv2
import time
import mediapipe as mp
import os
import json
from datetime import datetime

# Eye landmark indices for EAR calculation
RIGHT_EYE_IDX = [33, 160, 158, 133, 153, 144]
LEFT_EYE_IDX = [362, 385, 387, 263, 373, 380]

def get_eye_aspect_ratio(landmarks, eye_indices, h, w):
    top = (landmarks[eye_indices[1]].y + landmarks[eye_indices[2]].y) / 2
    bottom = (landmarks[eye_indices[5]].y + landmarks[eye_indices[4]].y) / 2
    left = landmarks[eye_indices[0]].x
    right = landmarks[eye_indices[3]].x

    vertical = abs(top - bottom) * h
    horizontal = abs(left - right) * w
    if horizontal == 0:
        return 0
    return vertical / horizontal

def record_for_5_minutes(stop_event):
    mp_face_mesh = mp.solutions.face_mesh
    mp_drawing = mp.solutions.drawing_utils
    face_mesh = mp_face_mesh.FaceMesh(static_image_mode=False, max_num_faces=1)

    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    os.makedirs("recordings", exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    video_filename = f"recordings/calibration_{timestamp}.avi"
    log_filename = f"recordings/blink_log_{timestamp}.txt"
    json_filename = f"recordings/baseline.json"

    out = cv2.VideoWriter(video_filename, fourcc, 20.0, (640, 480))

    blink_counter = 0
    closed_eyes_frame = 0
    start_time = time.time()
    duration = 5 * 60

    try:
        while time.time() - start_time < duration:
            if stop_event.is_set():
                print("[INFO] Recording stopped by user.")
                break

            ret, frame = cap.read()
            if not ret:
                break
            out.write(frame)

            h, w, _ = frame.shape
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = face_mesh.process(frame_rgb)

            if results.multi_face_landmarks:
                for face_landmarks in results.multi_face_landmarks:
                    mp_drawing.draw_landmarks(
                        frame, face_landmarks,
                        mp_face_mesh.FACEMESH_TESSELATION,
                        mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=1, circle_radius=1),
                        mp_drawing.DrawingSpec(color=(0, 0, 255), thickness=1)
                    )

                    landmarks = face_landmarks.landmark
                    left_ear = get_eye_aspect_ratio(landmarks, LEFT_EYE_IDX, h, w)
                    right_ear = get_eye_aspect_ratio(landmarks, RIGHT_EYE_IDX, h, w)
                    avg_ear = (left_ear + right_ear) / 2

                    if avg_ear < 0.20:
                        closed_eyes_frame += 1
                    else:
                        if closed_eyes_frame >= 2:
                            blink_counter += 1
                            print(f"Blink #{blink_counter}")
                        closed_eyes_frame = 0

            cv2.imshow("Recording...", frame)
            if cv2.waitKey(1) & 0xFF == 27:
                break

    finally:
        cap.release()
        out.release()
        cv2.destroyAllWindows()

        with open(log_filename, "w") as f:
            f.write(f"Blink Count: {blink_counter}\n")
            f.write(f"Duration: 5 minutes\n")
            f.write(f"Blinks per minute: {blink_counter / 5:.2f}\n")

        baseline_data = {
            "blink_count": blink_counter,
            "duration_minutes": 5,
            "blinks_per_minute": round(blink_counter / 5, 2),
            "timestamp": timestamp
        }
        with open(json_filename, "w") as f:
            json.dump(baseline_data, f, indent=4)

        print("[INFO] Recording saved.")
        print(f"[INFO] Blink Rate: {baseline_data['blinks_per_minute']} blinks/min")

    return video_filename, log_filename
