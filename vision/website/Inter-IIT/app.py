import os
import csv
import threading
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import sys

app = Flask(__name__)
app.secret_key = 'super_secret_rover_key_change_this'
# Make session cookies permanent for a long duration (approx 1 year)
# This keeps users logged in until they explicitly logout or clear cookies.
app.permanent_session_lifetime = timedelta(days=365)
# Force UTF-8 safe printing
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')

# -------------------------
# Config / Filenames
# -------------------------
ROVER_FILE = 'rover_data.csv'
INVENTORY_FILE = 'inventory.csv'   # stores inventory scan logs
RACKS_FILE = 'racks.csv'           # stores known racks and their shelf counts

# CSV headers
ROVER_HEADERS = ['round_id', 'timestamp', 'battery_level', 'cpu_temp', 'status', 'current_task', 'coordinates']
INVENTORY_HEADERS = ['round_id', 'timestamp', 'shelf_id', 'shelf_status']
RACKS_HEADERS = ['rack_id', 'shelves', 'created_at']

# Defaults
DEFAULT_RACK_COUNT = 5
DEFAULT_SHELVES_PER_RACK = 5
DEFAULT_RACK_IDS = ['R01', 'R02', 'R03', 'R04', 'R05']

file_lock = threading.Lock()
CURRENT_ROUND_ID = 0

# Flask app initialization
app = Flask(__name__)
app.secret_key = 'super_secret_rover_key_change_this'


# -------------------------
# Helper functions
# -------------------------
def init_db():
    """Initialize CSV files and detect last round_id."""
    global CURRENT_ROUND_ID

    # Rover file
    if not os.path.exists(ROVER_FILE):
        with open(ROVER_FILE, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(ROVER_HEADERS)

    # Inventory file
    if not os.path.exists(INVENTORY_FILE):
        with open(INVENTORY_FILE, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(INVENTORY_HEADERS)

    # Racks file
    if not os.path.exists(RACKS_FILE):
        with open(RACKS_FILE, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(RACKS_HEADERS)

    # Detect last round from rover logs
    try:
        with open(ROVER_FILE, 'r') as f:
            reader = csv.DictReader(f)
            rounds = [int(row['round_id']) for row in reader if row.get('round_id', '').isdigit()]
            CURRENT_ROUND_ID = max(rounds) if rounds else 1
    except:
        CURRENT_ROUND_ID = 1


def read_racks():
    """Return dict: rack_id -> shelves"""
    racks = {}
    if not os.path.exists(RACKS_FILE):
        return racks
    with open(RACKS_FILE, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for r in reader:
            rid = r.get('rack_id')
            if not rid:
                continue
            try:
                shelves = int(r.get('shelves', DEFAULT_SHELVES_PER_RACK))
            except:
                shelves = DEFAULT_SHELVES_PER_RACK
            racks[rid] = shelves
    return racks


def write_racks(racks_dict):
    """Write racks to racks.csv"""
    with open(RACKS_FILE, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=RACKS_HEADERS)
        writer.writeheader()
        for rid, shelves in racks_dict.items():
            row = {
                'rack_id': rid,
                'shelves': shelves,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            writer.writerow(row)


def ensure_default_racks():
    """Make sure default 5 racks exist."""
    racks = read_racks()

    if len(racks) >= DEFAULT_RACK_COUNT:
        return

    added = False
    for rid in DEFAULT_RACK_IDS[:DEFAULT_RACK_COUNT]:
        if rid not in racks:
            racks[rid] = DEFAULT_SHELVES_PER_RACK
            added = True

    if added:
        write_racks(racks)


# Initialize everything
init_db()
ensure_default_racks()


# -------------------------
# Authentication
# -------------------------
def login_required(func):
    def wrapper(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper


# -------------------------
# Routes
# -------------------------
@app.route('/')
def index():
    if 'logged_in' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == 'admin' and password == 'password':
            # Mark this session as permanent so it persists long-term
            session.permanent = True
        if request.form.get('username') == 'admin' and request.form.get('password') == 'password':
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
        error = 'Invalid Credentials.'
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')


# -------------------------
# API: Manual new round
# -------------------------
@app.route('/api/new_round', methods=['POST'])
@login_required
def new_round():
    global CURRENT_ROUND_ID
    with file_lock:
        CURRENT_ROUND_ID += 1
    print("New round started:", CURRENT_ROUND_ID)
    return jsonify({"message": "New round started", "new_round_id": CURRENT_ROUND_ID})


# -------------------------
# API: Rover Update
# -------------------------
@app.route('/api/update', methods=['POST'])
def update_data():
    global CURRENT_ROUND_ID

    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data"}), 400

        # Handle new round flag
        if data.get('new_round') is True:
            with file_lock:
                CURRENT_ROUND_ID += 1
            print("New round initialized by rover:", CURRENT_ROUND_ID)

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Telemetry row
        telemetry_row = [
            CURRENT_ROUND_ID,
            timestamp,
            data.get('battery_level', 'N/A'),
            data.get('cpu_temp', 'N/A'),
            data.get('status', 'Idle'),
            data.get('current_task', 'None'),
            data.get('coordinates', '0,0')
        ]

        with file_lock:
            # Write telemetry
            with open(ROVER_FILE, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(telemetry_row)

            # Handle inventory scan
            payload = data.get('payload', '')
            if len(payload) >= 0:
                shelf_id = payload[:3]+ '-' + '0' + payload[5]
                if payload:
                    shelf_status = payload[-6:]
                else:
                    shelf_status = "Unknown"
            if shelf_id:
                rack_part = shelf_id.split('-')[0] if '-' in shelf_id else shelf_id

                # auto-create rack if missing
                racks = read_racks()
                rack_created = False
                if rack_part not in racks:
                    racks[rack_part] = DEFAULT_SHELVES_PER_RACK
                    write_racks(racks)
                    print("Auto-created new rack:", rack_part)
                    rack_created = True

                # Write inventory entry
                inventory_row = [
                    CURRENT_ROUND_ID,
                    timestamp,
                    shelf_id,
                    shelf_status
                ]
                with open(INVENTORY_FILE, 'a', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(inventory_row)

        return jsonify({"message": "Logged", "round_id": CURRENT_ROUND_ID, "rack_created": rack_created if 'rack_created' in locals() else False}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# -------------------------
# API: Get Shelves (paginated)
# -------------------------
@app.route('/api/get_shelves', methods=['GET'])
@login_required
def get_shelves():
    """
    Paginated shelves for a given rack.
    Query params:
      - rack (required): rack id, e.g. A or G
      - offset (optional): integer offset (default 0)
      - limit  (optional): integer page size (default 5)
      - round_id (optional): which round to read inventory from (defaults to current round)
    """
    rack = request.args.get('rack')
    if not rack:
        return jsonify({"error": "missing rack parameter"}), 400

    try:
        offset = max(0, int(request.args.get('offset', 0)))
    except:
        offset = 0
    try:
        limit = max(1, int(request.args.get('limit', 5)))
    except:
        limit = 5

    # which round to view
    req_round = request.args.get('round_id')
    try:
        target_round = int(req_round) if req_round else CURRENT_ROUND_ID
    except:
        target_round = CURRENT_ROUND_ID

    # Get known shelves count for this rack from racks.csv
    racks = read_racks()
    shelves_count = int(racks.get(rack, DEFAULT_SHELVES_PER_RACK))

    # Build full list of shelf ids in natural order
    full_shelves = [f"{rack}-{i:02d}" for i in range(1, shelves_count + 1)]
    total = len(full_shelves)

    # read latest statuses for shelves (prefer entries for the target round)
    shelf_status_map = {}
    try:
        with file_lock:
            if os.path.exists(INVENTORY_FILE):
                with open(INVENTORY_FILE, 'r', newline='') as f:
                    reader = csv.DictReader(f)
                    # iterate and keep last status per shelf for the requested round
                    for row in reader:
                        try:
                            r_id = int(row.get('round_id', '1'))
                        except:
                            r_id = 1
                        if r_id != target_round:
                            continue
                        sid = row.get('shelf_id')
                        if sid:
                            shelf_status_map[sid] = row.get('shelf_status', 'Unknown')
    except Exception:
        pass

    # Build the page slice
    slice_shelves = full_shelves[offset: offset + limit]
    out = []
    for idx, sid in enumerate(slice_shelves, start=offset + 1):
        out.append({
            "shelf_id": sid,
            "index": idx,
            "status": shelf_status_map.get(sid, "Unknown")
        })

    return jsonify({
        "rack": rack,
        "total": total,
        "offset": offset,
        "limit": limit,
        "shelves": out
    })


# -------------------------
# API: Get Dashboard Data
# -------------------------
@app.route('/api/get_data', methods=['GET'])
@login_required
def get_data():
    req_round_id = request.args.get('round_id')
    try:
        target_round = int(req_round_id) if req_round_id else CURRENT_ROUND_ID
    except:
        target_round = CURRENT_ROUND_ID

    logs = []
    inventory_logs = []
    rounds_available = set()

    try:
        with file_lock:

            # Load telemetry logs
            if os.path.exists(ROVER_FILE):
                with open(ROVER_FILE, 'r') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        try:
                            r_id = int(row.get('round_id', '1'))
                        except:
                            r_id = 1
                        rounds_available.add(r_id)
                        if r_id == target_round:
                            logs.append(row)

            # Load inventory logs
            if os.path.exists(INVENTORY_FILE):
                with open(INVENTORY_FILE, 'r') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        try:
                            r_id = int(row.get('round_id', '1'))
                        except:
                            r_id = 1
                        if r_id == target_round:
                            inventory_logs.append(row)

        latest = logs[-1] if logs else {}

        # compute uptime
        uptime = "00:00:00"
        start_time_str = "N/A"
        last_scan_str = inventory_logs[-1]['timestamp'] if inventory_logs else "N/A"

        if logs:
            fmt = '%Y-%m-%d %H:%M:%S'
            try:
                start = datetime.strptime(logs[0]['timestamp'], fmt)
                end = datetime.strptime(logs[-1]['timestamp'], fmt) if target_round != CURRENT_ROUND_ID else datetime.now()
                uptime = str(end - start).split('.')[0]
                start_time_str = logs[0]['timestamp']
            except:
                pass

        # Load racks dynamically
        racks = read_racks()
        if not racks:
            racks = {'A': 5, 'B': 5, 'C': 5, 'D': 5, 'E': 5}

        # Build scanned shelf map
        scanned_shelves_map = {}
        for rack, count in racks.items():
            for i in range(1, count + 1):
                sid = f"{rack}-{i:02d}"
                scanned_shelves_map[sid] = "Unknown"

        for row in inventory_logs:
            sid = row['shelf_id']
            scanned_shelves_map[sid] = row['shelf_status']

        empty_shelves = [sid for sid, status in scanned_shelves_map.items() if status.lower() == "empty"]

        # Build combined logs
        combined_logs = logs[:]
        for irow in inventory_logs:
            combined_logs.append({
                'timestamp': irow['timestamp'],
                'status': 'SCANNED',
                'current_task': 'Inventory Update',
                'coordinates': '--',
                'shelf_id': irow['shelf_id'],
                'shelf_status': irow['shelf_status'],
                'battery_level': '-',
                'cpu_temp': '-'
            })
        combined_logs.sort(key=lambda x: x.get('timestamp', ''))

        return jsonify({
            "current_round_id": CURRENT_ROUND_ID,
            "viewing_round_id": target_round,
            "available_rounds": sorted(list(rounds_available), reverse=True),
            "vitals": latest,
            "stats": {
                "uptime": uptime,
                "start_time": start_time_str,
                "last_scan": last_scan_str,
                "empty_shelves": empty_shelves,
                "scanned_shelves_map": scanned_shelves_map,
                "racks": racks
            },
            "logs": combined_logs[-20:][::-1]
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# -------------------------
# API: get racks
# -------------------------
@app.route('/api/get_racks', methods=['GET'])
@login_required
def get_racks():
    try:
        return jsonify({"racks": read_racks()})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# -------------------------
# Run Server
# -------------------------
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)

