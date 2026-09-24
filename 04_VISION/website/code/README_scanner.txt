RUN.PY - SHELF SCANNER EXECUTION HELPER
---------------------------------------

run.py is the main runner script for the Scanner class.
It provides an easy CLI interface to start a shelf-level scan,
choose pose modes (normal / top / bottom), and manage logging outputs.

BASIC USAGE
-----------
Run a normal scan on a shelf:
    python3 run.py --level 2 --log-console

Scan top shelf:
    python3 run.py --level 1 --top --log-console

Scan bottom shelf:
    python3 run.py --level 0 --bottom --log-console

FLAGS / ARGUMENTS
-----------------

--level <int>
    Mandatory. Shelf level number to scan.

--top
    Enables top-shelf pose mode.
    Vertical poses become (v = 0,1). Horizontal (0,1,2) unchanged.

--bottom
    Enables bottom-shelf pose mode.
    Vertical poses become (v = 0,1). Horizontal (0,1,2) unchanged.

--csv <path>
    Output CSV file where per-pose results are appended.
    Default: scan_results.csv

--json <path>
    Path to the unified JSON file containing cleaned aggregated results.
    Default: output.json

LOGGING CONTROLS
----------------

--log-console
    Print logs to terminal (INFO, WARN, ERROR, SUCCESS).

--log-file
    Save logs to a file (path configurable via --log-path).

--log-path <path>
    File path for log file if --log-file is enabled.
    Default: scanner.log

EXIT & CLEANUP
--------------
The script automatically:
    - Closes the camera
    - Returns servo to neutral (90,90)
    - Writes unified JSON
    - Finishes any open log actions

NOTES
-----
1. Scanner auto-initializes camera, detector, and servo on startup.
2. If servo is not connected or dry_run mode is enabled,
   scanning still proceeds using static camera captures.
3. Debug images and metadata are stored inside:
       debug/level_<id>/
   whenever debug mode is enabled inside Scanner.

SUMMARY
-------
Use run.py to trigger shelf scans quickly with CLI arguments.
For automation, logs, or integration with other systems,
adjust csv/json/log paths as needed.

---------------------------------------
END OF FILE
---------------------------------------







 warning <idx>
danger <idx>
mandatory <idx>
safe <idx>
bg <idx>
contrast <idx>
