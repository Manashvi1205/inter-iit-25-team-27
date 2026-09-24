import os
import cv2

import enhance_lib
from enhance_lib import enhance_fin, detect_fin   # <-- your existing file
# your_module.py must contain: enhance_fin(), detect_fin(), and we_chat_decoder inside detect_fin()

def run_folder(folder_path):
    results = []

    # list all image files
    valid_ext = (".png", ".jpg", ".jpeg", ".bmp")
    files = [f for f in os.listdir(folder_path) if f.lower().endswith(valid_ext)]

    for fname in files:
        path = os.path.join(folder_path, fname)
        print(f"[PROCESS] {path}")

        img = cv2.imread(path)
        if img is None:
            print(f"[ERROR] Failed to read {path}")
            continue

        # --- RUN ENHANCEMENT ---
        enhanced = enhance_fin(img)

        # --- RUN DETECTION (your function already handles success/fail + deletion) ---
        qr = detect_fin(enhanced)   # returns string or empty

        if qr:
            results.append(qr)

    return results


if __name__ == "__main__":
    folder = "images"  # <--- set your folder
    all_qr = run_folder(folder)
    print("\n=== FINAL QR LIST ===")
    print(all_qr)
