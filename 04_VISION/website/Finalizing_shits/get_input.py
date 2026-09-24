# camera captures
# (pre)process frames,store in captures, save capture meta data in csv

'''
FLOW:
1.) take the camera instance and capture multiple frames ( N frames for now)
--> vary sharpness and click the best picture... basically preprocessing
2.) store the captures in a folder named captures with timestamp
3.) store the meta data in a csv file with columns:
4.) if any error occurs, handle exceptions and log them in a log file
5.) take care of store directory creation if not exists and meta data csv file creation if not exists


'''


import os
import csv
import cv2
import time
import traceback
from datetime import datetime
import numpy as np


# ==========================================================
# HELPERS
# ==========================================================
def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)


def ensure_csv(csv_path, header):
    """Create metadata CSV file if not exists."""
    new_file = not os.path.exists(csv_path)
    with open(csv_path, "a", newline="") as f:
        w = csv.writer(f)
        if new_file:
            w.writerow(header)


def log_error(err_msg, log_path="capture_errors.log"):
    """Append error traceback to log file."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_path, "a") as f:
        f.write(f"[{ts}] {err_msg}\n")


def compute_sharpness(frame):
    """Variance of Laplacian – higher is sharper."""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return cv2.Laplacian(gray, cv2.CV_64F).var()


# ==========================================================
# MAIN CAPTURE FUNCTION
# ==========================================================
def capture_best_frame(
    cap,
    num_frames=10,
    save_dir="captures",
    meta_csv="captures_meta.csv",
    log_file="capture_errors.log"
):
    try:
        ensure_dir(save_dir)
        header = ["timestamp", "filename", "sharpness", "width", "height"]
        ensure_csv(meta_csv, header)

        # Flush buffer
        for _ in range(3):
            cap.grab()

        samples = []

        for i in range(num_frames):

            cap.grab()                     # fast
            ret, frame = cap.retrieve()    # decode only once

            if not ret:
                continue

            sharp = compute_sharpness(frame)
            samples.append((sharp, frame))

        if not samples:
            raise RuntimeError("No frames captured.")

        # best frame
        samples.sort(key=lambda x: x[0], reverse=True)
        best_sharpness, best_frame = samples[0]
        h, w = best_frame.shape[:2]

        ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"{ts}.png"
        filepath = os.path.join(save_dir, filename)
        cv2.imwrite(filepath, best_frame)

        with open(meta_csv, "a", newline="") as f:
            w_csv = csv.writer(f)
            w_csv.writerow([ts, filename, round(best_sharpness, 2), w, h])

        return {
            "status": "OK",
            "timestamp": ts,
            "filename": filename,
            "sharpness": best_sharpness,
            "resolution": (w, h),
            "path": filepath
        }

    except Exception as e:
        trace = traceback.format_exc()
        log_error(trace, log_file)
        return {"status": "ERROR", "error": str(e)}



if __name__ == "__main__":
    # Open camera (0,1,2 depending on your device)
    cap = cv2.VideoCapture(1)

    if not cap.isOpened():
        print("❌ ERROR: Camera not opening. Try a different index like 1 or 2.")
        exit()

    # Run capture
    result = capture_best_frame(
        cap,
        num_frames=10,          # number of frames to capture quickly
        save_dir="captures",    # where images will be stored
        meta_csv="captures_meta.csv",
        log_file="capture_errors.log"
    )

    cap.release()

    print("RESULT =>", result)
