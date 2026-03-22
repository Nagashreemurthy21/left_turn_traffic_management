from __future__ import division
import argparse
import os
import os.path as osp
import torch
from torch.autograd import Variable
import cv2
import warnings
warnings.filterwarnings('ignore')

print('\033[1m' + '\033[91m' + "Kickstarting YOLO...\n")

from util.parser import load_classes
from util.model import Darknet
from util.image_processor import preparing_image
from util.utils import non_max_suppression

# ---------------- ARGUMENTS ----------------
def arg_parse():
    parser = argparse.ArgumentParser(description='YOLO Traffic System')
    parser.add_argument("--images", default="vehicles-on-lanes", type=str)
    parser.add_argument("--confidence", default=0.4)
    parser.add_argument("--nms_thresh", default=0.3)
    parser.add_argument("--cfg", default="config/yolov3.cfg", type=str)
    parser.add_argument("--weights", default="weights/yolov3.weights", type=str)
    parser.add_argument("--reso", default="416", type=str)
    return parser.parse_args()

args = arg_parse()
images = args.images
confidence = float(args.confidence)
nms_thesh = float(args.nms_thresh)

CUDA = torch.cuda.is_available()
classes = load_classes("data/idd.names")

# ---------------- MODEL ----------------
model = Darknet(args.cfg)
print("Input Data Passed Into YOLO Model...✓")
model.load_weights(args.weights)
print("YOLO Neural Network Successfully Loaded...✓\n")

model.hyperparams["height"] = args.reso
inp_dim = int(model.hyperparams["height"])

if CUDA:
    model.cuda()
model.eval()

# ---------------- LOAD IMAGES ----------------
try:
    imlist = [osp.join(osp.realpath('.'), images, img) for img in os.listdir(images)]
except:
    print("Error loading images")
    exit()

loaded_ims = []
for x in imlist:
    img = cv2.imread(x)
    if img is not None:
        loaded_ims.append(img)
    else:
        print(f"Skipping invalid image: {x}")

im_batches = list(map(preparing_image, loaded_ims, [inp_dim]*len(loaded_ims)))

decision = "WAIT ⚠️"

print("\n" + "-"*120)
print("SUMMARY")
print("-"*120)

# ---------------- MAIN LOOP ----------------
for i, batch in enumerate(im_batches):

    if CUDA:
        batch = batch.cuda()

    with torch.no_grad():
        prediction = model(Variable(batch))

    prediction = non_max_suppression(
        prediction, confidence, model.num_classes, nms_conf=nms_thesh
    )

    if type(prediction) == int:
        continue

    output = prediction.cpu()

    for frame in loaded_ims:

        h, w = frame.shape[:2]

        left_lane_count = 0
        conflict_count = 0
        objs = []

        # ---------------- DRAW ZONES ----------------
        cv2.rectangle(frame, (0, 0), (int(w*0.4), h), (255, 0, 0), 2)
        cv2.rectangle(frame, (int(w*0.4), 0), (int(w*0.75), h), (0, 0, 255), 2)
        cv2.rectangle(frame, (int(w*0.75), 0), (w, h), (0, 255, 0), 2)

        # ---------------- DETECTION ----------------
        for x in output:
            cls = classes[int(x[-1].item())]
            objs.append(cls)

            if cls in ["car", "motorbike", "truck", "bicycle", "autorickshaw", "person"]:

                x1 = int(x[1].item())
                y1 = int(x[2].item())
                x2 = int(x[3].item())
                y2 = int(x[4].item())

                # 🔥 FIXED ZONE LOGIC (overlap based)
                if x2 < w * 0.4:
                    left_lane_count += 1
                    color = (255, 0, 0)

                elif x1 < w * 0.75:
                    conflict_count += 1
                    color = (0, 0, 255)

                else:
                    color = (0, 255, 0)

                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

        # ---------------- PEDESTRIAN CHECK ----------------
        person_count = 0

        for x in output:
            cls = classes[int(x[-1].item())]

            if cls == "person":
                x1 = int(x[1].item())
                x2 = int(x[3].item())

                if x2 < w * 0.85:
                    person_count += 1

        # ---------------- FINAL DECISION ----------------
        if person_count > 3 and conflict_count > 0:
            decision = "BLOCKED ❌ (PEDESTRIAN)"
            color = (0,0,255)

        elif conflict_count > 0:
            decision = "BLOCKED ❌ (TRAFFIC)"
            color = (0,0,255)

        elif left_lane_count > 0:
            decision = "LEFT TURN ALLOWED ✅"
            color = (0,255,0)

        else:
            decision = "WAIT ⚠️"
            color = (0,255,255)

        # ---------------- UI ----------------
        cv2.rectangle(frame, (20, 50), (420, 180), (0, 0, 0), -1)

        cv2.putText(frame, decision, (30, 90),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

        cv2.putText(frame, f"Left: {left_lane_count}", (30, 120),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 2)

        cv2.putText(frame, f"Conflict: {conflict_count}", (30, 150),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 2)

        cv2.imshow("Intelligent Left Turn System", frame)

        if cv2.waitKey(3000) & 0xFF == 27:
            break

# ---------------- FINAL OUTPUT ----------------
print("\n🚦 FINAL LEFT TURN DECISION:", decision)
print("-"*120)

cv2.destroyAllWindows()
torch.cuda.empty_cache()