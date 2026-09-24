import random
from process_data import process_scan_input
def random_payload():
    rack = f"R{random.randint(1,9):02d}"
    shelf = f"S{random.randint(1,5)}"
    item = f"ITM{random.randint(100,999)}"
    return f"{rack}_{shelf}_{item}"

def random_centroid():
    return (round(random.uniform(5,95), 2), 
            round(random.uniform(5,95), 2))

# -------------------------------
# TESTING LOOP
# -------------------------------
for i in range(10):
    payload = random_payload()
    centroid = random_centroid()
    scan_id = f"SCAN_{1000+i}"

    result = process_scan_input(
        raw_payload=payload,
        global_centroid=centroid,
        scan_id=scan_id
    )

    print(f"\nTest {i+1}:")
    print("Payload:", payload)
    print("Centroid:", centroid)
    print("Result:", result)
