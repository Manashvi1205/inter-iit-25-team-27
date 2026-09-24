#!/usr/bin/env python3

import sys
import subprocess
from pathlib import Path

# =========================================================
# Base directory (same folder as this script)
# =========================================================
HERE = Path(__file__).resolve().parent

# =========================================================
# Files to clean (SAFE)
# =========================================================
FILES = [
    "data/inventory.csv",
    "data/rover_data.csv",
    "data/racks.csv",
]

print("[INFO] Cleaning old data files...")

for name in FILES:
    p = HERE / name
    try:
        p.unlink()
        print(f"[OK] Deleted: {p}")
    except FileNotFoundError:
        print(f"[SKIP] Not found: {p}")
    except Exception as e:
        print(f"[WARN] Failed to delete {p}: {e}", file=sys.stderr)

# =========================================================
# Launch app.py (SAFE)
# =========================================================
app = HERE / "app.py"

if not app.exists():
    print(f"[ERROR] app.py not found at: {app}", file=sys.stderr)
    print("[HINT] Make sure this script is in the same directory as app.py")
    sys.exit(1)

print(f"[INFO] Starting app: {app}")

try:
    ret = subprocess.run(
        [sys.executable, str(app)],
        check=False
    )
    sys.exit(ret.returncode)

except KeyboardInterrupt:
    print("\n[INFO] Interrupted by user")
    sys.exit(130)

except Exception as e:
    print(f"[FATAL] Failed to start app.py: {e}", file=sys.stderr)
    sys.exit(1)
