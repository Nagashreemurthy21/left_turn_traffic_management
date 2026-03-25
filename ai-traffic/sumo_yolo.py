import traci
import cv2

# 🔥 IMPORT YOUR FILE
from itms_yolov3 import process_frame   # IMPORTANT

# Start SUMO
sumoCmd = [
    r"C:\Program Files (x86)\Eclipse\Sumo\bin\sumo-gui.exe",
    "-c",
    "sumo/config.sumocfg"
]
traci.start(sumoCmd)

cap = cv2.VideoCapture(0)  # or use demo video

step = 0
import traci
import cv2
import os

# 🔥 IMPORT YOUR YOLO FILE
from itms_yolov3 import process_frame

# ---------------- SUMO START ----------------
sumoCmd = [
    r"C:\Program Files (x86)\Eclipse\Sumo\bin\sumo-gui.exe",
    "-c",
    "sumo/config.sumocfg"
]

try:
    traci.start(sumoCmd)
    print("✅ SUMO Started Successfully")
except Exception as e:
    print("⚠️ SUMO Error:", e)

# ---------------- CHOOSE MODE ----------------
# 👉 change this to test different folders
MODE = "demo_left"   # demo_left / demo_pedestrian / demo_empty / demo_conflict

image_folder = MODE

# ---------------- MAIN LOOP ----------------
images = os.listdir(image_folder)

for img_name in images:

    path = os.path.join(image_folder, img_name)

    frame = cv2.imread(path)
    if frame is None:
        continue

    # 🔥 YOLO DETECTION
    frame, decision, conf = process_frame(frame)

    print("\n🚦 FINAL DECISION:", decision)

    # ---------------- SUMO STEP ----------------
    try:
        traci.simulationStep()
    except:
        pass

    # ---------------- SIGNAL LOGIC ----------------
    if decision.startswith("ALLOW"):
        state = "GGGG"
    elif decision.startswith("BLOCK"):
        state = "RRRR"
    elif decision.startswith("CONTROLLED"):
        state = "yyyy"
    else:
        state = "rrrr"

    # ---------------- APPLY SIGNAL ----------------
    try:
        traci.trafficlight.setRedYellowGreenState("junction_1", state)
    except:
        pass

    # ---------------- DISPLAY ----------------
    cv2.imshow("🚦 YOLO Traffic Detection", frame)

    key = cv2.waitKey(2000)
    if key == 27:
        break

# ---------------- CLEANUP ----------------
cv2.destroyAllWindows()

try:
    traci.close()
except:
    pass

print("✅ Finished Execution")
while True:
    traci.simulationStep()

    ret, frame = cap.read()
    if not ret:
        break

    # 🔥 YOUR YOLO LOGIC
    frame, decision, conf = process_frame(frame)

    print("Decision:", decision)

    # 🔥 MAP DECISION → SUMO SIGNAL
    if decision.startswith("ALLOW"):
        state = "GGGG"   # green
    elif decision.startswith("BLOCK"):
        state = "RRRR"   # red
    elif decision.startswith("CONTROLLED"):
        state = "yyyy"   # yellow
    else:
        state = "rrrr"

    # ⚠️ (will work after we add junction)
    try:
        traci.trafficlight.setRedYellowGreenState("junction_1", state)
    except:
        pass

    cv2.imshow("YOLO + SUMO", frame)

    if cv2.waitKey(1) == 27:
        break

    step += 1

cap.release()
traci.close()
cv2.destroyAllWindows()