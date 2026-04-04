import os

src_img_root = r"C:\Users\NAGASHREE K S\OneDrive\Desktop\left-turn-ai\ai-traffic\traffic-ai\bdd100k\bdd100k\images\100k\train"

src_lbl_root = r"C:\Users\NAGASHREE K S\OneDrive\Desktop\left-turn-ai\ai-traffic\traffic-ai\bdd100k_labels_release\bdd100k\labels\det_20\train"

print("Images:", os.path.exists(src_img_root))
print("Labels:", os.path.exists(src_lbl_root))