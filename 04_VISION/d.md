# Warehouse QR Scanning System - Complete Technical Overview

## System Architecture Overview

This is a **real-time warehouse inventory management system** that uses computer vision to detect and process 
QR codes on shelves, mapping them to global coordinates via SLAM integration.

---

## 1. High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        WAREHOUSE ENVIRONMENT                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │ Rack R01 │  │ Rack R02 │  │ Rack R03 │  │ Rack R04 │       │
│  │ ┌──────┐ │  │ ┌──────┐ │  │ ┌──────┐ │  │ ┌──────┐ │       │
│  │ │ QR   │ │  │ │ QR   │ │  │ │ QR   │ │  │ │ QR   │ │       │
│  │ └──────┘ │  │ └──────┘ │  │ └──────┘ │  │ └──────┘ │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     HARDWARE LAYER                               │
│  ┌────────────────┐  ┌────────────────┐  ┌──────────────────┐  │
│  │  USB Camera    │  │  Servo Motors  │  │  LED Controller  │  │
│  │  (640x480)     │  │  (Pan/Tilt)    │  │  (Status LEDs)   │  │
│  └────────┬───────┘  └────────┬───────┘  └────────┬─────────┘  │
└───────────┼──────────────────┼───────────────────┼─────────────┘
            │                  │                   │
            ▼                  ▼                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                   SOFTWARE LAYER (Python)                        │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │              visionNode (Orchestrator)                      │ │
│  │  • Singleton coordinator                                   │ │
│  │  • LED status control                                      │ │
│  │  • Multi-angle scanning logic                              │ │
│  └────────────────┬───────────────────────────────────────────┘ │
│                   │                                              │
│       ┌───────────┴───────────┐                                 │
│       ▼                       ▼                                 │
│  ┌─────────┐           ┌───────────┐                           │
│  │ Scanner │           │ Processor │                            │
│  │ Module  │           │  Worker   │                            │
│  └─────────┘           └───────────┘                            │
└─────────────────────────────────────────────────────────────────┘
            │                       │
            ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                     DATA LAYER                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Raw Images   │  │ Inventory DB │  │  Remote API Server   │  │
│  │  (PNG)       │  │  (CSV)       │  │  (HTTP POST)         │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Hardware Subsystems

### 2.1 Camera System
```
┌────────────────────────────────────────┐
│         USB Camera (V4L2)              │
│  • Resolution: 640x480 pixels          │
│  • Codec: MJPEG                        │
│  • FPS: 30                             │
│  • Backend: CAP_V4L2 (Linux)          │
└────────────────────────────────────────┘
```

### 2.2 Servo System
```
┌────────────────────────────────────────┐
│      2-Axis Servo Pan/Tilt Mount      │
│                                        │
│  Servo 0 (Horizontal):                │
│  • Range: 0-180°                      │
│  • Positions: Left(0), Center(1), Right(2) │
│                                        │
│  Servo 1 (Vertical):                  │
│  • Range: 0-180°                      │
│  • Positions: Down(0), Front(1), Up(2) │
│                                        │
│  Control: Serial @ 115200 baud        │
└────────────────────────────────────────┘
```

### 2.3 LED System
```
┌────────────────────────────────────────┐
│       RGB LED Status Indicators        │
│  • Signal Yellow: Warning              │
│  • Signal Red: Danger                  │
│  • Signal Green: Safe/Complete         │
│  • Signal Blue: Mandatory              │
│  • White: Flashlight mode              │
└────────────────────────────────────────┘
```

---

## 3. Complete Control Flow

### 3.1 System Initialization Sequence

```
START
  │
  ├─► [1] Load YAML Configuration
  │     │
  │     ├── camera_cfg (resolution, FPS, codec)
  │     ├── processor_cfg (thresholds, paths)
  │     ├── scanner_cfg (servo ports, LED settings)
  │     └── session_cfg (session_id, API URL)
  │
  ├─► [2] Initialize visionNode Singleton
  │     │
  │     ├── Create log directories
  │     ├── Initialize Scanner subsystem
  │     │     ├── Try cameras [0, 1, 2] in sequence
  │     │     ├── Set camera properties (width, height, FPS)
  │     │     ├── Warmup period (150ms)
  │     │     └── Initialize servo board (optional)
  │     │
  │     └── Launch Processor Worker (multiprocessing)
  │           ├── Create Queue (maxsize=20)
  │           ├── Create Stop Event
  │           └── Spawn background process
  │
  └─► [3] System Ready
        • Scanner: Active on camera device
        • Processor: Waiting for jobs
        • Servos: At neutral position (H=1, V=1)
```

---

### 3.2 Main Scanning Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                    CAPTURE REQUEST                               │
│  visionNode.capture(x, y, isTop, isBottom)                      │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
        ┌──────────────────────────────┐
        │  Determine Scan Strategy     │
        │  • Normal: 1 angle           │
        │  • Top: 2 angles (1→2)       │
        │  • Bottom: 2 angles (1→0)    │
        │  • Full: 3 angles (0→1→2)    │
        └──────────┬───────────────────┘
                   │
                   ▼
        ┌──────────────────────────────┐
        │   FOR EACH ANGLE:            │
        │   1. Move Servo              │
        │   2. Wait 250ms              │
        │   3. Capture Frame           │
        └──────────┬───────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                  FRAME CAPTURE (Scanner)                         │
│                                                                  │
│  [1] Burst Capture (10 frames)                                  │
│      ├── Flush camera buffer (3 frames)                         │
│      ├── Use grab() for fast acquisition                        │
│      └── Use retrieve() to decode frames                        │
│                                                                  │
│  [2] Sharpness Analysis                                         │
│      ├── Convert to grayscale                                   │
│      ├── Apply Laplacian operator                               │
│      ├── Compute variance                                       │
│      └── Select frame with highest score                        │
│                                                                  │
│  [3] Save Best Frame                                            │
│      ├── Filename: capture_YYYY-MM-DD_HH-MM-SS.png             │
│      ├── Save to: /data/raw_captures/                          │
│      └── Log metadata to CSV                                    │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
        ┌──────────────────────────────┐
        │   Queue for Processing       │
        │   • path: image filepath     │
        │   • x0: SLAM x coordinate    │
        │   • y0: SLAM y coordinate    │
        │   • orientation: 0/1/2       │
        └──────────┬───────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│            PROCESSOR WORKER (Background Process)                 │
│                                                                  │
│  [1] Load Image                                                 │
│      └── cv2.imread(path)                                       │
│                                                                  │
│  [2] Geometric Rectification                                    │
│      ├── Map orientation → (theta, phi)                         │
│      │   • 0 (down):  theta=180°, phi=90°                      │
│      │   • 1 (front): theta=90°,  phi=90°                      │
│      │   • 2 (up):    theta=0°,   phi=90°                      │
│      │                                                          │
│      ├── Build rotation matrix R                                │
│      ├── Project each pixel onto wall plane                     │
│      └── Create rectified image                                 │
│                                                                  │
│  [3] QR Detection                                               │
│      ├── Run YOLO-based QRDetector                             │
│      ├── Extract bounding boxes [x1,y1,x2,y2]                  │
│      ├── Calculate centroids (u_center, v_center)              │
│      └── Crop with padding                                      │
│                                                                  │
│  [4] QR Enhancement & Decoding                                  │
│      ├── Resize to 400x400                                      │
│      ├── Apply CLAHE contrast enhancement                       │
│      ├── Apply Unsharp Mask                                     │
│      ├── Binary threshold                                       │
│      └── WeChat QR decoder                                      │
│                                                                  │
│  [5] Coordinate Transformation                                  │
│      ├── UV (pixels) → Camera Frame (meters)                   │
│      │   x_cam = (u/ppm) + x_cam_origin                        │
│      │   y_cam = y_cam_origin - (v/ppm)                        │
│      │                                                          │
│      └── Camera Frame → Global Frame                            │
│          global_x = x_cam + x_offset (SLAM)                    │
│          global_y = y_cam + y_offset (SLAM)                    │
│                                                                  │
│  [6] Inventory Management                                       │
│      ├── Parse payload: "R03_S4_ITM240"                        │
│      │   → rack="R03", shelf="S4", item="ITM240"              │
│      │                                                          │
│      ├── Read existing inventory CSV                            │
│      │                                                          │
│      ├── Duplicate Detection                                    │
│      │   • Same item + Same location → IGNORE                  │
│      │   • Same item + New location → NEW ENTRY                │
│      │   • New item → NEW ENTRY                                │
│      │                                                          │
│      ├── Save to inventory.csv                                  │
│      └── POST to remote API                                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. Coordinate System Transformations

### 4.1 Three Coordinate Frames

```
┌────────────────────────────────────────────────────────────────┐
│  [1] UV FRAME (Image Pixels)                                   │
│                                                                 │
│      (0,0) ────────► u                                         │
│        │                                                        │
│        │   ┌───────────────┐                                   │
│        │   │               │                                   │
│        ▼   │    QR Code    │                                   │
│        v   │   @ (u,v)     │                                   │
│            │               │                                   │
│            └───────────────┘                                   │
│                                                                 │
│  Origin: Top-left corner                                       │
│  Units: Pixels                                                 │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│  [2] CAMERA FRAME (3D Space)                                   │
│                                                                 │
│                     y_cam (up)                                 │
│                       ▲                                         │
│                       │                                         │
│            ┌──────────┼──────────┐                            │
│            │          │          │                             │
│            │     Wall Plane      │                             │
│            │     (d = 0.2m)      │                             │
│            │          │          │                             │
│  ◄─────────┼──────────●──────────┼──────► x_cam (right)      │
│            │     Camera Optical  │                             │
│            │       Center        │                             │
│            └─────────────────────┘                             │
│                                                                 │
│  Origin: Camera optical center projected onto wall             │
│  Units: Meters                                                 │
│  Distance to wall: d = 0.20m                                   │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│  [3] GLOBAL FRAME (SLAM Coordinates)                           │
│                                                                 │
│                                                                 │
│         Warehouse Floor Plan                                   │
│                                                                 │
│    (x_offset, y_offset) ───► Global Origin                    │
│           │                                                     │
│           ▼                                                     │
│    ┌──────────┐  ┌──────────┐  ┌──────────┐                  │
│    │ Rack 01  │  │ Rack 02  │  │ Rack 03  │                  │
│    │          │  │          │  │          │                  │
│    │  QR @    │  │          │  │          │                  │
│    │ (gx, gy) │  │          │  │          │                  │
│    └──────────┘  └──────────┘  └──────────┘                  │
│                                                                 │
│  Origin: SLAM/Odometry world origin                            │
│  Units: Meters                                                 │
│  Transformation: (global_x, global_y) = (x_cam, y_cam) +       │
│                  (x_offset, y_offset)                          │
└────────────────────────────────────────────────────────────────┘
```

### 4.2 Transformation Pipeline

```python
# STEP 1: UV → Camera Frame
# ─────────────────────────────────────
# 1. Get camera ray direction
ray_cam = [(u - c_x)/f_x, (v - c_y)/f_y, 1.0]

# 2. Apply rotation matrix (camera orientation)
R = rotation_matrix(theta, phi)
ray_world = R @ ray_cam

# 3. Intersect ray with wall plane at distance d
t = d / ray_world[1]  # y-component
x_cam = t * ray_world[0]
y_cam = t * ray_world[2]

# STEP 2: Camera Frame → Global Frame
# ─────────────────────────────────────
global_x = x_cam + x_offset  # SLAM X offset
global_y = y_cam + y_offset  # SLAM Y offset
```

---

## 5. Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    INPUT LAYER                                   │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ SLAM System  │  │  Scan Cmd    │  │   Camera Hardware    │  │
│  │ (x, y, θ)    │  │ (isTop/Bot)  │  │   (Raw Frames)       │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────────────┘  │
└─────────┼──────────────────┼──────────────────┼──────────────────┘
          │                  │                  │
          ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                 PROCESSING LAYER                                 │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                   visionNode                                │ │
│  │  • Coordinate visionNode.capture()                         │ │
│  │  • LED status control                                       │ │
│  │  • Multi-angle logic                                        │ │
│  └──────┬─────────────────────────────────────────────────────┘ │
│         │                                                        │
│         ├──► Scanner.capture_best_frame()                       │
│         │      ├── Burst capture (10 frames)                    │
│         │      ├── Sharpness selection                          │
│         │      └── Save to disk                                 │
│         │                                                        │
│         └──► Processor Worker (background)                      │
│                ├── Load image                                   │
│                ├── Geometric rectification                      │
│                ├── QR detection (YOLO)                          │
│                ├── QR decoding (WeChat)                         │
│                ├── Coordinate transform                         │
│                └── Inventory update                             │
│                                                                  │
└─────────┬───────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────┐
│                   OUTPUT LAYER                                   │
│                                                                  │
│  ┌──────────────────┐  ┌──────────────────┐  ┌───────────────┐ │
│  │  inventory.csv   │  │  Remote API      │  │  Log Files    │ │
│  │                  │  │  POST /session   │  │  (Debug)      │ │
│  │  session_id      │  │                  │  │               │ │
│  │  timestamp       │  │  {               │  │               │ │
│  │  payload         │  │    round_id,     │  │               │ │
│  │  rack            │  │    timestamp,    │  │               │ │
│  │  shelf           │  │    payload,      │  │               │ │
│  │  item            │  │    shelf_status  │  │               │ │
│  │  global_x        │  │  }               │  │               │ │
│  │  global_y        │  │                  │  │               │ │
│  └──────────────────┘  └──────────────────┘  └───────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## 6. Detailed Module Breakdown

### 6.1 visionNode.py (Orchestrator)

**Purpose**: High-level coordinator that manages the entire scanning workflow

**Key Responsibilities**:
```
├── System Initialization
│   ├── Load configuration
│   ├── Initialize Scanner hardware
│   └── Launch Processor worker
│
├── Scan Strategy Execution
│   ├── Single-angle capture
│   ├── Top-sweep (normal → up)
│   ├── Bottom-sweep (normal → down)
│   └── Full-sweep (down → normal → up)
│
├── LED Status Control
│   ├── Warning (yellow)
│   ├── Danger (red)
│   ├── Safe (green)
│   └── Flashlight (white)
│
└── Worker Management
    ├── Queue management
    ├── Job distribution
    └── Graceful shutdown
```

**Key Methods**:
- `capture(x, y, isTop, isBottom)` - Main scanning API
- `capture_once(x, y, orientation)` - Single frame capture
- `led(color, level, index)` - LED control
- `shutdown()` - Clean resource cleanup

---

### 6.2 Scanner.py (Hardware Interface)

**Purpose**: Direct hardware control for camera and servos

**Key Responsibilities**:
```
├── Camera Management
│   ├── Device selection (tries [0,1,2])
│   ├── Property configuration
│   ├── Burst capture
│   └── Sharpness analysis (Laplacian variance)
│
├── Servo Control
│   ├── Position commands
│   ├── Calibration
│   └── Status queries
│
└── File Management
    ├── Image saving
    ├── Metadata logging (CSV)
    └── Error logging
```

**Burst Capture Algorithm**:
```python
1. Flush buffer (3 frames)
2. FOR i in range(10):
     - grab() frame (fast)
     - retrieve() frame (decode)
     - compute sharpness
     - if sharpness > best:
         save as best_frame
3. Save best_frame to disk
4. Log metadata
```

---

### 6.3 Processor.py (Vision Pipeline)

**Purpose**: Image processing and QR analysis

**Key Responsibilities**:
```
├── Geometric Rectification
│   ├── Orientation → angles
│   ├── Build rotation matrix
│   ├── Project pixels to wall
│   └── Create rectified image
│
├── QR Detection
│   ├── YOLO-based detector
│   ├── Bounding box extraction
│   ├── Centroid calculation
│   └── ROI cropping
│
├── QR Enhancement
│   ├── Resize to 400x400
│   ├── CLAHE (contrast)
│   ├── Unsharp masking
│   └── Binary threshold
│
├── QR Decoding
│   └── WeChat QR detector
│
├── Coordinate Transformation
│   ├── UV → Camera frame
│   └── Camera → Global frame
│
└── Inventory Management
    ├── Payload parsing
    ├── Duplicate detection
    ├── CSV storage
    └── API posting
```

**QR Enhancement Pipeline**:
```
Input Image
    │
    ├─► Resize (400x400, LANCZOS4)
    │
    ├─► CLAHE (clipLimit=2.0, tileSize=8x8)
    │
    ├─► Unsharp Mask
    │     gaussian = GaussianBlur(σ=2.0)
    │     sharpened = 1.5*enhanced - 0.5*gaussian
    │
    ├─► Binary Threshold (threshold=140)
    │
    └─► WeChat QR Decoder
          └─► Payload String
```

---

### 6.4 servoBoard.py (Servo Driver)

**Purpose**: Low-level servo communication

**Key Features**:
```
├── Serial Communication (115200 baud)
├── Servo Commands
│   ├── move(id, angle)
│   ├── calibrate(id)
│   └── get_positions()
│
├── LED Control
│   ├── RGB + brightness
│   ├── Signal colors
│   └── Flash modes
│
└── Camera Helpers
    ├── set_camera_orientation()
    ├── servo_move_to()
    └── get_pose_list()
```

---

## 7. Complete Scanning Workflow Example

```
┌─────────────────────────────────────────────────────────────────┐
│  USER REQUEST: Scan shelf at (x=2.5m, y=1.0m) with TOP sweep   │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
        visionNode.capture(x=2.5, y=1.0, isTop=True, isBottom=False)
                       │
                       ├──► LED: Yellow (Scanning)
                       │
                       ├──► Move servo to (H=1, V=1)
                       │    Wait 250ms
                       │    Scanner.capture_best_frame()
                       │      ├─► Burst: 10 frames
                       │      ├─► Select sharpest
                       │      └─► Save: capture_2024-12-06_14-30-15.png
                       │    Queue job: {path, x=2.5, y=1.0, ori=1}
                       │
                       ├──► Move servo to (H=1, V=2)
                       │    Wait 250ms
                       │    Scanner.capture_best_frame()
                       │      └─► Save: capture_2024-12-06_14-30-16.png
                       │    Queue job: {path, x=2.5, y=1.0, ori=2}
                       │
                       ├──► Move servo back to (H=1, V=1)
                       │
                       └──► LED: Green (Complete)

            [Background Processor Worker processes queued jobs]

        FOR EACH QUEUED JOB:
            │
            ├─► Load image
            │
            ├─► Rectify to camera frame
            │     • orientation=1 → theta=90°, phi=90°
            │     • Project 640x480 → rectified image
            │
            ├─► Detect QR codes
            │     • YOLO finds 3 QR codes
            │     • Bounding boxes: [(x1,y1,x2,y2), ...]
            │
            ├─► FOR EACH QR:
            │     ├─► Enhance (CLAHE + Unsharp + Threshold)
            │     ├─► Decode: "R03_S2_ITM145"
            │     ├─► Parse: rack=R03, shelf=S2, item=ITM145
            │     ├─► Transform coordinates
            │     │     UV (320, 240) → Camera (0.05, 0.12)
            │     │     → Global (2.55, 1.12)
            │     │
            │     ├─► Check duplicates
            │     │     • Distance = 0.03m < threshold
            │     │     → IGNORE (already scanned)
            │     │
            │     └─► Next QR...
            │
            ├─► Decode: "R03_S3_ITM201"
            │     • Global coords: (2.57, 1.35)
            │     • No duplicates found
            │     → NEW ENTRY
            │     → Save to inventory.csv
            │     → POST to API
            │
            └─► Processing complete

        LED: Off (Idle)
```

---

## 8. Performance Characteristics

```
┌─────────────────────────────────────────────────────────────────┐
│                      TIMING ANALYSIS                             │
├─────────────────────────────────────────────────────────────────┤
│  Servo Movement:          ~250ms per angle change                │
│  Burst Capture:           ~330ms (10 frames @ 30fps)            │
│  Image Save:              ~50ms (PNG compression)                │
│  Queue Handoff:           ~1ms                                   │
│  ────────────────────────────────────────────────────────────── │
│  Single Capture Total:    ~630ms                                 │
│  Top Sweep (2 angles):    ~1260ms                                │
│  Full Sweep (3 angles):   ~1890ms                                │
│                                                                  │
│  Processing (per image):                                         │
│    - Rectification:       ~50ms                                  │
│    - QR Detection:        ~100ms                                 │
│    - QR Decoding:         ~80ms per QR                          │
│    - Coordinate transform: ~1ms                                  │
│    - Database update:     ~10ms                                  │
│  ────────────────────────────────────────────────────────────── │
│  Total (1 QR):            ~240ms                                 │
│  Total (3 QRs):           ~400ms                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 9. Error Handling & Robustness

```
┌─────────────────────────────────────────────────────────────────┐
│                    ERROR HANDLING STRATEGY                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Camera Failures:                                                │
│    → Try multiple device indices [0, 1, 2]                      │
│    → Verify frame capture before accepting camera                │
│    → Log all initialization errors                               │
│                                                                  │
│  QR Detection Failures:                                          │
│    → Return empty list (no crash)                                │
│    → Log "NO_QR_DETECTED" status                                 │
│    → Continue with next frame                                    │
│                                                                  │
│  QR Decoding Failures:                                           │
│    → Enhancement pipeline (3 stages)                             │
│    → Skip invalid payloads                                       │
│    → Log but don't block                                         │
│                                                                  │
│  Servo Failures:                                                 │
│    → Graceful degradation (continue without servo)               │
│    → Log warnings                                                │
│    → Manual control still available                              │
│                                                                  │
│  Network Failures (API POST):                                    │
│    → Log error                                                   │
│    → Continue processing (local CSV preserved)                   │
│    → Retry logic can be added                                    │
│                                                                  │
│  Duplicate Detection:                                            │
│    → Normalized Euclidean distance                               │
│    → Configurable thresholds (x: 0.5m, y: 0.5m)                │
│    → Same item, new location → New entry                         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 10. Configuration Management

```yaml
# config/config.yaml

camera:
  d: 0.20                    # Distance to wall (meters)

scanner:
  camera_candidates: [0, 1, 2]
  image_width: 640
  image_height: 480
  fourcc_codec: "MJPG"
  fps_target: 30
  servo_port: "/dev/ttyUSB0"
  servo_baud_rate: 115200
  enable_servo: true
  raw_save_dir: "data/raw_captures"

processor:
  log_file: "data/logs/processor.log"
  inventory_file: "data/inventory.csv"
  raw_meta_csv: "data/raw_captures/metadata.csv"
  save_annotated: false

duplicacy_thresholds:
  x: 0.5                     # 50cm horizontal
  y: 0.5                     # 50cm vertical

qr_detector:
  conf_th: 0.5               # YOLO confidence
  nms_iou: 0.45              # Non-max suppression
  padding_value: 0.3         # ROI padding (30%)

session:
  session_id: "S001"
  session_url: "http://api.warehouse.com/inventory"
```

---

## 11. Key Algorithms

### 11.1 Sharpness-Based Frame Selection
```python
def compute_sharpness(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    return laplacian.var()  # Higher = sharper
```

### 11.2 Normalized Distance for Duplicates
```python
def check_distance(coords1, coords2, threshold_x, threshold_y):
    dx = coords1[0] - coords2[0]
    dy = coords1[1] - coords2[1]
    
    # Normalized Euclidean distance
    norm_dist = sqrt((dx/threshold_x)² + (dy/threshold_y)²)
    
    return norm_dist <= 1.0  # True if duplicate
```

### 11.3 Camera Ray Intersection
```python
def uv_to_camera_coords(u, v, K, R, d):
    # 1. Get camera ray
    ray_cam = [(u - c_x)/f_x, (v - c_y)/f_y, 1.0]
    
    # 2. Rotate to world frame
    ray_world = R @ ray_cam
    
    # 3. Intersect with plane at distance d
    t = d / ray_world[1]
    x_cam = t * ray_world[0]
    y_cam = t * ray_world[2]
    
    return (x_cam, y_cam)
```

---

## 12. System States

```
┌─────────────────────────────────────────────────────────────────┐
│                     SYSTEM STATE MACHINE                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  IDLE                                                            │
│    ├─► Camera: Active                                           │
│    ├─► Servo: Neutral (H=1, V=1)                               │
│    ├─► LED: Off                                                 │
│    ├─► Queue: Empty                                             │
│    └─► Processor: Waiting                                       │
│                                                                  │
│  SCANNING                                                        │
│    ├─► Camera: Capturing                                        │
│    ├─► Servo: Moving between angles                            │
│    ├─► LED: Yellow (warning)                                    │
│    ├─► Queue: Jobs pending                                      │
│    └─► Processor: Active                                        │
│                                                                  │
│  PROCESSING                                                      │
│    ├─► Camera: Idle                                             │
│    ├─► Servo: Neutral                                           │
│    ├─► LED: Blue (working)                                      │
│    ├─► Queue: Draining                                          │
│    └─► Processor: Active (background)                           │
│                                                                  │
│  COMPLETE                                                        │
│    ├─► Camera: Idle                                             │
│    ├─► Servo: Neutral                                           │
│    ├─► LED: Green (success)                                     │
│    ├─► Queue: Empty                                             │
│    └─► Results: Saved to CSV + API                             │
│                                                                  │
│  ERROR                                                           │
│    ├─► Camera: May be released                                  │
│    ├─► Servo: Safe position                                     │
│    ├─► LED: Red (danger)                                        │
│    ├─► Queue: Flushed                                           │
│    └─► Logs: Error details written                             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Summary

This is a **production-grade computer vision system** for warehouse inventory management. The architecture features:

✅ **Modular Design**: Clear separation of hardware, processing, and orchestration  
✅ **Robustness**: Multi-level error handling and graceful degradation  
✅ **Performance**: Background processing with multiprocessing  
✅ **Accuracy**: Multi-stage QR enhancement and geometric rectification  
✅ **Scalability**: Queue-based job distribution  
✅ **Maintainability**: Comprehensive logging and configuration management

The system successfully bridges the gap between physical hardware (camera, servos, LEDs) and digital inventory management (CSV database, REST API) through sophisticated computer vision and coordinate transformation pipelines.