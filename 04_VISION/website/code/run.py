#!/usr/bin/env python3
import argparse
import time
import cv2
from servo_board import (
    ServoBoard,
    set_camera_orientation,
    servo_move_to,
    get_pose_list,
)

# ---------------------------------------------------------
# HELP MENU
# ---------------------------------------------------------
HELP_TEXT = """
================= SERVO TEST CLI =================

COMMANDS:

  help
      Show this help menu.

  exit
      Quit program.

  pos
      Read servo positions.

  move <id> <angle>
      Move servo ID (0 or 1) to angle (0–180).
      Example:  move 0 120

  calib <id>
      Calibrate servo (sends angle = -1).
      Example:  calib 1

  led <index> <R> <G> <B> [brightness]
      Control WS2812 LED.
      Example:  led 1 255 0 0  80

  ori <h> <v>
      Legacy orientation (h,v ∈ {0,1})
      Example: ori 1 1

  hv <h> <v>
      Full-resolution orientation (h,v ∈ {0,1,2})
      Example: hv 2 1

  scan normal|top|bottom
      Print sequence of (h,v) poses for scanning.

===================================================
"""


# ---------------------------------------------------------
# MAIN LOOP
# ---------------------------------------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=str, required=True,
                        help="Serial port (e.g., COM9, /dev/ttyUSB0)")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--camera", action="store_true",
                        help="Enable camera read for hv moves")
    args = parser.parse_args()

    # -----------------------
    # CONNECT BOARD
    # -----------------------
    board = ServoBoard(args.port, args.baud)
    if not board.ser:
        print("[ERROR] Cannot open serial port.")
        return

    cap = None
    if args.camera:
        cap = cv2.VideoCapture(0)
        print("[INFO] camera enabled for hv capture")

    print(HELP_TEXT)

    # -----------------------
    # CLI LOOP
    # -----------------------
    while True:
        cmd = input("servo> ").strip().lower()
        if cmd == "":
            continue

        # exit
        if cmd in ("exit", "quit", "q"):
            break

        # help
        if cmd == "help":
            print(HELP_TEXT)
            continue

        # read positions
        if cmd == "pos":
            print(board.get_positions())
            continue

        # -----------------------------------------------------
        # MOVE:  move 0 120
        # -----------------------------------------------------
        if cmd.startswith("move"):
            parts = cmd.split()
            if len(parts) != 3:
                print("Usage: move <id> <angle>")
                continue

            try:
                sid = int(parts[1])
                angle = float(parts[2])
                board.move(sid, angle)
            except:
                print("[ERROR] invalid move cmd")
            continue

        # -----------------------------------------------------
        # CALIBRATE
        # -----------------------------------------------------
        if cmd.startswith("calib"):
            parts = cmd.split()
            if len(parts) != 2:
                print("Usage: calib <id>")
                continue

            try:
                sid = int(parts[1])
                board.calibrate(sid)
            except:
                print("[ERROR] invalid calib cmd")
            continue

        # -----------------------------------------------------
        # LED CONTROL
        # -----------------------------------------------------
        if cmd.startswith("led"):
            parts = cmd.split()
            if len(parts) not in (5, 6):
                print("Usage: led <idx> <R> <G> <B> [brightness]")
                continue
            try:
                index = int(parts[1])
                r = int(parts[2])
                g = int(parts[3])
                b = int(parts[4])
                brightness = int(parts[5]) if len(parts) == 6 else 255
                board.LED(index, r, g, b, brightness)
            except:
                print("[ERROR] invalid led cmd")
            continue

        # -----------------------------------------------------
        # LEGACY ORIENTATION (0/1)
        # -----------------------------------------------------
        if cmd.startswith("ori"):
            parts = cmd.split()
            if len(parts) != 3:
                print("Usage: ori <h> <v> (0/1)")
                continue
            try:
                h = int(parts[1])
                v = int(parts[2])
                set_camera_orientation(board, h, v)
            except:
                print("[ERROR] invalid ori")
            continue

        # -----------------------------------------------------
        # FULL 3×3 ORIENTATION (h,v ∈ {0,1,2})
        # -----------------------------------------------------
        if cmd.startswith("hv"):
            parts = cmd.split()
            if len(parts) != 3:
                print("Usage: hv <h> <v> (0/1/2)")
                continue
            try:
                h = int(parts[1])
                v = int(parts[2])
                ok, frame = servo_move_to(board, h, v, cap=cap)
                if ok:
                    print(f"[OK] moved to {h},{v}")
                    if frame is not None:
                        cv2.imshow("frame", frame)
                        cv2.waitKey(1)
            except:
                print("[ERROR] invalid hv")
            continue

        # -----------------------------------------------------
        # SCAN POSE LIST PRINT
        # -----------------------------------------------------
        if cmd.startswith("scan"):
            parts = cmd.split()
            if len(parts) != 2:
                print("Usage: scan normal|top|bottom")
                continue

            mode = parts[1]
            if mode == "normal":
                print(get_pose_list(False, False))
            elif mode == "top":
                print(get_pose_list(True, False))
            elif mode == "bottom":
                print(get_pose_list(False, True))
            else:
                print("[ERROR] invalid scan mode")
            continue

        # unknown command
        print("[ERROR] unknown command")


    # ---------------------------------------------------------
    # CLEANUP
    # ---------------------------------------------------------
    board.close()
    if cap:
        cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
