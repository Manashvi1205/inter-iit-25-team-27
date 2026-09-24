# Inter IIT Tech Meet — Team 27 Autonomous Warehouse Rover

ROS 2 navigation, QR shelf scanning, hardware, and mission-control HMI.

Demo `.mov` files are stored with **Git LFS** (several are over GitHub’s 100 MB git-object limit). Clone with `git lfs install` first.

---

## Layout

| Path | What it is |
|------|------------|
| [`code/`](code) | Robot software: ROS 2 workspace, Arduino firmware, Flask HMI |
| [`hardware/`](hardware) | BOM, CAD (`Bot.step`), drawings, schematics, demo videos |
| [`vision/`](vision) | Vision notes, alternate ROS workspace, HMI clones, CV experiments |
| [`docs/technical-documentation.pdf`](docs/technical-documentation.pdf) | Team technical write-up |

### Robot software (`code/`)

```
code/
  src/src/                 ROS 2 packages (double-src layout from the Jetson workspace)
    bot_description        URDF/xacro, Gazebo worlds, RViz
    bot_bringup            Bringup launch, Nav2 params, EKF, commander
    bot_broadcaster        Odom / IMU / joint_states / cmd_vel → Arduino
    bot_scanning           Vision pipeline as a ROS package (Scanner, Processor, servos, QR)
    rplidar_ros            Slamtec RPLiDAR ROS 2 driver (vendored)
  Utils/                   Arduino sketches (drive, odom, BNO055, servos, LEDs, buzzer)
  hmi/                     Flask “Eternal Rover Mission Control” dashboard
```

### Hardware (`hardware/`)

- [`hardware/BOM.csv`](hardware/BOM.csv) — parts list (Jetson Orin Nano, RPLiDAR S2E, IMX258 camera, IG42/IG45 motors, LiFePO4 pack, …)
- CAD: `hardware/CAD_Models/CAD and Drawings/Bot.step` plus assembly PDFs
- Schematics: `hardware/Electrical_Schematics/`
- Videos: `hardware/Videos/` (`Vertical_scanning.mov`, `HMI.mov`, `obstacle_avoidance.mov`, `Slam.mov`, …)

`HMI.mov` / `2.mov` and `obstacle_avoidance.mov` / `obs.mov` are duplicate pairs (same content). Both are kept.

### Vision copies (not the live stack)

The live robot stack is **`code/`**. Treat `vision/` as history / experiments:

- `code/hmi/` — **use this HMI**
- `vision/Inter IIT/`, `vision/website/Inter IIT/`, `vision/website/Inter-IIT/` — older clones of the same dashboard
- `vision/ros_workspace/` — TCP vision server + `warehouse_scanning` scripts
- `vision/website/code/` and `vision/website/Finalizing_shits/` — scanner / YOLO / homography prototypes
- [`vision/d.md`](vision/d.md) — long vision-architecture notes

---

## Robot stack (ROS 2)

Packages under `code/src/src/`. Expected compute: **NVIDIA Jetson Orin Nano**.

Typical bringup (on the robot, after `colcon build` and sourcing `install/setup.bash`):

```bash
ros2 launch bot_bringup my_bot.launch.py
```

Gazebo / model check:

```bash
ros2 launch bot_description gazebo_test.launch.py
```

LiDAR: RPLiDAR S2E via vendored `rplidar_ros`.

Firmware to flash is in `code/Utils/` (`.ino` sketches for Mega / ESP / servo board).

---

## Mission-control HMI

```pwsh
cd code/hmi
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Open `http://localhost:5000`. Demo login in the HMI README is `admin` / `password` — change it before exposing the dashboard on a network.

Jetson posts telemetry/inventory to `POST /api/update`. See [`code/hmi/README.md`](code/hmi/README.md).

---

## Vision pipeline

High level: camera + pan/tilt servos → YOLO / WeChat QR → shelf inventory CSV → HMI API. Orchestrated by `visionNode` / `Processor` / `Scanner`.

WeChat QR `.caffemodel` weights live next to the prototxt under:

- `code/src/src/bot_scanning/config/wechat_qrcode_models/`
- `vision/ros_workspace/src/warehouse_scanning/config/wechat_qrcode_models/`

Standalone TCP server notes: [`vision/ros_workspace/readme.txt`](vision/ros_workspace/readme.txt).

Python deps (vision side): [`vision/ros_workspace/requirements.txt`](vision/ros_workspace/requirements.txt).

---

## Clone this repository (videos need Git LFS)

```bash
git lfs install
git clone https://github.com/Manashvi1205/inter-iit-25-team-27.git
```

Without Git LFS you will only get tiny pointer files instead of the `.mov` demos.
