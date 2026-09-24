# process the input data 

'''
FLOW:
Input-> raw:  Payload; global_centroid; Scan_ID(/number/index/( assume a random unique number which i give))
1.) read this data store this input into log_file.txt ( just append mode)
2.)  separate the payload into different variables ( rack_id, shelf , item)
3.) now look for this item in inventory.csv file (try to look for exact payload)
--> If not found => (new item/at/new/location detected) store this item with: Scan_ID, timestamp,
                      payload, location(rack,shelf), item_id and centroid append mode in inventory.csv
--> If found => The same item already exists in inventory.csv, then check distance between centroids
                    ---> just pass the centroids of both to the check_dist function ( leave the implementationf or now)
                Two cases:
                1.) if distance < threshold => same location => IGNORE ( Just log it ( already done ))
                2.) if distance > threshold => different(more quantity) item => store it in the csv with all the data(rack,shelf,centroid etc etc)

4.) return status msg to caller and exit



// (the parent of this functions should use the return status and based on that send a POST REQUEST ON WEBSITE... WILL DO THAT LATER!!!)

'''

import csv
import os
import math
from datetime import datetime

# ==========================================================
# UTILS
# ==========================================================
def ensure_file(path):
    """Creates an empty file if not exists."""
    if not os.path.exists(path):
        with open(path, "w") as f:
            pass


def log_raw_input(log_path, raw_payload, centroid, scan_id):
    """Append raw input event into log file."""
    ensure_file(log_path)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_path, "a") as f:
        f.write(f"{ts} | scan_id={scan_id} | payload={raw_payload} | centroid={centroid}\n")


def parse_payload(payload):
    """
    Payload format: R03_S4_ITM240
    Returns:
        rack="R03"
        shelf="S4"
        item="ITM240"
    """
    try:
        parts = payload.split("_")
        rack = parts[0]       # R03
        shelf = parts[1]      # S4
        item = parts[2]       # ITM240
        return rack, shelf, item
    except:
        return None, None, None


def check_dist(c1, c2, threshold=4.0):
    """Euclidean distance in percentage coordinate space."""
    dx = c1[0] - c2[0]
    dy = c1[1] - c2[1]
    d = math.sqrt(dx*dx + dy*dy)
    return d, d <= threshold


def read_inventory(csv_path):
    """Read inventory CSV as list of dicts."""
    if not os.path.exists(csv_path):
        return []

    entries = []
    with open(csv_path, "r") as f:
        rdr = csv.DictReader(f)
        for row in rdr:
            row["cx_pct"] = float(row["cx_pct"])
            row["cy_pct"] = float(row["cy_pct"])
            entries.append(row)
    return entries


def append_inventory(csv_path, row_dict):
    """Append one item row; create CSV with header if new."""
    new_file = not os.path.exists(csv_path)
    with open(csv_path, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "scan_id", "timestamp", "payload", "rack", "shelf", "item", "cx_pct", "cy_pct"
        ])
        if new_file:
            writer.writeheader()
        writer.writerow(row_dict)


# ==========================================================
# MAIN PROCESSOR
# ==========================================================
def process_scan_input(
    raw_payload,
    global_centroid,   # tuple (cx_pct, cy_pct)
    scan_id,
    log_file="log_file.txt",
    inv_file="inventory.csv",
    threshold=4.0
):
    """
    Workflow:
    1) Log input
    2) Parse payload
    3) Load inventory file
    4) Check if same item exists
    5) If new → save
    6) If exists → check centroid distance
           - close → ignore
           - far   → treat as new location
    Returns status dict.
    """

    # -----------------------------------
    # 1. LOG INPUT
    # -----------------------------------
    log_raw_input(log_file, raw_payload, global_centroid, scan_id)

    # -----------------------------------
    # 2. PARSE PAYLOAD
    # -----------------------------------
    rack, shelf, item = parse_payload(raw_payload)
    if rack is None:
        return {"status": "ERR_BAD_PAYLOAD"}

    cx, cy = global_centroid

    # -----------------------------------
    # 3. LOAD EXISTING INVENTORY
    # -----------------------------------
    inv = read_inventory(inv_file)

    # filter all rows with same item id
    same_item_entries = [r for r in inv if r["item"] == item]

    # ====================================================
    # CASE A: ITEM NEVER SEEN BEFORE → CREATE ENTRY
    # ====================================================
    if len(same_item_entries) == 0:
        row = {
            "scan_id": scan_id,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "payload": raw_payload,
            "rack": rack,
            "shelf": shelf,
            "item": item,
            "cx_pct": cx,
            "cy_pct": cy
        }
        append_inventory(inv_file, row)
        return {"status": "NEW_ITEM_CREATED", "data": row}

    # ====================================================
    # CASE B: FOUND SAME ITEM → CHECK CENTROID
    # ====================================================
    for entry in same_item_entries:
        old_c = (entry["cx_pct"], entry["cy_pct"])
        dist, is_same = check_dist(global_centroid, old_c, threshold)

        if is_same:
            # same location → ignore
            return {"status": "SAME_LOCATION_IGNORE", "distance": dist}

    # ====================================================
    # CASE C: SAME ITEM BUT DIFFERENT LOCATION → ADD NEW
    # ====================================================
    row = {
        "scan_id": scan_id,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "payload": raw_payload,
        "rack": rack,
        "shelf": shelf,
        "item": item,
        "cx_pct": cx,
        "cy_pct": cy
    }
    append_inventory(inv_file, row)
    return {"status": "NEW_LOCATION_ADDED", "data": row}
