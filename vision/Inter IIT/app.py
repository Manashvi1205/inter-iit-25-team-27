import os
import csv
import threading
import importlib
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import sys

# =========================================================
# Flask App Setup
# =========================================================
app = Flask(__name__)
app.secret_key = 'super_secret_rover_key_change_this'
app.permanent_session_lifetime = timedelta(days=365)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')

# =========================================================
# Base Paths
# =========================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
os.makedirs(DATA_DIR, exist_ok=True)

# =========================================================
# Files
# =========================================================
ROVER_FILE = os.path.join(DATA_DIR, 'rover_data.csv')
INVENTORY_FILE = os.path.join(DATA_DIR, 'inventory.csv')
RACKS_FILE = os.path.join(DATA_DIR, 'racks.csv')

# =========================================================
# Vision Node (SAFE, SAME DIR AS app.py)
# =========================================================
vision_node_path = BASE_DIR
vision_node_file = os.path.join(vision_node_path, 'visionNode.py')

if vision_node_path not in sys.path:
    sys.path.insert(0, vision_node_path)

# Auto-create visionNode.py if missing
if not os.path.isfile(vision_node_file):
    with open(vision_node_file, 'w') as f:
        f.write(
            "# Auto-generated visionNode stub\n"
            "class DummyVision:\n"
            "    def capture(self, *a, **k): raise RuntimeError('Vision not implemented')\n"
            "    def capture_once(self, *a, **k): raise RuntimeError('Vision not implemented')\n"
            "    def led(self, *a, **k): return False\n"
            "    def led_off(self, *a, **k): return False\n"
            "    def wait_until_done(self, *a, **k): pass\n"
            "    @property\n"
            "    def scanner(self): return self\n"
            "    def open_servo_debug_terminal(self): pass\n\n"
            "def get():\n"
            "    return DummyVision()\n"
        )
    print(f"[VISION WARN] visionNode.py auto-created at {vision_node_file}")

# =========================================================
# CSV Headers
# =========================================================
ROVER_HEADERS = ['round_id', 'timestamp', 'battery_level', 'cpu_temp', 'status', 'current_task', 'coordinates']
INVENTORY_HEADERS = ['round_id', 'timestamp', 'shelf_id', 'shelf_status']
RACKS_HEADERS = ['rack_id', 'shelves', 'created_at']

DEFAULT_RACK_COUNT = 5
DEFAULT_SHELVES_PER_RACK = 5
DEFAULT_RACK_IDS = ['R01', 'R02', 'R03', 'R04', 'R05']

file_lock = threading.Lock()
CURRENT_ROUND_ID = 1

# =========================================================
# Init DB
# =========================================================
def init_db():
    global CURRENT_ROUND_ID

    for path, headers in [
        (ROVER_FILE, ROVER_HEADERS),
        (INVENTORY_FILE, INVENTORY_HEADERS),
        (RACKS_FILE, RACKS_HEADERS)
    ]:
        if not os.path.exists(path):
            with open(path, 'w', newline='') as f:
                csv.writer(f).writerow(headers)

    try:
        with open(ROVER_FILE) as f:
            rows = [int(r['round_id']) for r in csv.DictReader(f) if r['round_id'].isdigit()]
            CURRENT_ROUND_ID = max(rows) if rows else 1
    except:
        CURRENT_ROUND_ID = 1

init_db()

# =========================================================
# Vision Loader (SAFE)
# =========================================================
_vision_node = None

def init_vision_node():
    global _vision_node
    if _vision_node:
        return _vision_node
    try:
        visionNode = importlib.import_module('visionNode')
        importlib.reload(visionNode)
        _vision_node = visionNode.get()
        return _vision_node
    except Exception as e:
        print(f"[VISION ERROR] {e}")
        return None

# =========================================================
# Auth
# =========================================================
def login_required(fn):
    def wrapper(*a, **k):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return fn(*a, **k)
    wrapper.__name__ = fn.__name__
    return wrapper

# =========================================================
# Routes
# =========================================================
@app.route('/')
def index():
    return redirect(url_for('dashboard') if 'logged_in' in session else url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and request.form.get('username') == 'admin':
        if request.form.get('password') == 'password':
            session['logged_in'] = True
            session.permanent = True
            return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

# =========================================================
# ✅ FIXED: get_data route (CORRECT LOCATION)
# =========================================================
@app.route('/api/get_data', methods=['GET'])
@login_required
def get_data():
    return jsonify({
        "status": "ok",
        "message": "get_data endpoint restored"
    })

# =========================================================
# Vision APIs (SAFE)
# =========================================================
@app.route('/api/vision/capture', methods=['POST'])
@login_required
def vision_capture():
    vision = init_vision_node()
    if not vision:
        return jsonify({"error": "Vision module unavailable"}), 500
    try:
        d = request.get_json() or {}
        vision.capture(d.get('x', 0), d.get('y', 0))
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/vision/wait_completion', methods=['POST'])
@login_required
def vision_wait():
    vision = init_vision_node()
    if not vision:
        return jsonify({"error": "Vision module unavailable"}), 500
    vision.wait_until_done()
    return jsonify({"status": "done"})

# =========================================================
# Run
# =========================================================
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
