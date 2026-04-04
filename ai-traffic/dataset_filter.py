import os
import glob
import random
import shutil
import pathlib
from tqdm import tqdm
import cv2

# ================= CONFIG =================
src_img_root = r"C:\Users\NAGASHREE K S\OneDrive\Desktop\left-turn-ai\ai-traffic\traffic-ai\bdd100k\bdd100k\images\100k\train"

src_lbl_root = r"C:\Users\NAGASHREE K S\OneDrive\Desktop\left-turn-ai\ai-traffic\traffic-ai\bdd100k_labels_release\bdd100k\labels\det_20\train"

out_img_root = r"dataset_filtered/images"
out_lbl_root = r"dataset_filtered/labels"
out_max = 2000

vehicle_classes = {1, 2, 3, 4, 5}

pedestrian_classes = {0}

junction_ratio = 0.5

# relaxed filters (important)
min_vehicle_total = 1
min_pedestrian = 0
min_objects = 1

os.makedirs(out_img_root, exist_ok=True)
os.makedirs(out_lbl_root, exist_ok=True)

# ================= DEBUG =================
print("Checking paths...")
print("Images path exists:", os.path.exists(src_img_root))
print("Labels path exists:", os.path.exists(src_lbl_root))

# ================= FUNCTIONS =================
def get_label_path(image_path):
    rel_path = os.path.relpath(image_path, src_img_root)
    lab_path = pathlib.Path(rel_path).with_suffix(".txt")
    return os.path.join(src_lbl_root, str(lab_path))

def junction_box_img(img_w, img_h):
    cx = img_w / 2.0
    cy = img_h / 2.0
    jw = img_w * junction_ratio
    jh = img_h * junction_ratio
    return (cx - jw / 2.0, cy - jh / 2.0, cx + jw / 2.0, cy + jh / 2.0)

def intersects_junction(xc, yc, w, h, img_w, img_h):
    x1, y1, x2, y2 = junction_box_img(img_w, img_h)
    bx1 = (xc - w / 2.0) * img_w
    by1 = (yc - h / 2.0) * img_h
    bx2 = (xc + w / 2.0) * img_w
    by2 = (yc + h / 2.0) * img_h

    ix = max(0, min(x2, bx2) - max(x1, bx1))
    iy = max(0, min(y2, by2) - max(y1, by1))

    inter_area = ix * iy
    box_area = (bx2 - bx1) * (by2 - by1)

    if box_area <= 0:
        return False

    return (inter_area / box_area) >= 0.20

def score_frame(label_path, img_w, img_h):
    try:
        with open(label_path, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip()]
    except:
        return 0.0

    if len(lines) < min_objects:
        return 0.0

    veh_count = 0
    ped_count = 0
    veh_in_junc = 0
    ped_in_junc = 0
    total_area = 0.0

    for ln in lines:
        parts = ln.split()
        if len(parts) != 5:
            continue

        try:
            cls_id = int(parts[0])
            xc, yc, w, h = map(float, parts[1:])
        except:
            continue

        area = w * h
        total_area += area

        is_junc = intersects_junction(xc, yc, w, h, img_w, img_h)

        if cls_id in pedestrian_classes:
            ped_count += 1
            if is_junc:
                ped_in_junc += 1

        if cls_id in vehicle_classes:
            veh_count += 1
            if is_junc:
                veh_in_junc += 1

    if veh_count < min_vehicle_total or ped_count < min_pedestrian:
        return 0.0

    score = (
        1.0 * veh_count +
        1.5 * ped_count +
        2.0 * veh_in_junc +
        2.0 * ped_in_junc +
        3.0 * min(veh_in_junc, ped_in_junc) +
        2.5 * min(2, veh_count + ped_count)
    )

    score += 20.0 * min(1.0, (veh_count + ped_count) / 12.0)
    score += 20.0 * min(1.0, total_area * 2.5)

    return score

# ================= LOAD IMAGES =================
img_files = glob.glob(os.path.join(src_img_root, "**", "*.jpg"), recursive=True)
img_files += glob.glob(os.path.join(src_img_root, "**", "*.png"), recursive=True)

print("Total images found:", len(img_files))

random.shuffle(img_files)

# ================= PROCESS =================
scored = []
missing_labels = 0

for img_path in tqdm(img_files, desc="Evaluate frames"):
    lbl_path = get_label_path(img_path)

    if not os.path.exists(lbl_path):
        missing_labels += 1
        continue

    img = cv2.imread(img_path)
    if img is None:
        continue

    h, w = img.shape[:2]

    sc = score_frame(lbl_path, w, h)

    if sc > 0:
        scored.append((sc, img_path, lbl_path))

print("Missing labels:", missing_labels)
print("Valid scored frames:", len(scored))

# ================= SELECTION =================
if not scored:
    print("⚠️ No frames matched, selecting random images...")

    selected = []
    for img_path in img_files[:out_max]:
        lbl_path = get_label_path(img_path)
        if os.path.exists(lbl_path):
            selected.append((1, img_path, lbl_path))
else:
    scored.sort(reverse=True, key=lambda x: x[0])
    selected = scored[:out_max]

# ================= COPY =================
for _, img_path, lbl_path in tqdm(selected, desc="Copy dataset"):
    rel_img = os.path.relpath(img_path, src_img_root)
    rel_lbl = os.path.relpath(lbl_path, src_lbl_root)

    dst_img = os.path.join(out_img_root, rel_img)
    dst_lbl = os.path.join(out_lbl_root, rel_lbl)

    os.makedirs(os.path.dirname(dst_img), exist_ok=True)
    os.makedirs(os.path.dirname(dst_lbl), exist_ok=True)

    shutil.copy2(img_path, dst_img)
    shutil.copy2(lbl_path, dst_lbl)

print("\n✅ DONE — dataset_filtered created!")