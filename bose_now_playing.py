"""
bose_now_playing.py - asks your Bose speaker directly what it's playing,
whatever the source (Spotify, AirPlay, Bluetooth...).

Uses pybose, a library written by Bose fans (not by Bose). It needs your
Bose account email and password in the .env file.

Run it with:  python3 bose_now_playing.py
"""

import os
import json
import asyncio                                  # pybose needs this (see note at the bottom)
from dotenv import load_dotenv
from pybose import BoseAuth, BoseDiscovery, BoseSpeaker

load_dotenv()


async def main():
    # 1. Work out where the speaker is.
    #    If you've put BOSE_IP in your .env file, use that. Otherwise search for it.
    if os.getenv("BOSE_IP"):
        speaker_ip, speaker_id = os.getenv("BOSE_IP"), None   # the ID is learned on connect
        print(f"Using the speaker address from .env: {speaker_ip}")
    else:
        print("Looking for Bose speakers on your network (10 seconds)...")
        devices = BoseDiscovery().discover_devices(timeout=10)
        if not devices:
            print("No Bose speakers found. Is the speaker awake and on Wi-Fi?")
            print("Tip: add BOSE_IP=<speaker address> to your .env file to skip searching.")
            return
        speaker_ip, speaker_id = devices[0]["IP"], devices[0]["GUID"]
        print(f"Found a speaker at {speaker_ip}")

    # 2. Log in to your Bose account. Oddly, Bose requires this even to
    #    talk to your speaker over your own home network.
    auth = BoseAuth()
    auth.getControlToken(os.getenv("BOSE_EMAIL"), os.getenv("BOSE_PASSWORD"))

    # 3. Connect to the speaker and ask what's playing
    speaker = BoseSpeaker(host=speaker_ip, device_id=speaker_id, bose_auth=auth)
    await speaker.connect()
    now = await speaker.get_now_playing()

    # 4. Pull out the parts we care about. ".get(..., {})" means
    #    "use an empty box if Bose didn't send this part" - so it won't crash.
    meta = now.get("metadata") or {}
    source = (now.get("source") or {}).get("sourceDisplayName", "Unknown source")
    status = (now.get("state") or {}).get("status", "unknown")
    art = ((now.get("track") or {}).get("contentItem") or {}).get("containerArt") \
        or ((now.get("container") or {}).get("contentItem") or {}).get("containerArt")

    if not meta.get("trackName"):
        print(f"Nothing with song details is playing (source: {source}, status: {status}).")
    else:
        print(f"{status} from {source}")
        print(f"  Song:   {meta.get('trackName')}")
        print(f"  Artist: {meta.get('artist', '-')}")
        print(f"  Album:  {meta.get('album', '-')}")
        print(f"  Cover:  {art or 'none sent'}")

    # 5. Everything Bose sent back, for exploring what's available
    print("\nFull reply from the speaker:")
    print(json.dumps(now, indent=2))

    # 6. Hang up. pybose has a bug where this can wait forever, so we give it
    #    3 seconds and then move on anyway.
    try:
        await asyncio.wait_for(speaker.disconnect(), timeout=3)
    except (asyncio.TimeoutError, Exception):
        pass


# pybose is "asynchronous": it can wait for the speaker without freezing.
# asyncio.run() starts that machinery and runs main().
asyncio.run(main())
