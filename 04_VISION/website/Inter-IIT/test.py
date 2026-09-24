import requests
import time
import random
import sys

# Configuration
# Ensure this matches your Flask IP (localhost if running on same machine)
SERVER_URL = "http://127.0.0.1:5000/api/update"

# Generate shelves A-01 to F-05
SHELVES = [f"{row}-{num:02d}" for row in ['A', 'B', 'C', 'D', 'E', 'F'] for num in range(1, 6)] 
STATUS_OPTIONS = ["Full", "Full", "Full", "Empty"] 

def simulate_rover():
    print(f"🚀 Connecting to Rover Backend at {SERVER_URL}...")
    
    # --- STEP 1: INITIALIZE NEW ROUND ---
    print("🔄 Sending Round Initialization Command...")
    try:
        init_payload = {
            "new_round": True,
            "status": "Initializing",
            "current_task": "System Boot - New Mission",
            "coordinates": "0.0, 0.0"
        }
        resp = requests.post(SERVER_URL, json=init_payload, timeout=2)
        if resp.status_code == 200:
            print(f"✅ New Round Initialized! (Server said: {resp.json()})")
        else:
            print(f"⚠️ Server returned error: {resp.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ CRITICAL ERROR: Could not connect to server.")
        print("   -> Make sure 'app.py' is running in another terminal.")
        return

    # --- STEP 2: MISSION LOOP ---
    battery = 100.0
    x, y = 0.0, 0.0
    shelf_index = 0
    
    print("🤖 Rover Mission Started. Press Ctrl+C to stop.")
    
    try:
        while True:
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

            # increased chance to 40% for faster updates on UI
            if random.random() < 0.4:
                current_shelf = SHELVES[shelf_index % len(SHELVES)]
                shelf_status = random.choice(STATUS_OPTIONS)
                
                payload["status"] = "Scanning"
                payload["current_task"] = f"Inspecting {current_shelf}"
                payload["shelf_id"] = current_shelf
                payload["shelf_status"] = shelf_status
                
                print(f"📸 SCANNED: {current_shelf} -> {shelf_status}")
                shelf_index += 1
            else:
                # Just telemetry
                print(f"📡 Telemetry: Bat {payload['battery_level']}% | Pos {payload['coordinates']}")

            try:
                requests.post(SERVER_URL, json=payload, timeout=1)
            except requests.exceptions.ConnectionError:
                print("⚠️ Connection lost... retrying")
            
            # Faster tick rate (0.8s) for smoother UI
            time.sleep(0.8)

    except KeyboardInterrupt:
        print("\n🛑 Simulation stopped by user.")

if __name__ == "__main__":
    simulate_rover()