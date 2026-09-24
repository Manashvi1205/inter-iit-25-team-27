import requests
import time
import random
import sys

# =========================================================
# Configuration
# =========================================================
SERVER_URL = "http://127.0.0.1:8000/api/update"

# Generate shelves R01-01 to R06-05
SHELVES = [
    f"{row}-{num:02d}"
    for row in ['R01', 'R02', 'R03', 'R04', 'R05', 'R06']
    for num in range(1, 6)
]

STATUS_OPTIONS = ["Full", "Full", "Full", "Empty"]

# =========================================================
# Simulator
# =========================================================
def simulate_rover():
    print(f"🚀 Connecting to Rover Backend at {SERVER_URL}...")

    # -----------------------------------------------------
    # STEP 1: Initialize new round
    # -----------------------------------------------------
    print("🔄 Sending Round Initialization Command...")
    try:
        init_payload = {
            "new_round": True,
            "status": "Initializing",
            "current_task": "System Boot - New Mission",
            "coordinates": "0.0, 0.0"
        }

        resp = requests.post(SERVER_URL, json=init_payload, timeout=3)
        if resp.status_code == 200:
            print(f"✅ New Round Initialized: {resp.json()}")
        else:
            print(f"⚠️ Server returned error: {resp.status_code}")

    except requests.exceptions.ConnectionError:
        print("❌ CRITICAL ERROR: Could not connect to server.")
        print("   → Make sure app.py is running.")
        return

    # -----------------------------------------------------
    # STEP 2: Mission loop
    # -----------------------------------------------------
    battery = 100.0
    x, y = 0.0, 0.0
    shelf_index = 0

    print("🤖 Rover Mission Started. Press Ctrl+C to stop.")

    i = 0
    try:
        while i < 90:
            battery = max(0, battery - 0.2)
            x += random.uniform(-0.5, 0.5)
            y += random.uniform(0, 0.5)

            payload = {
                "battery_level": round(battery, 1),
                "cpu_temp": round(random.uniform(45.0, 60.0), 1),
                "status": "Navigating",
                "current_task": "Moving to next rack",
                "coordinates": f"{x:.1f}, {y:.1f}"
            }

            # 40% chance of scan
            if random.random() < 0.4:
                current_shelf = SHELVES[shelf_index % len(SHELVES)]
                item_code = "ITM" + str(random.randint(100, 999))

                payload["status"] = "Scanning"
                payload["current_task"] = f"Inspecting {current_shelf}"

                # ✅ BACKEND EXPECTS THIS FORMAT ONLY
                payload["payload"] = (
                    current_shelf.split("-")[0] + "_" +
                    current_shelf.split("-")[1] + "_" +
                    item_code
                )

                print(f"📸 SCANNED: {current_shelf} -> {item_code}")
                shelf_index += 1
                i += 1
            else:
                print(f"📡 Telemetry: Bat {payload['battery_level']}% | Pos {payload['coordinates']}")

            try:
                requests.post(SERVER_URL, json=payload, timeout=5)
            except requests.exceptions.ConnectionError:
                print("⚠️ Connection lost... retrying")

            time.sleep(0.8)

    except KeyboardInterrupt:
        print("\n🛑 Simulation stopped by user.")

# =========================================================
# Entry point
# =========================================================
if __name__ == "__main__":
    simulate_rover()
