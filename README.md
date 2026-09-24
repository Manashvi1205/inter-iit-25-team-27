# Inter IIT Tech Meet — Team 27 Autonomous Warehouse Rover

Submission archive for **Team 27**: ROS 2 navigation + QR shelf scanning + hardware + mission-control HMI.

The GitHub repo is this inner folder (`02_CODE_REPOSITORY`, `03_HARDWARE`, `04_VISION`). Demo `.mov` files are stored with **Git LFS** because several are larger than GitHub’s 100 MB git-object limit.

---

## Layout

| Path | What it is |
|------|------------|
| [`01_TECHNICAL_DOCUMENTATION.pdf`](01_TECHNICAL_DOCUMENTATION.pdf) | Team technical write-up |
| [`02_CODE_REPOSITORY/`](02_CODE_REPOSITORY) | **Canonical robot software**: ROS 2 workspace, Arduino firmware, Flask HMI |
| [`03_HARDWARE/`](03_HARDWARE) | BOM, CAD (`Bot.step`), drawings, schematics, demo videos |
| [`04_VISION/`](04_VISION) | Vision notes, alternate ROS vision workspace, HMI clones, CV experiments |

`README_SUBMISSION.txt` is the original one-line submission tag (`TEAM 27`).

### Canonical code (start here)

```
02_CODE_REPOSITORY/
  src/src/                 ROS 2 packages (double-src layout from the Jetson workspace)
    bot_description        URDF/xacro, Gazebo worlds, RViz
    bot_bringup            Bringup launch, Nav2 params, EKF, commander
    bot_broadcaster        Odom / IMU / joint_states / cmd_vel → Arduino
    bot_scanning           Vision pipeline as a ROS package (Scanner, Processor, servos, QR)
    rplidar_ros            Slamtec RPLiDAR ROS 2 driver (vendored)
  Utils/                   Arduino sketches (drive, odom, BNO055, servos, LEDs, buzzer)
  hmi/                     Flask “Eternal Rover Mission Control” dashboard
```

### Hardware

- [`03_HARDWARE/BOM.csv`](03_HARDWARE/BOM.csv) — parts list (Jetson Orin Nano, RPLiDAR S2E, IMX258 camera, IG42/IG45 motors, LiFePO4 pack, …)
- CAD: `03_HARDWARE/CAD_Models/CAD and Drawings/Bot.step` plus assembly PDFs
- Schematics: `03_HARDWARE/Electrical_Schematics/`
- Videos: `03_HARDWARE/Videos/` (`Vertical_scanning.mov`, `HMI.mov`, `obstacle_avoidance.mov`, `Slam.mov`, …)

`HMI.mov` / `2.mov` and `obstacle_avoidance.mov` / `obs.mov` look like duplicate pairs (same file sizes). Both are kept.

### Vision copies (not the live stack)

There are **four Flask HMI trees** and extra vision scripts. The live robot stack is `02_CODE_REPOSITORY`. Treat these as history / experiments:

- `02_CODE_REPOSITORY/hmi/` — **use this HMI**
- `04_VISION/Inter IIT/`, `04_VISION/website/Inter IIT/`, `04_VISION/website/Inter-IIT/` — older clones of the same dashboard
- `04_VISION/ros_workspace/` — TCP vision server + `warehouse_scanning` scripts
- `04_VISION/website/code/` and `04_VISION/website/Finalizing_shits/` — scanner / YOLO / homography prototypes
- [`04_VISION/d.md`](04_VISION/d.md) — long vision-architecture notes

---

## Robot stack (ROS 2)

Packages under `02_CODE_REPOSITORY/src/src/`. Expected compute: **NVIDIA Jetson Orin Nano**.

Typical bringup (on the robot, after `colcon build` and sourcing `install/setup.bash`):

```bash
ros2 launch bot_bringup my_bot.launch.py
```

Gazebo / model check:

```bash
ros2 launch bot_description gazebo_test.launch.py
```

LiDAR: RPLiDAR S2E via vendored `rplidar_ros`.

Firmware to flash is in `02_CODE_REPOSITORY/Utils/` (`.ino` sketches for Mega / ESP / servo board).

---

## Mission-control HMI

```pwsh
cd 02_CODE_REPOSITORY/hmi
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Open `http://localhost:5000`. Demo login in the HMI README is `admin` / `password` — change it before exposing the dashboard on a network.

Jetson posts telemetry/inventory to `POST /api/update`. See [`02_CODE_REPOSITORY/hmi/README.md`](02_CODE_REPOSITORY/hmi/README.md).

---

## Vision pipeline

High level: camera + pan/tilt servos → YOLO / WeChat QR → shelf inventory CSV → HMI API. Orchestrated by `visionNode` / `Processor` / `Scanner`.

WeChat QR `.caffemodel` weights live next to the prototxt under:

- `02_CODE_REPOSITORY/src/src/bot_scanning/config/wechat_qrcode_models/`
- `04_VISION/ros_workspace/src/warehouse_scanning/config/wechat_qrcode_models/`

Standalone TCP server notes: [`04_VISION/ros_workspace/readme.txt`](04_VISION/ros_workspace/readme.txt).

Python deps (vision side): [`04_VISION/ros_workspace/requirements.txt`](04_VISION/ros_workspace/requirements.txt).

---

## Clone this repository (videos need Git LFS)

```bash
git lfs install
git clone <this-repo-url>
```

Without Git LFS you will only get tiny pointer files instead of the `.mov` demos.

---

## What was cleaned for GitHub

This used to be a dump with **nested git clones** (including `sthitapragyan001/Inter-IIT` HMI copies). Nested `.git` folders were removed so everything lands in **one** repository instead of empty submodule links.

Ignored: `__pycache__`, virtualenvs, colcon `build/install/log`, macOS `__MACOSX` junk, `*.log`, `.env` secrets.

Kept: all source, CAD, PDFs, images, STL/STEP meshes, and demo videos.
