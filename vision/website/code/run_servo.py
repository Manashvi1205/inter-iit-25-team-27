#!/usr/bin/env python3
import argparse
import time
import cv2
from servoBoard import (
    ServoBoard,
    set_camera_orientation,
    servo_move_to,
    get_pose_list,
)

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
  calib <id>

  led <idx> <R> <G> <B> [brightness]
  ledc <idx> <color> [brightness]
  ledoff <idx>
  ledm <idx> <R> <G> <B> [brightness]
  flash <idx>
  alert <idx> <color>

  warning <idx>
  danger <idx>
  mandatory <idx>
  safe <idx>
  bg <idx>
  contrast <idx>

  ori <h> <v>
  hv <h> <v>

  scan normal|top|bottom

===================================================
"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=str, required=True)
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--camera", action="store_true")
    args = parser.parse_args()

    board = ServoBoard(args.port, args.baud)
    if not board.ser:
        print("[ERROR] Cannot open serial port.")
        return

    cap = None
    if args.camera:
        cap = cv2.VideoCapture(0)
        print("[INFO] camera enabled")

    print(HELP_TEXT)

    while True:
        cmd = input("servo> ").strip().lower()
        if cmd == "":
            continue

        if cmd in ("exit", "quit", "q"):
            break

        if cmd == "help":
            print(HELP_TEXT)
            continue

        if cmd == "pos":
            print(board.get_positions())
            continue

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
                print("[ERROR] invalid move")
            continue

        if cmd.startswith("calib"):
            parts = cmd.split()
            if len(parts) != 2:
                print("Usage: calib <id>")
                continue
            sid = int(parts[1])
            board.calibrate(sid)
            continue

        # RAW LED
        if cmd.startswith("led "):
            parts = cmd.split()
            if len(parts) not in (5, 6):
                print("Usage: led <idx> <R> <G> <B> [brightness]")
                continue
            idx = int(parts[1])
            r = int(parts[2]); g = int(parts[3]); b = int(parts[4])
            bright = int(parts[5]) if len(parts) == 6 else 255
            board.LED(idx, r, g, b, bright)
            continue

        # easy color LED
        if cmd.startswith("ledc"):
            parts = cmd.split()
            if len(parts) not in (3,4):
                print("Usage: ledc <idx> <color> [brightness]")
                continue
            idx = int(parts[1])
            color = parts[2]
            bright = int(parts[3]) if len(parts)==4 else 255
            board.led(idx, color, bright)
            continue

        if cmd.startswith("ledoff"):
            idx = int(cmd.split()[1])
            board.led_off(idx)
            continue

        if cmd.startswith("flash"):
            idx = int(cmd.split()[1])
            board.led_flash_on(idx)
            continue

        if cmd.startswith("alert"):
            parts = cmd.split()
            if len(parts) != 3:
                print("Usage: alert <idx> <color>")
                continue
            idx = int(parts[1])
            color = parts[2]
            board.led_alert(idx, color)
            continue

        # -----------------------------------------
        # SIGNAL PRESET COMMANDS
        # -----------------------------------------
        if cmd.startswith("warning"):
            idx = int(cmd.split()[1])
            board.warning(idx)
            continue

        if cmd.startswith("danger"):
            idx = int(cmd.split()[1])
            board.danger(idx)
            continue

        if cmd.startswith("mandatory"):
            idx = int(cmd.split()[1])
            board.mandatory(idx)
            continue

        if cmd.startswith("safe"):
            idx = int(cmd.split()[1])
            board.safe(idx)
            continue

        if cmd.startswith("bg"):
            idx = int(cmd.split()[1])
            board.bg(idx)
            continue

        if cmd.startswith("contrast"):
            idx = int(cmd.split()[1])
            board.contrast(idx)
            continue

        # Manual LED
        if cmd.startswith("ledm"):
            parts = cmd.split()
            if len(parts) not in (5,6):
                print("Usage: ledm <idx> <R> <G> <B> [brightness]")
                continue
            idx = int(parts[1])
            r = int(parts[2]); g = int(parts[3]); b = int(parts[4])
            bright = int(parts[5]) if len(parts)==6 else 255
            board.set_led_manual(idx, r, g, b, bright)
            continue

        # ori
        if cmd.startswith("ori"):
            parts = cmd.split()
            if len(parts) != 3:
                print("Usage: ori <h> <v>")
                continue
            h = int(parts[1]); v = int(parts[2])
            set_camera_orientation(board, h, v)
            continue

        # hv
        if cmd.startswith("hv"):
            parts = cmd.split()
            if len(parts) != 3:
                print("Usage: hv <h> <v>")
                continue
            h = int(parts[1]); v = int(parts[2])
            ok, frame = servo_move_to(board, h, v, cap=cap)
            if ok:
                print(f"[OK] moved to {h},{v}")
                if frame is not None:
                    cv2.imshow("frame", frame)
                    cv2.waitKey(1)
            continue

        # scan
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

        print("[ERROR] unknown command")

    board.close()
    if cap:
        cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
