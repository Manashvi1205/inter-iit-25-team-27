# servo_lib.py
import serial
import time
import re

# ==========================================
# PART 1: DRIVER CLASS (UNCHANGED)
# ==========================================
class ServoBoard:
    def __init__(self, port, baudrate=115200, timeout=2):
        try:
            self.ser = serial.Serial(port, baudrate, timeout=timeout)
            print(f"Connected to {port} at {baudrate} baud.")
            time.sleep(2)
            self.clear_buffer()
        except serial.SerialException as e:
            print(f"Error connecting to serial port: {e}")
            self.ser = None

    def clear_buffer(self):
        if self.ser and self.ser.in_waiting:
            self.ser.read(self.ser.in_waiting)

    def move(self, servo_id, angle):
        if not self.ser:
            return
        angle = max(0, min(180, angle))
        cmd = f"{servo_id} {angle}\n"
        self.ser.write(cmd.encode())
        time.sleep(0.01)

    def calibrate(self, servo_id):
        if not self.ser:
            return
        cmd = f"{servo_id} -1\n"
        self.ser.write(cmd.encode())
        time.sleep(0.5)

    def get_positions(self):
        if not self.ser:
            return {}
        self.clear_buffer()
        self.ser.write(b"P\n")

        angles = {}
        start = time.time()

        while time.time() - start < 1.0:
            if self.ser.in_waiting:
                try:
                    line = self.ser.readline().decode().strip()
                    match = re.search(r"ID (\d+): ([\d\.-]+) deg", line)
                    if match:
                        s_id = int(match.group(1))
                        s_ang = float(match.group(2))
                        angles[s_id] = s_ang

                    if 0 in angles and 1 in angles:
                        break
                except:
                    pass
        return angles

    def LED(self, index=0, r=255, g=255, b=255, brightness=int(255*0.7)):
        if not self.ser:
            print("[ERROR] Servo board not initialized.")
            return

        cmd = f"L {index} {r} {g} {b} {brightness}\n"
        print("Sending LED command:", repr(cmd))
        self.ser.write(cmd.encode())
        time.sleep(0.05)


    def close(self):
        if self.ser:
            self.ser.close()
            
            print("Connection closed.")
    

    





# ==========================================
# PART 2: CAMERA SERVO CONTROL HELPERS
# ==========================================
# Default shifts (kept as in your original settings)
DEFAULT_H_THETA = 30
DEFAULT_V_THETA = 25

H_NEUTRAL = 90
V_NEUTRAL = 90


def set_camera_orientation(board, h, v):
    """
    Legacy helper kept for compatibility.
    h, v ∈ {0,1}
    (1,1) -> neutral (90,90)
    (0,1) -> horizontal left (90-30, 90)
    (1,0) -> vertical down (90, 90-25)
    (0,0) -> both offsets
    Returns True/False.
    """
    if board is None or getattr(board, "ser", None) is None:
        print("[ERROR] Servo board not initialized.")
        return False

    try:
        if h not in [0, 1] or v not in [0, 1]:
            print("[ERROR] h and v must be 0 or 1.")
            return False

        # compute angles
        h_angle = H_NEUTRAL - (DEFAULT_H_THETA * (1 - h))
        v_angle = V_NEUTRAL - (DEFAULT_V_THETA * (1 - v))

        # send
        board.move(0, h_angle)  # horizontal
        board.move(1, v_angle)  # vertical

        return True

    except Exception as e:
        print(f"[ERROR] Servo move failed: {e}")
        return False


def servo_move_to(board, h=1, v=1,
                  h_delta=DEFAULT_H_THETA, v_delta=DEFAULT_V_THETA,
                  neutral_h=H_NEUTRAL, neutral_v=V_NEUTRAL,
                  wait_after_move=0.25, cap=None, capture_after_move=True):
    """
    Move camera to discrete pose (h,v) where each ∈ {0,1,2}:
      0 -> neutral - delta (left / down)
      1 -> neutral (center)
      2 -> neutral + delta (right / up)

    If capture_after_move==True and cap supplied, returns (True, frame).
    Otherwise returns (True, None) on success, (False, None) on failure.
    """
    # validation
    if board is None or getattr(board, "ser", None) is None:
        # fail-safe: not initialized servo - return False (caller can handle)
        print("[WARN] servo_move_to: board not initialized (no-servo).")
        return False, None
    if h not in (0, 1, 2) or v not in (0, 1, 2):
        print("[ERROR] servo_move_to: h and v must be 0,1,2")
        return False, None

    def map_angle(idx, neutral, delta):
        if idx == 1:
            return float(neutral)
        elif idx == 0:
            return float(max(0, neutral - delta))
        else:  # idx == 2
            return float(min(180, neutral + delta))

    h_angle = map_angle(h, neutral_h, h_delta)
    v_angle = map_angle(v, neutral_v, v_delta)

    try:
        # move horizontal then vertical
        board.move(0, h_angle)
        board.move(1, v_angle)

        # settle
        time.sleep(wait_after_move)

        # optional capture
        captured = None
        if capture_after_move and cap is not None:
            ret, frame = cap.read()
            if ret and frame is not None:
                captured = frame.copy()
        return True, captured

    except Exception as e:
        print(f"[ERROR] servo_move_to failed: {e}")
        return False, None


def get_pose_list(is_top=False, is_bottom=False):
    """
    Return list of (h,v) tuples to try for a level based on flags.
    Rules (as requested):
      - normal scan: H = 0,1,2 ; V = 1
      - top: H = 0,1,2 ; V = 1,2
      - bottom: H = 0,1,2 ; V = 0,1
    """
    Hs = [0, 1, 2]
    if not is_top and not is_bottom:
        return [(h, 1) for h in Hs]
    if is_top:
        return [(h, v) for h in Hs for v in (1, 2)]
    if is_bottom:
        return [(h, v) for h in Hs for v in (0, 1)]
    return [(h, 1) for h in Hs]


# ==========================================
# PART 3: DEBUG TERMINAL (MANUAL CONTROL)
# ==========================================
def servo_debug_terminal(port, baud=115200):
    """
    Opens the classic CLI interface for calibration and testing.
    """
    board = ServoBoard(port, baud)
    if not board.ser:
        print("[ERROR] Could not open servo terminal.")
        return

    print("\n[DEBUG TERMINAL]")
    print("Commands:")
    print("  0 90      → move servo 0 to 90°")
    print("  1 -1      → calibrate servo 1")
    print("  P         → read positions")
    print("  Q         → quit")
    print("----------------------------------------")

    while True:
        cmd = input("debug > ").strip().upper()

        if cmd in ["Q", "QUIT", "EXIT"]:
            break

        elif cmd == "P":
            pos = board.get_positions()
            print(pos)

        
                # ----------------------------------------
        # LED COMMAND:   LED index r g b [brightness]
        # Example:       LED 1 255 0 0  80
        # ----------------------------------------
        elif cmd.startswith("LED"):
            parts = cmd.split()
            if len(parts) not in (5, 6):
                print("Usage: LED index R G B [brightness]")
                continue

            try:
                index = int(parts[1])
                r = int(parts[2])
                g = int(parts[3])
                b = int(parts[4])
                brightness = int(parts[5]) if len(parts) == 6 else 255

                board.LED(index, r, g, b, brightness)
            except:
                print("[ERROR] LED command invalid.")
            continue

        else:
            parts = cmd.split()
            if len(parts) == 2:
                try:
                    s_id = int(parts[0])
                    angle = float(parts[1])
                    if angle == -1:
                        board.calibrate(s_id)
                    else:
                        board.move(s_id, angle)
                except:
                    print("[ERROR] Invalid command.")
            else:
                print("[ERROR] Format: ID ANGLE")


    board.close()
