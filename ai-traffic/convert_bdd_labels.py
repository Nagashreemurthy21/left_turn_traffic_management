import json
import os
from tqdm import tqdm

# ===== PATHS =====
json_path = r"C:\Users\NAGASHREE K S\OneDrive\Desktop\left-turn-ai\ai-traffic\traffic-ai\bdd100k_labels_release\bdd100k\labels\bdd100k_labels_images_train.json"

output_dir = r"C:\Users\NAGASHREE K S\OneDrive\Desktop\left-turn-ai\ai-traffic\traffic-ai\bdd100k_labels_release\bdd100k\labels\det_20\train"

os.makedirs(output_dir, exist_ok=True)

# ===== CLASS MAP =====
class_map = {
    "person": 0,
    "car": 1,
    "bus": 2,
    "truck": 3,
    "bike": 4,
    "motor": 5
}

# ===== LOAD JSON =====
with open(json_path) as f:
    data = json.load(f)

# ===== CONVERT =====
for item in tqdm(data):
    img_name = item["name"]
    labels = item.get("labels", [])

    txt_path = os.path.join(output_dir, img_name.replace(".jpg", ".txt"))

    lines = []

    for obj in labels:
        if "box2d" not in obj:
            continue

        category = obj["category"]
        if category not in class_map:
            continue

        cls_id = class_map[category]
        box = obj["box2d"]

        x1, y1 = box["x1"], box["y1"]
        x2, y2 = box["x2"], box["y2"]

        img_w, img_h = 1280, 720  # BDD100K size

        xc = ((x1 + x2) / 2) / img_w
        yc = ((y1 + y2) / 2) / img_h
        w = (x2 - x1) / img_w
        h = (y2 - y1) / img_h

        lines.append(f"{cls_id} {xc} {yc} {w} {h}")

    if lines:
        with open(txt_path, "w") as f:
            f.write("\n".join(lines))