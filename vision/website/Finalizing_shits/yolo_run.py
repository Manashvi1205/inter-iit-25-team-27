import os
import cv2
import numpy as np
from qrdet import QRDetector

import yolo_lib   # your file
from yolo_lib import crop_qr, annotate_img   # import your functions


# ================================
# USER SETTINGS
# ================================
input_folder = r"D:/qr_images"          # <-- your input image folder
crop_output  = r"D:/qr_images/crops"    # <-- cropped QR output
anno_output  = r"D:/qr_images/annotated"  # <-- annotated output


def run_crop_anno(height, orientation)
    # Make output folders
    os.makedirs(crop_output, exist_ok=True)
    os.makedirs(anno_output, exist_ok=True)

    # ================================
    # INITIALIZE DETECTOR
    # ================================
    detector = QRDetector(model_size='s')   # model sizes: s, m, l, x

    # ================================
    # PROCESS EACH IMAGE IN FOLDER
    # ================================
    for filename in os.listdir(input_folder):

        if not filename.lower().endswith((".jpg", ".jpeg", ".png", ".bmp")):
            continue

        image_path = os.path.join(input_folder, filename)
        print(f"[INFO] Processing {image_path}")

        # Read image
        img = cv2.imread(image_path)
        if img is None:
            print(f"[WARN] Failed to load {filename}")
            continue

        # Run QR detection
        detections = detector.detect(image=img, is_bgr=True)

        # Output file paths
        crop_path = os.path.join(crop_output, f"crop_{filename}")
        anno_path = os.path.join(anno_output, f"anno_{filename}")

        # Apply your library functions
        crop_qr(img, detections, crop_path, height)
        annotate_img(img, detections, anno_path, height, orientation)

    print("[DONE] All images processed.")
