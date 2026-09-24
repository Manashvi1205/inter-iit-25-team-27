import socket
import json
import threading
from visionNode import visionNode

import yaml
from pathlib import Path

SESSION_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "server.yaml"

with open(SESSION_CONFIG_PATH, "r") as f:
    _session_cfg = yaml.safe_load(f)


# Initialize your existing visionNode
vision = visionNode.get()

HOST = _session_cfg["vision_node"]["host"]   # only local communication
PORT = _session_cfg["vision_node"]["port"]
running = True       # flag to stop server when shutdown is called


def handle_client(conn):
    global running
    try:
        data = conn.recv(4096)
        if not data:
            conn.close()
            return

        msg = json.loads(data.decode())
        cmd = msg.get("cmd")

        # ----------------------------
        # CAMERA / CAPTURE COMMANDS
        # ----------------------------
        if cmd == "capture":
            x = msg.get("x", 0.0)
            y = msg.get("y", 0.0)
            isTop = msg.get("isTop", False)
            isBottom = msg.get("isBottom", False)
            vision.capture(x, y, isTop, isBottom)
            conn.send(json.dumps({"status": "OK"}).encode())

        elif cmd == "capture_once":
            x = msg.get("x", 0.0)
            y = msg.get("y", 0.0)
            ori = msg.get("orientation", 1)
            vision.capture_once(x, y, orientation=ori)
            conn.send(json.dumps({"status": "OK"}).encode())

        # ----------------------------
        # LED CONTROL
        # ----------------------------
        elif cmd == "led":
            color = msg.get("color", "white")
            level = msg.get("level", "low")
            index = msg.get("index", 0)
            success = vision.led(color=color, level=level, index=index)
            conn.send(json.dumps({"status": success}).encode())

        elif cmd == "led_off":
            index = msg.get("index", 0)
            success = vision.led_off(index)
            conn.send(json.dumps({"status": success}).encode())

        # ----------------------------
        # WAIT FOR PROCESSING
        # ----------------------------
        elif cmd == "wait_done":
            vision.wait_until_done()
            conn.send(json.dumps({"status": "DONE"}).encode())

        # ----------------------------
        # SHUTDOWN VISION NODE
        # ----------------------------
        elif cmd == "shutdown":
            conn.send(json.dumps({"status": "SHUTTING_DOWN"}).encode())
            vision.shutdown()       # this is your internal shutdown
            running = False         # stop server loop

        # ----------------------------
        else:
            conn.send(json.dumps({"status": "ERR", "msg": "Unknown cmd"}).encode())

    except Exception as e:
        conn.send(json.dumps({"status": "ERR", "msg": str(e)}).encode())

    finally:
        conn.close()


def start_server():
    global running

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(5)

    print(f"[VISION SERVER] Running on {HOST}:{PORT}")

    while running:
        try:
            server.settimeout(1.0)   # allows clean shutdown
            conn, _ = server.accept()
            threading.Thread(target=handle_client, args=(conn,), daemon=True).start()
        except socket.timeout:
            continue

    server.close()
    print("[VISION SERVER] Shutdown completed.")


if __name__ == "__main__":
    start_server()
