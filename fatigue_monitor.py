# fatigue_monitor.py
import cv2
import time
import mediapipe as mp
from plyer import notification

stop_flag = None

def start_monitoring(stop_event):
    global stop_flag
    stop_flag = stop_event

    print("[INFO] Starting monitoring...")

    # Initialize MediaPipe
    mp_face_mesh = mp.solutions.face_mesh
    mp_drawing = mp.solutions.drawing_utils
    face_mesh = mp_face_mesh.FaceMesh(
        static_image_mode=False,
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    )

    # Open webcam
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    blink_counter = 0
    closed_eyes_frame = 0
    monitoring_start = time.time()

    while not stop_flag.is_set():
        ret, frame = cap.read()
        if not ret:
            break

        h, w, _ = frame.shape
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(frame_rgb)

        EAR = 0
        if results.multi_face_landmarks:
            for landmarks in results.multi_face_landmarks:
                # Draw face mesh on frame
                mp_drawing.draw_landmarks(
                    image=frame,
                    landmark_list=landmarks,
                    connections=mp_face_mesh.FACEMESH_CONTOURS,
                    landmark_drawing_spec=mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=1, circle_radius=1),
                    connection_drawing_spec=mp_drawing.DrawingSpec(color=(0, 0, 255), thickness=1)
                )

                # Get eye landmarks for EAR
                right_eye_top = landmarks.landmark[159].y * h
                right_eye_bottom = landmarks.landmark[145].y * h
                EAR = abs(right_eye_top - right_eye_bottom)

                # Blink Detection
                if EAR < 5:  # eye is closed
                    closed_eyes_frame += 1
                else:
                    if 1 < closed_eyes_frame < 10:
                        blink_counter += 1
                    closed_eyes_frame = 0

        # Every 60 seconds, check blink rate
        if time.time() - monitoring_start >= 60:
            current_blink_rate = blink_counter
            blink_counter = 0
            monitoring_start = time.time()

            print(f"[INFO] Blink Rate: {current_blink_rate}/min | EAR: {EAR:.2f}")

            if current_blink_rate > 22:
                notification.notify(
                    title="👀 Eye Strain Warning",
                    message="You're blinking too frequently. You may be tired or straining. Consider resting.",
                    timeout=7
                )
            elif current_blink_rate < 6:
                if closed_eyes_frame > 30:
                    notification.notify(
                        title="😴 Drowsiness Detected!",
                        message="Long eye closures detected. You seem sleepy. Take a short break.",
                        timeout=7
                    )
                else:
                    notification.notify(
                        title="⚠️ Fatigue Warning",
                        message="Low blink rate detected. You may be tired or losing focus.",
                        timeout=7
                    )
            else:
                print("[INFO] Blink rate is normal.")

        # Show frame with mesh
        cv2.imshow("Fatigue Monitor", frame)
        if cv2.waitKey(1) & 0xFF == 27:
            break

    print("[INFO] Monitoring stopped.")
    cap.release()
    cv2.destroyAllWindows()
