# Eternal Rover Mission Control — Inter IIT Tech Meet 14.0

A compact mission-control dashboard for the Autonomous Rover. Visualizes real-time telemetry, manages mission rounds, and maps warehouse inventory (Racks A–F) from Jetson Nano POSTs.

---

## Table of Contents
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Accessing the Dashboard](#accessing-the-dashboard)
- [API / Jetson Nano Integration](#api--jetson-nano-integration)
- [Payload Fields](#payload-fields)
- [Examples](#examples)
- [Warehouse Configuration](#warehouse-configuration)

---

## Quick Start

Recommended: create and activate a virtual environment, then install dependencies.

```pwsh
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Two ways to run:

- Fresh start (clears old CSVs and restarts):

```pwsh
python restart_run.py
```

- Resume mission (keep existing data):

```pwsh
python app.py
```

---

## Project Structure

- `app.py` — Main Flask server and API handlers.
- `restart_run.py` — Utility to clear data and restart a fresh session.
- `test.py` — Simulator to exercise the dashboard without hardware.
- `templates/` — HTML templates (e.g., `dashboard.html`, `dashboard_login.html`).
- `*.csv` — Generated data files (e.g., `rover_data.csv`, `inventory.csv`).

---

## Accessing the Dashboard

Open a browser to:

```
http://localhost:5000
```

Default login

```
Username: admin
Password: password
```

---

## API / Jetson Nano Integration

Endpoint: `POST /api/update`

Content-Type: `application/json`

This endpoint accepts telemetry and inventory scan updates. All fields are optional; include the fields you have available.

### Payload Fields

| Field | Type | Description | Example |
|---|---:|---|---|
| `battery_level` | number | Battery percentage (0–100) | `88.5` |
| `cpu_temp` | number | CPU temperature in °C | `45.2` |
| `status` | string | Short status message | `"Scanning"` |
| `current_task` | string | Current task description | `"Moving to Rack B"` |
| `coordinates` | string | Position as `x, y` | `"12.5, 4.0"` |
| `shelf_id` | string | Inventory slot identifier (Rack-Level) — e.g. `A-05` | `"A-05"` |
| `shelf_status` | string | Shelf state: `Empty` or `Full` | `"Empty"` |
| `new_round` | boolean | If `true`, forces a new mission round | `true` |

---

## Examples

1) Telemetry-only update (Python requests):

```python
import requests

SERVER_URL = "http://<DASHBOARD_IP>:5000/api/update"

payload = {
    "battery_level": 75.0,
    "cpu_temp": 55.0,
    "status": "Navigating",
    "coordinates": "1.2, 3.4"
}

requests.post(SERVER_URL, json=payload)
```

2) Shelf scan update (updates visual grid):

```python
scan_payload = {
    "status": "Scanning",
    "shelf_id": "C-03",      # Valid: A-01 to F-05
    "shelf_status": "Empty"  # Will mark the box as empty on the dashboard
}
requests.post(SERVER_URL, json=scan_payload)
```

3) Start a new round (reset map):

```python
requests.post(SERVER_URL, json={"new_round": True})
```

---

## Warehouse Configuration

Default layout (Inter IIT blueprint):

- Racks: `A`, `B`, `C`, `D`, `E`, `F` (6 racks)
- Levels per rack: `01` to `05` (5 levels)
- Total slots: 30

To change these values, edit the `WAREHOUSE_MAPPING` (or relevant constants) in `app.py`.

---

If you want, I can:
- Add a short curl example for testing the API from a terminal.
- Add a Dockerfile to containerize the dashboard.
- Convert this README into a more detailed developer guide.

Generated and formatted for readability.