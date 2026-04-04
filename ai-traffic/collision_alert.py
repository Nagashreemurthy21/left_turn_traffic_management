import cv2
import numpy as np
from ultralytics import YOLO
import pygame

# ================= LOAD MODEL =================
model = YOLO(r"C:\Users\NAGASHREE K S\runs\detect\train\weights\best.pt")

# ================= SOUND SETUP =================
pygame.mixer.init()
pygame.mixer.music.load("siren.mp3")

# ================= CLASS IDs =================
PERSON_ID = 0
VEHICLE_IDS = [1, 2, 3, 4, 5]  # car, bus, truck, bike, motor

# ================= DISTANCE THRESHOLD =================
DANGER_DISTANCE = 120  # pixels (adjust later)

# ================= VIDEO SOURCE =================
cap = cv2.VideoCapture(0)  # 0 = webcam
# cap = cv2.VideoCapture("test.mp4")  # for video file

while True:
    ret, frame = cap.read()
    if not ret:
        break

    results = model(frame)[0]

    persons = []
    vehicles = []

    # ================= EXTRACT BOXES =================
    for box in results.boxes:
        cls = int(box.cls[0])
        x1, y1, x2, y2 = map(int, box.xyxy[0])

        cx = (x1 + x2) // 2
        cy = (y1 + y2) // 2

        if cls == PERSON_ID:
            persons.append((cx, cy))
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

        elif cls in VEHICLE_IDS:
            vehicles.append((cx, cy))
            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)

    danger = False

    # ================= CHECK COLLISION =================
    for px, py in persons:
        for vx, vy in vehicles:
            distance = np.sqrt((px - vx)**2 + (py - vy)**2)

            if distance < DANGER_DISTANCE:
                danger = True

                # draw warning line
                cv2.line(frame, (px, py), (vx, vy), (0, 0, 255), 3)

    # ================= ALERT =================
    if danger:
        cv2.putText(frame, "⚠️ COLLISION RISK!", (50, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)

        if not pygame.mixer.music.get_busy():
            pygame.mixer.music.play()

    # ================= SHOW FRAME =================
    cv2.imshow("Traffic AI", frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()