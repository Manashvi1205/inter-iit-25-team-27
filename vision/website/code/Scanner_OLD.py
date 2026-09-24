# Scanner.py
#Auther: Mahesh (iek)

from typing import List, Tuple, Optional, Callable, Dict, Any
import os
import time
import json
import datetime
import cv2
import numpy as np
import csv
from collections import defaultdict

# import servo helpers from your servo_lib
from servoBoard import ServoBoard, servo_move_to, get_pose_list

class Scanner:
    def __init__(
        self,
        camera_candidates: Tuple[int, ...] = (0, 1, 2),
        width: int = 1920,
        height: int = 1080,
        fourcc: str = "MJPG",
        servo_port: str = "/dev/ttyUSB0",
        csv_path: str = "scan_results.csv",
        unified_json: str = "output.json",
        model_dir: str = "wechat_qrcode_models",
        num_frames: int = 10,
        top_k: int = 3,
        merge_thresh_pct: float = 3.0,
        aggressive_aug: bool = True,
        wait_after_move: float = 0.25,
        debug: bool = True,
        dry_run: bool = False,

        # NEW LOGGING SETTINGS
        log_print: bool = True,
        log_file: bool = False,
        log_file_path: str = "scanner.log"
    ):
        """
        Auto-initializes hardware & detector on instantiation.
        """

        # logging flags
        self.log_print = log_print
        self.log_file = log_file
        self.log_file_path = log_file_path

        # config
        self.camera_candidates = camera_candidates
        self.width = width
        self.height = height
        self.fourcc = fourcc
        self.servo_port = servo_port
        self.csv_path = csv_path
        self.unified_json = unified_json
        self.model_dir = model_dir
        self.num_frames = num_frames
        self.top_k = top_k
        self.merge_thresh_pct = merge_thresh_pct
        self.aggressive_aug = aggressive_aug
        self.wait_after_move = wait_after_move
        self.debug = debug
        self.dry_run = dry_run

        # runtime
        self.cap = None
        self.camera_idx = None
        self.servo = None
        self.detector = None

        self.aggregated_results = []

        self.loggg("Scanner initializing…", "INFO")

        # auto init
        self._init_ALL()

        self.loggg("Scanner initialized successfully.", "SUCCESS")

    # -------------------------------------------------------------------------
    # Custom Logging System
    # -------------------------------------------------------------------------
    def loggg(self, msg: str, level: str = "INFO"):
        prefix = {
            "INFO": "[INFO]",
            "WARN": "[WARN]",
            "ERROR": "[ERROR]",
            "SUCCESS": "[SUCCESS]"
        }.get(level.upper(), "[INFO]")

        final_msg = f"{prefix} {msg}"

        if self.log_print:
            print(final_msg)

        if self.log_file:
            try:
                with open(self.log_file_path, "a") as f:
                    f.write(final_msg + "\n")
            except:
                pass

    # -------------------------------------------------------------------------
    # INIT HELPERS
    # -------------------------------------------------------------------------
    def _init_camera(self):
        last_errs = []
        for idx in self.camera_candidates:
            cap = cv2.VideoCapture(idx, cv2.CAP_V4L2)
            if not cap.isOpened():
                last_errs.append(f"device {idx} not opened")
                try: cap.release()
                except: pass
                continue

            cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*self.fourcc))
            cap.set(cv2.CAP_PROP_FPS, 30)

            time.sleep(0.15)
            ret, _ = cap.read()
            if not ret:
                last_errs.append(f"device {idx} opened but read failed")
                try: cap.release()
                except: pass
                continue

            self.cap = cap
            self.camera_idx = idx
            self.loggg(f"Camera initialized on index {idx}", "SUCCESS")
            return True

        self.loggg("No usable camera found: " + "; ".join(last_errs), "ERROR")
        raise SystemExit("Camera initialization failed")

    def _init_detector(self):
        try:
            detect_proto = os.path.join(self.model_dir, "detect.prototxt")
            detect_model = os.path.join(self.model_dir, "detect.caffemodel")
            sr_proto     = os.path.join(self.model_dir, "sr.prototxt")
            sr_model     = os.path.join(self.model_dir, "sr.caffemodel")
            self.detector = cv2.wechat_qrcode_WeChatQRCode(
                detect_proto, detect_model, sr_proto, sr_model
            )
            self.loggg("WeChat QR detector loaded", "SUCCESS")
        except Exception as e:
            self.loggg(f"ERROR initializing WeChat QR detector: {e}", "ERROR")
            self.detector = None

    def _init_servo(self):
        if self.dry_run:
            self.loggg("Dry-run mode: servo disabled.", "WARN")
            self.servo = None
            return
        try:
            self.servo = ServoBoard(self.servo_port)
            self.loggg("Servo initialized", "SUCCESS")
        except Exception as e:
            self.loggg(f"Servo init failed: {e}", "WARN")
            self.servo = None

    def _init_ALL(self):
        self._init_camera()
        self._init_detector()
        self._init_servo()

    # -------------------------------------------------------------------------
    # Processing Helpers (unchanged)
    # -------------------------------------------------------------------------
    @staticmethod
    def compute_sharpness(img):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        return cv2.Laplacian(gray, cv2.CV_64F).var()

    @staticmethod
    def sharpen_image(img):
        kernel = np.array([[0,-1,0],[-1,5,-1],[0,-1,0]])
        return cv2.filter2D(img, -1, kernel)

    @staticmethod
    def apply_clahe(img):
        yuv = cv2.cvtColor(img, cv2.COLOR_BGR2YUV)
        y = yuv[:,:,0]
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        yuv[:,:,0] = clahe.apply(y)
        return cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR)

    @staticmethod
    def gamma_correction(img, gamma=1.15):
        inv = 1.0/gamma
        table = np.array([((i/255.0)**inv)*255 for i in np.arange(256)]).astype("uint8")
        return cv2.LUT(img, table)

    def make_augmentations(self, img):
        out = [("orig",img),
               ("shp",self.sharpen_image(img))]
        if self.aggressive_aug:
            out += [
                ("clahe", self.apply_clahe(img)),
                ("g1.15", self.gamma_correction(img))
            ]
        return out

    def detect_on_image(self, img):
        if img is None or self.detector is None:
            return []
        try:
            decoded, pts = self.detector.detectAndDecode(img)
        except Exception as e:
            self.loggg(f"Detector error: {e}", "ERROR")
            return []

        results = []
        h, w = img.shape[:2]

        if pts is None or len(pts)==0:
            return results

        for idx, quad in enumerate(pts):
            q = np.array(quad).reshape(4,2).astype(float)
            cx = float(np.mean(q[:,0]))
            cy = float(np.mean(q[:,1]))
            cx_pct = (cx/w)*100
            cy_pct = (cy/h)*100

            payload = ""
            if decoded is not None and idx < len(decoded):
                payload = decoded[idx]

            quad_pixels = [(int(x),int(y)) for x,y in q]
            results.append((payload,cx_pct,cy_pct,quad_pixels))
        return results

    def merge_detections(self, raw):
        clusters = []
        for payload, cx, cy, bbox in raw:
            placed = False
            for c in clusters:
                if c["payload"] == payload:
                    dist = np.hypot(c["cx"]-cx, c["cy"]-cy)
                    if dist <= self.merge_thresh_pct:
                        old = c["count"]
                        c["cx"] = (c["cx"]*old + cx)/(old+1)
                        c["cy"] = (c["cy"]*old + cy)/(old+1)
                        c["count"] = old+1
                        if c["bbox"] is None and bbox is not None:
                            c["bbox"] = bbox
                        placed=True
                        break
            if not placed:
                clusters.append({
                    "payload":payload,
                    "cx":cx,
                    "cy":cy,
                    "count":1,
                    "bbox":bbox
                })

        merged = []
        for c in clusters:
            merged.append({
                "payload":c["payload"],
                "cx_pct":round(c["cx"],2),
                "cy_pct":round(c["cy"],2),
                "bbox":c["bbox"]
            })
        return merged

    # -------------------------------------------------------------------------
    # SAVE HELPERS (unchanged)
    # -------------------------------------------------------------------------
    def save_debug_outputs(self, raw, annotated, detections, level_id):
        if not self.debug:
            return
        out_dir = f"debug/level_{level_id}"
        os.makedirs(out_dir, exist_ok=True)

        ts = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        cv2.imwrite(os.path.join(out_dir, f"raw_{ts}.png"), raw)
        cv2.imwrite(os.path.join(out_dir, f"annotated_{ts}.png"), annotated)

        json_dets = [{"payload":d["payload"],
                      "cx_pct":d["cx_pct"],
                      "cy_pct":d["cy_pct"]} for d in detections]

        meta = {
            "timestamp":ts,
            "level":level_id,
            "device":self.camera_idx,
            "detections":json_dets
        }
        with open(os.path.join(out_dir, f"meta_{ts}.json"),"w") as f:
            json.dump(meta,f,indent=2)

    def save_csv_rows(self, detections):
        header = ["timestamp","payload","level","h","v","cx_pct","cy_pct"]
        exists = os.path.exists(self.csv_path)

        with open(self.csv_path,"a",newline="") as f:
            w = csv.writer(f)
            if not exists:
                w.writerow(header)
            ts = datetime.datetime.now().isoformat()
            for d in detections:
                w.writerow([
                    ts, d.get("payload",""), d.get("level"),
                    d.get("h"), d.get("v"),
                    d.get("cx_pct"), d.get("cy_pct")
                ])

    def save_json_results(self, detections, level_id, out_dir="results_json"):
        os.makedirs(out_dir, exist_ok=True)
        out = []
        for d in detections:
            out.append({
                "payload":d["payload"],
                "level":level_id,
                "h":d["h"],
                "v":d["v"],
                "centroid":[d["cx_pct"], d["cy_pct"]]
            })

        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(out_dir, f"level_{level_id}_{ts}.json")
        with open(path,"w") as f:
            json.dump(out,f,indent=2)

    # -------------------------------------------------------------------------
    # POSE → LEVEL SCANNING
    # -------------------------------------------------------------------------
    def scan_shelf_level(self, level_id, debug=False, 
                         num_frames=None, top_k=None, aggressive_augment=None):
        
        if num_frames is None: num_frames=self.num_frames
        if top_k is None: top_k=self.top_k
        if aggressive_augment is None: aggressive_augment=self.aggressive_aug

        samples=[]
        for i in range(num_frames):
            ret,frame=self.cap.read()
            if not ret or frame is None:
                continue
            s=self.compute_sharpness(frame)
            samples.append((s,frame))
            time.sleep(0.02)

        if not samples:
            return []

        samples.sort(key=lambda x:x[0], reverse=True)
        top_samples = samples[:max(1,min(top_k,len(samples)))]

        best_frame = top_samples[0][1].copy()
        raw_dets=[]
        annotated = best_frame.copy()

        for sharpness_val,frame in top_samples:
            for tag,aug in self.make_augmentations(frame):
                dets = self.detect_on_image(aug)
                for payload,cx,cy,bbox in dets:
                    raw_dets.append((payload,cx,cy,bbox))
                    x = int((cx/100)*annotated.shape[1])
                    y = int((cy/100)*annotated.shape[0])
                    cv2.circle(annotated,(x,y),4,(0,255,0),-1)

        merged = self.merge_detections(raw_dets)
        self.save_debug_outputs(best_frame,annotated,merged,level_id)
        return merged

    def scan_pose(self, h, v, level_id, debug=False):
        ok, captured = True, None

        if self.servo is not None:
            ok, captured = servo_move_to(
                self.servo, h=h, v=v, cap=self.cap,
                neutral_h=90, neutral_v=90,
                h_delta=30, v_delta=25,
                wait_after_move=self.wait_after_move,
                capture_after_move=True
            )
        else:
            if self.cap is not None:
                ret,f=self.cap.read()
                if ret and f is not None:
                    captured=f.copy()
            else:
                self.loggg("No servo and no camera available.", "ERROR")
                return []

        if not ok:
            self.loggg(f"servo_move_to failed for (h={h}, v={v})", "WARN")

        # detection path unchanged...
        if captured is None:
            merged = self.scan_shelf_level(level_id)
        else:
            samples=[]
            s_cap=self.compute_sharpness(captured)
            samples.append((s_cap,captured))

            for i in range(max(0,self.num_frames-1)):
                ret,frame=self.cap.read()
                if not ret or frame is None: continue
                s=self.compute_sharpness(frame)
                samples.append((s,frame))
                time.sleep(0.02)

            samples.sort(key=lambda x:x[0], reverse=True)
            top_samples = samples[:max(1,min(self.top_k,len(samples)))]

            best_frame = top_samples[0][1].copy()
            raw=[]
            annotated=best_frame.copy()

            for _,frame in top_samples:
                for _,aug in self.make_augmentations(frame):
                    dets = self.detect_on_image(aug)
                    for payload,cx,cy,bbox in dets:
                        raw.append((payload,cx,cy,bbox))

            merged = self.merge_detections(raw)
            self.save_debug_outputs(best_frame,annotated,merged,level_id)

        out=[]
        for m in merged:
            out.append({
                "payload":m["payload"],
                "cx_pct":m["cx_pct"],
                "cy_pct":m["cy_pct"],
                "bbox":m["bbox"],
                "h":h,
                "v":v,
                "level":level_id
            })
        return out

    def scan_level(self, level_id, is_top=False, is_bottom=False):
        poses = get_pose_list(is_top=is_top, is_bottom=is_bottom)

        all_d=[]
        for (h,v) in poses:
            dets = self.scan_pose(h,v,level_id)
            all_d.extend(dets)

        raw=[(d["payload"], d["cx_pct"], d["cy_pct"], d["bbox"]) for d in all_d]
        merged = self.merge_detections(raw)

        cleaned=[]
        for m in merged:
            cleaned.append({
                "payload":m["payload"],
                "cx_pct":m["cx_pct"],
                "cy_pct":m["cy_pct"],
                "bbox":m["bbox"],
                "h":None,
                "v":None,
                "level":level_id
            })

        if all_d:
            self.save_csv_rows(all_d)
        self.save_json_results(cleaned,level_id)

        self.aggregated_results.extend(cleaned)

        with open(self.unified_json,"w") as f:
            json.dump(self.aggregated_results,f,indent=2)

        self.loggg(f"Level {level_id} scan complete.", "SUCCESS")

        return cleaned

    # -------------------------------------------------------------------------
    # SERVO UTILS
    # -------------------------------------------------------------------------
    def open_servo_debug_terminal(self, baud=115200):
        from servoBoard import servo_debug_terminal
        servo_debug_terminal(self.servo_port, baud=baud)

    def calibrate_servo(self, servo_id):
        if self.servo is None:
            self.loggg("calibrate_servo: servo not initialized.", "WARN")
            return
        self.servo.calibrate(servo_id)

    def get_servo_positions(self):
        if self.servo is None:
            return {}
        return self.servo.get_positions()

    # -------------------------------------------------------------------------
    # CLEANUP
    # -------------------------------------------------------------------------
    def close(self):
        try:
            if self.cap is not None:
                self.cap.release()
                self.cap=None
        except: pass

        try:
            if self.servo is not None:
                try:
                    self.servo.move(0,90)
                    self.servo.move(1,90)
                    time.sleep(0.25)
                except: pass
                self.servo.close()
                self.servo=None
        except: pass

        self.loggg("Scanner closed.", "INFO")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
