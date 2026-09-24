import os
import cv2
import csv
import time
import traceback
import numpy as np
from datetime import datetime

# -------------------------
# Helpers
# -------------------------
def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def timestamp_seconds():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def save_meta_row(csv_path, row, header):
    newf = not os.path.exists(csv_path)
    with open(csv_path, "a", newline="") as f:
        w = csv.writer(f)
        if newf:
            w.writerow(header)
        w.writerow(row)

def compute_sharpness(img):
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return float(cv2.Laplacian(g, cv2.CV_64F).var())

# -------------------------
# ALIGNMENT helpers
# -------------------------
def align_ecc(ref_gray, img_gray, warp_mode=cv2.MOTION_AFFINE, number_of_iterations=2000, termination_eps=1e-6):
    """
    Align img_gray to ref_gray using ECC (works well for small wobble).
    Returns warp_matrix (2x3 for affine) and success flag.
    """
    # initialize warp matrix
    if warp_mode == cv2.MOTION_HOMOGRAPHY:
        warp_matrix = np.eye(3, 3, dtype=np.float32)
    else:
        warp_matrix = np.eye(2, 3, dtype=np.float32)

    criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, number_of_iterations, termination_eps)
    try:
        (cc, warp_matrix) = cv2.findTransformECC(ref_gray, img_gray, warp_matrix, warp_mode, criteria, inputMask=None, gaussFiltSize=5)
        return warp_matrix, True
    except Exception:
        return None, False

def warp_image(img, warp_matrix, dsize, warp_mode=cv2.MOTION_AFFINE):
    if warp_matrix is None:
        return None
    if warp_mode == cv2.MOTION_HOMOGRAPHY:
        aligned = cv2.warpPerspective(img, warp_matrix, dsize, flags=cv2.INTER_LINEAR + cv2.WARP_INVERSE_MAP)
    else:
        aligned = cv2.warpAffine(img, warp_matrix, dsize, flags=cv2.INTER_LINEAR + cv2.WARP_INVERSE_MAP)
    return aligned

def align_via_orb(ref_gray, img_gray):
    """Fallback: ORB + findHomography."""
    orb = cv2.ORB_create(2000)
    k1, d1 = orb.detectAndCompute(ref_gray, None)
    k2, d2 = orb.detectAndCompute(img_gray, None)
    if d1 is None or d2 is None:
        return None, False
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    matches = bf.match(d1, d2)
    if len(matches) < 8:
        return None, False
    matches = sorted(matches, key=lambda x: x.distance)[:200]
    pts1 = np.float32([k1[m.queryIdx].pt for m in matches]).reshape(-1, 1, 2)
    pts2 = np.float32([k2[m.trainIdx].pt for m in matches]).reshape(-1, 1, 2)
    H, mask = cv2.findHomography(pts2, pts1, cv2.RANSAC, 5.0)
    if H is None:
        return None, False
    return H, True

# -------------------------
# Burst capture + merge
# -------------------------
def burst_capture_and_merge(
    cap,
    n_frames=10,
    out_dir="captures",
    meta_csv="captures_meta.csv",
    log_file="capture_errors.log",
    keep_all=False,
    discard_blur_threshold=None,
    align_mode="ecc",   # "ecc" or "orb"
    merge_mode="median" # "median", "average", "mertens"
):
    """
    Capture n_frames from cap, align, merge, save result + metadata.
    Returns dict with status and file info.
    """
    ensure_dir(out_dir)
    meta_header = ["timestamp", "result_filename", "method", "n_frames", "sharpness_ref", "notes"]
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    result_filename = f"burst_{ts}.png"
    result_path = os.path.join(out_dir, result_filename)

    try:
        frames = []
        sharpness = []
        h, w = None, None

        # 1) capture frames fast
        for i in range(n_frames):
            ret, frame = cap.read()
            if not ret or frame is None:
                # small sleep and try again once (robustness)
                time.sleep(0.01)
                ret, frame = cap.read()
                if not ret or frame is None:
                    continue
            if h is None:
                h, w = frame.shape[:2]
            frames.append(frame.copy())
            sharpness.append(compute_sharpness(frame))
            time.sleep(0.01)  # tiny gap

        if len(frames) == 0:
            raise RuntimeError("No frames captured in burst.")

        # Optionally discard very blurry frames
        if discard_blur_threshold is not None:
            keep_idx = [i for i,s in enumerate(sharpness) if s >= discard_blur_threshold]
            if len(keep_idx) == 0:
                keep_idx = list(range(len(frames)))
            frames = [frames[i] for i in keep_idx]
            sharpness = [sharpness[i] for i in keep_idx]

        # Reference frame = the sharpest
        ref_idx = int(np.argmax(sharpness))
        ref = frames[ref_idx]
        ref_gray = cv2.cvtColor(ref, cv2.COLOR_BGR2GRAY)

        # Align all frames to ref
        aligned = []
        warp_mode = cv2.MOTION_AFFINE
        for i, f in enumerate(frames):
            if i == ref_idx:
                aligned.append(ref)
                continue

            img_gray = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)

            if align_mode == "ecc":
                warp, ok = align_ecc(ref_gray, img_gray, warp_mode=warp_mode)
                if ok:
                    al = warp_image(f, warp, (w, h), warp_mode=warp_mode)
                    if al is not None:
                        aligned.append(al)
                        continue
                # fallback to ORB if ECC fails
                H, ok2 = align_via_orb(ref_gray, img_gray)
                if ok2:
                    al = cv2.warpPerspective(f, H, (w, h), flags=cv2.INTER_LINEAR + cv2.WARP_INVERSE_MAP)
                    aligned.append(al)
                    continue
                # if both fail, append original (will degrade merge)
                aligned.append(f)
            else:
                # direct ORB
                H, ok2 = align_via_orb(ref_gray, img_gray)
                if ok2:
                    al = cv2.warpPerspective(f, H, (w, h), flags=cv2.INTER_LINEAR + cv2.WARP_INVERSE_MAP)
                    aligned.append(al)
                else:
                    aligned.append(f)

        # convert aligned list to numpy array (N,H,W,3)
        stack = np.stack([np.asarray(x, dtype=np.float32) for x in aligned], axis=0)

        # MERGE
        if merge_mode == "median":
            merged = np.median(stack, axis=0).astype(np.uint8)
        elif merge_mode == "average":
            merged = np.mean(stack, axis=0).astype(np.uint8)
        elif merge_mode == "mertens":
            merge_mertens = cv2.createMergeMertens()
            # Mertens expects float32 in 0..1
            imgs_f = [x.astype(np.float32)/255.0 for x in stack]
            res = merge_mertens.process(imgs_f)
            merged = np.clip(res*255.0, 0, 255).astype(np.uint8)
        else:
            # default to median
            merged = np.median(stack, axis=0).astype(np.uint8)

        # Save result
        cv2.imwrite(result_path, merged)

        # Save metadata row
        notes = ""
        meta_row = [timestamp_seconds(), result_filename, f"align={align_mode}|merge={merge_mode}", len(frames), round(float(sharpness[ref_idx]),2), notes]
        save_meta_row(meta_csv, meta_row, meta_header)

        return {
            "status": "OK",
            "result_path": result_path,
            "n_frames": len(frames),
            "ref_index": ref_idx,
            "ref_sharpness": float(sharpness[ref_idx])
        }

    except Exception as e:
        trace = traceback.format_exc()
        with open(log_file, "a") as lf:
            lf.write(f"[{timestamp_seconds()}] ERROR in burst_capture_and_merge: {trace}\n")
        return {"status": "ERROR", "error": str(e)}




cap = cv2.VideoCapture(1)              # your camera
res = burst_capture_and_merge(cap, n_frames=15,
                              align_mode="ecc",
                              merge_mode="median",
                              discard_blur_threshold=None)
print(res)

