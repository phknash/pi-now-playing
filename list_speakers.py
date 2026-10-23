"""
list_speakers.py - lists every Bose speaker on your network with its address,
unique ID (GUID) and Wi-Fi MAC address, so you can tell them apart.

Run it ON THE PI with:  python3 list_speakers.py
Then copy the GUID of the speaker you want into .env as  BOSE_GUID=...
"""

import subprocess
from pybose import BoseDiscovery

print("Searching for Bose speakers (10 seconds)...")
devices = BoseDiscovery().discover_devices(timeout=10)

if not devices:
    print("No Bose speakers found. Are they awake and on Wi-Fi?")

for device in devices:
    ip, guid = device["IP"], device["GUID"]

    # Ping the speaker so the Pi learns its MAC address, then look it up
    subprocess.run(["ping", "-c", "1", "-W", "1", ip], capture_output=True)
    neighbour = subprocess.run(["ip", "neigh", "show", ip], capture_output=True, text=True).stdout.split()
    mac = neighbour[neighbour.index("lladdr") + 1] if "lladdr" in neighbour else "unknown"

    print(f"\n  Address: {ip}\n  GUID:    {guid}\n  MAC:     {mac.upper()}")
