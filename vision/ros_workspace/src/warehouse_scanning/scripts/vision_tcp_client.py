import socket, json
import yaml
from pathlib import Path

SESSION_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "server.yaml"

with open(SESSION_CONFIG_PATH, "r") as f:
    _session_cfg = yaml.safe_load(f)

class VisionTCPClient:
    HOST = _session_cfg["vision_node"]["host"]
    PORT = _session_cfg["vision_node"]["port"]

    def send(self, msg_dict):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.HOST, self.PORT))
        s.send(json.dumps(msg_dict).encode())
        data = s.recv(4096)
        s.close()
        return json.loads(data.decode())

    # high level wrappers

    def capture(self, x, y, isTop=False, isBottom=False):
        return self.send({"cmd":"capture", "x":x, "y":y, "isTop":isTop, "isBottom":isBottom})

    def capture_once(self, x, y, orientation=1):
        return self.send({"cmd":"capture_once", "x":x, "y":y, "orientation":orientation})

    def led(self, color="white", level="low", index=0):
        return self.send({"cmd":"led", "color":color, "level":level, "index":index})

    def led_off(self, index=0):
        return self.send({"cmd":"led_off", "index":index})

    def wait_done(self):
        return self.send({"cmd":"wait_done"})
    
    def shutdown(self):
        return self.send({"cmd":"shutdown"})