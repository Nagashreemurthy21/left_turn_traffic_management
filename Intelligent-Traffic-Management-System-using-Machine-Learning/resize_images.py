import cv2
import os

folders = ["demo_left", "demo_conflict", "demo_pedestrian", "demo_empty"]

for folder in folders:
    if not os.path.exists(folder):
        print(f"❌ Folder not found: {folder}")
        continue

    for file in os.listdir(folder):
        path = os.path.join(folder, file)

        img = cv2.imread(path)
        if img is None:
            continue

        resized = cv2.resize(img, (640, 640))
        cv2.imwrite(path, resized)

    print(f"✅ Resized all images in {folder}")

print("🎉 Done!")