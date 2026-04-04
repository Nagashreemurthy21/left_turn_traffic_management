import argparse
import os
import os.path as osp
import torch
from torch.autograd import Variable
import cv2
import warnings
import time

warnings.filterwarnings('ignore')

print("🚦 Intelligent Traffic System (AI + Camera + Demo) Starting...\n")

from util.parser import load_classes
from util.model import Darknet
from util.image_processor import preparing_image
from util.utils import non_max_suppression

# ---------------- ARGUMENTS ----------------
def arg_parse():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", default="demo_left",
                        help="camera / demo_left / demo_pedestrian / demo_conflict / demo_empty")
    parser.add_argument("--confidence", default=0.4)
    parser.add_argument("--nms_thresh", default=0.3)
    parser.add_argument("--cfg", default="config/yolov3.cfg")
    parser.add_argument("--weights", default="weights/yolov3.weights")
    parser.add_argument("--reso", default="416")
    return parser.parse_args()

args = arg_parse()
mode = args.mode.replace("-", "_")

CUDA = torch.cuda.is_available()

# ✅ KEEP YOUR ORIGINAL DATASET
classes = load_classes("data/idd.names")

# ---------------- MODEL ----------------
model = Darknet(args.cfg)
model.load_weights(args.weights)
model.hyperparams["height"] = args.reso
inp_dim = int(model.hyperparams["height"])

if CUDA:
    model.cuda()

model.eval()

# ---------------- GAP SYSTEM ----------------
last_vehicle_time = None
SAFE_GAP_THRESHOLD = 2.5


# ================= PROCESS FRAME =================
def process_frame(frame):

    global last_vehicle_time

    h, w = frame.shape[:2]

    left_lane_count = 0
    conflict_count = 0
    pedestrian_count = 0
    vehicle_count = 0

    current_time = time.time()
    current_gap = 0
    safe_gap = False

    inp = preparing_image(frame, inp_dim)

    if CUDA:
        inp = inp.cuda()

    with torch.no_grad():
        prediction = model(Variable(inp))

    prediction = non_max_suppression(
        prediction,
        float(args.confidence),
        model.num_classes,
        nms_conf=float(args.nms_thresh)
    )

    if type(prediction) == int:
        return frame, "WAIT ⚠️"

    output = prediction.cpu()

    # ---------------- ZONES ----------------
    cv2.rectangle(frame, (0, 0), (int(w*0.4), h), (255, 0, 0), 2)
    cv2.rectangle(frame, (int(w*0.4), 0), (int(w*0.6), h), (0, 0, 255), 2)
    cv2.rectangle(frame, (int(w*0.6), 0), (w, h), (0, 255, 0), 2)

    conflict_vehicle_present = False

    # ================= DETECTION =================
    for x in output:

        cls_id = int(x[-1].item())

        if cls_id >= len(classes):
            continue

        cls = classes[cls_id]

        x1 = int(x[1].item())
        y1 = int(x[2].item())
        x2 = int(x[3].item())
        y2 = int(x[4].item())

        center_x = (x1 + x2) // 2

        # VEHICLES
        if cls.lower() in ["car", "truck", "bus", "motorcycle", "bicycle"]:
            vehicle_count += 1

        # PEDESTRIANS
        if cls.lower() == "person":
            pedestrian_count += 1

        # ZONE LOGIC
        if center_x < w * 0.4:
            left_lane_count += 1
            color = (255, 0, 0)

        elif center_x < w * 0.6:
            conflict_count += 1
            conflict_vehicle_present = True
            color = (0, 0, 255)

        else:
            color = (0, 255, 0)

        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        cv2.putText(frame, cls, (x1, y1-5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

    # ---------------- GAP ----------------
    if conflict_vehicle_present:
        last_vehicle_time = current_time
        current_gap = 0
        safe_gap = False
    else:
        if last_vehicle_time:
            current_gap = current_time - last_vehicle_time
            if current_gap > SAFE_GAP_THRESHOLD:
                safe_gap = True

    # ---------------- DENSITY ----------------
    if vehicle_count == 0:
        density = "EMPTY 🟢"
    elif vehicle_count < 5:
        density = "LOW 🟡"
    elif vehicle_count < 10:
        density = "MEDIUM 🟠"
    else:
        density = "HIGH 🔴"

    total = left_lane_count + conflict_count

    # ================= DECISION =================
    if mode == "demo_left" or mode == "camera":

        if safe_gap and left_lane_count > 0:
            decision = "ALLOW ✅ (SAFE GAP)"
            col = (0, 255, 0)
        else:
            decision = "BLOCK ❌"
            col = (0, 0, 255)

    elif mode == "demo_pedestrian":

        if pedestrian_count >= 1:
            decision = "BLOCK ❌ (PEDESTRIAN)"
            col = (0, 0, 255)
        else:
            decision = "ALLOW ✅"
            col = (0, 255, 0)

    elif mode == "demo_conflict":

        if conflict_count >= 3:
            decision = "BLOCK ❌ (TRAFFIC)"
            col = (0, 0, 255)
        else:
            decision = "CONTROLLED ⚠️"
            col = (0, 165, 255)

    elif mode == "demo_empty":

        if vehicle_count == 0:
            decision = "ALLOW ✅ (EMPTY)"
            col = (0, 255, 0)
        else:
            decision = "WAIT ⚠️"
            col = (0, 255, 255)

    else:
        decision = "WAIT ⚠️"
        col = (0, 255, 255)

    # ---------------- UI ----------------
    cv2.rectangle(frame, (20, 50), (600, 350), (0, 0, 0), -1)

    cv2.putText(frame, f"Mode: {mode}", (30, 80),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,0), 2)

    cv2.putText(frame, f"Decision: {decision}", (30, 110),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, col, 2)

    cv2.putText(frame, f"Vehicles: {vehicle_count}", (30, 150),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 2)

    cv2.putText(frame, f"Density: {density}", (30, 180),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 2)

    cv2.putText(frame, f"Left Lane: {left_lane_count}", (30, 210),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 2)

    cv2.putText(frame, f"Conflict Lane: {conflict_count}", (30, 240),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 2)

    cv2.putText(frame, f"Pedestrians: {pedestrian_count}", (30, 270),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 2)

    cv2.putText(frame, f"Gap: {round(current_gap,2)} sec", (30, 300),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 2)

    cv2.putText(frame, f"Safe Gap: {safe_gap}", (30, 330),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 2)

    return frame, decision


# ================= RUN =================

# 🎥 CAMERA MODE
if mode == "camera":

    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("❌ Camera not working")
        exit()

    print("🎥 Camera started... Press ESC to exit")

    while True:

        ret, frame = cap.read()

        if not ret:
            break

        frame, decision = process_frame(frame)

        cv2.imshow("🚦 LIVE TRAFFIC", frame)

        print("Live →", decision)

        if cv2.waitKey(1) == 27:
            break

    cap.release()
    cv2.destroyAllWindows()


# 🖼 IMAGE DEMO MODE
else:

    try:
        images = sorted(os.listdir(mode))
    except:
        print("❌ Folder not found:", mode)
        exit()

    print(f"📂 Processing: {mode} | Images: {len(images)}")

    for img_name in images:

        img_path = osp.join(mode, img_name)

        frame = cv2.imread(img_path)
        if frame is None:
            continue

        frame, decision = process_frame(frame)

        cv2.imshow(f"🚦 {mode}", frame)

        print(f"{img_name} → {decision}")

        if cv2.waitKey(1500) == 27:
            break

    cv2.destroyAllWindows()