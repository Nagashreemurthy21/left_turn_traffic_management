import traci
import time
import cv2

# ✅ correct import
from itms_yolov3 import process_frame

# ================= SUMO =================
sumoCmd = [
    r"C:\Program Files (x86)\Eclipse\Sumo\bin\sumo-gui.exe",
    "-c",
    r"C:\Users\NAGASHREE K S\OneDrive\Desktop\left-turn-ai\ai-traffic\sumo\config.sumocfg"
]

traci.start(sumoCmd)

junction_id = "n1"

print("🚀 YOLO + SUMO INTEGRATED SYSTEM")


# 🔥 improve visibility
traci.gui.setZoom("View #0", 2000)


# ================= CAPTURE SUMO =================
def capture_sumo():
    try:
        traci.gui.screenshot("View #0", "temp.png")
        frame = cv2.imread("temp.png")
        return frame
    except:
        return None


# ================= CONTROL =================
def apply_signal(decision):

    if decision.startswith("ALLOW"):
        state = "GGrrGGrr"
        msg = "🟢 LEFT ALLOWED"
    elif decision.startswith("CONTROLLED"):
        state = "yyrryyrr"
        msg = "🟡 CONTROLLED"
    else:
        state = "rrGGrrGG"
        msg = "🔴 BLOCKED"

    try:
        traci.trafficlight.setRedYellowGreenState(junction_id, state)
        traci.gui.setStatusBarText(msg)
    except:
        pass


# ================= MAIN LOOP =================
try:
    step = 0

    while True:
        traci.simulationStep()
        time.sleep(0.1)

        step += 1

        # 🔥 run YOLO every 20 steps
        if step % 20 == 0:

            frame = capture_sumo()

            if frame is None:
                continue

            frame, decision, conf = process_frame(frame)

            print(f"\n🧠 AI Decision: {decision}")

            apply_signal(decision)

            cv2.imshow("YOLO + SUMO", frame)

            if cv2.waitKey(1) == 27:
                break

except KeyboardInterrupt:
    print("\n🛑 Stopping...")

finally:
    print("🔴 Closing SUMO...")
    traci.close()
    cv2.destroyAllWindows()