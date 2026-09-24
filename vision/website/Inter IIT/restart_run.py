import sys
import subprocess
from pathlib import Path

#!/usr/bin/env python3

HERE = Path(__file__).resolve().parent
FILES = ["./data/inventory.csv", "./data/rover_data.csv", "./data/racks.csv"]

for name in FILES:
    p = HERE / name
    try:
        p.unlink()
        print(f"Deleted: {p}")
    except FileNotFoundError:
        print(f"Not found (skipping): {p}")
    except Exception as e:
        print(f"Failed to delete {p}: {e}", file=sys.stderr)

app = HERE / "app.py"
if not app.exists():
    print(f"app.py not found at {app}", file=sys.stderr)
    sys.exit(1)

# Run app.py with the same Python interpreter
ret = subprocess.run([sys.executable, str(app)])
sys.exit(ret.returncode)