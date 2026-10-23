"""
sources.py - works out what's playing on the Bose, from any source.

1. Ask the Bose speaker what it's playing (works for AirPlay, Spotify, radio...).
2. Tidy up the messy text some apps send (radio stations, "Video Available").
3. If Spotify is playing the same song, use Spotify's cleaner details and cover.

Other scripts use it with:  from sources import get_now_playing
"""

import os
import time
import asyncio
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from pybose import BoseAuth, BoseSpeaker, BoseDiscovery

load_dotenv()

# ---- Spotify connection (same as before) ----------------------------------
sp = spotipy.Spotify(
    auth_manager=SpotifyOAuth(
        client_id=os.getenv("SPOTIFY_CLIENT_ID"),
        client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
        redirect_uri=os.getenv("SPOTIFY_REDIRECT_URI"),
        scope="user-read-currently-playing user-read-playback-state",
    )
)

# ---- Bose connection -------------------------------------------------------
BOSE_IP = os.getenv("BOSE_IP")      # starting guess - may go out of date after a router restart
BOSE_GUID = os.getenv("BOSE_GUID")  # the speaker's unique ID - picks the right one if you have several Bose
bose_auth = BoseAuth()
SEARCH_EVERY = 120                  # if the speaker can't be reached, search for it at most every 2 minutes
last_search = 0                     # when we last searched (0 = never)

# Extra labels some apps tack onto the artist, which we don't want on screen
JUNK_LABELS = {"Video Available", "Explicit"}
SEPARATOR = " • "      # " • " - the dot apps use to squeeze two things into one field


async def ask_bose(ip):
    """Connect to the speaker at this address, ask what's playing, hang up. Returns Bose's raw reply."""
    speaker = BoseSpeaker(host=ip, bose_auth=bose_auth)
    await speaker.connect()
    try:
        # Check it's the right speaker (a different Bose could now have this address)
        found_id = speaker.get_device_id()
        if BOSE_GUID and found_id and found_id.lower() != BOSE_GUID.lower():
            raise RuntimeError(f"the Bose at {ip} is a different speaker ({found_id})")
        reply = await speaker.get_now_playing()
    finally:
        try:
            await asyncio.wait_for(speaker.disconnect(), timeout=3)   # pybose bug workaround
        except (asyncio.TimeoutError, Exception):
            pass
    return reply


def find_speaker():
    """Search the network for OUR Bose speaker. Returns its address, or None if not found."""
    global last_search
    last_search = time.time()
    print("Searching for the Bose speaker...")
    devices = BoseDiscovery().discover_devices(timeout=10)

    if BOSE_GUID:
        # Only keep the speaker whose ID matches the one in .env
        devices = [d for d in devices if (d.get("GUID") or "").lower() == BOSE_GUID.lower()]
    elif len(devices) > 1:
        # Several Bose found and we don't know which is ours - don't guess
        print("Found more than one Bose speaker. Run list_speakers.py and add BOSE_GUID to .env")
        return None

    if not devices:
        print("Couldn't find the Bose speaker (is it awake and on Wi-Fi?)")
        return None
    ip = devices[0]["IP"]
    print(f"Found the Bose speaker at {ip}")
    return ip


def ask_bose_finding_it_if_needed():
    """Ask the speaker what's playing. If it can't be reached, search for it and try once more."""
    global BOSE_IP

    # First go: use the address we already know (if we know one)
    if BOSE_IP:
        try:
            return asyncio.run(ask_bose(BOSE_IP))
        except Exception as error:
            print(f"Couldn't reach the Bose at {BOSE_IP}: {error}")

    # Couldn't reach it - search, but not more than once every SEARCH_EVERY seconds,
    # otherwise a sleeping speaker would make us search non-stop.
    if time.time() - last_search < SEARCH_EVERY:
        return None
    new_ip = find_speaker()
    if not new_ip:
        return None
    if new_ip != BOSE_IP:
        print(f"Speaker address changed: {BOSE_IP} -> {new_ip} (update BOSE_IP in .env to match)")
        BOSE_IP = new_ip

    # Second go, at the address we just found
    try:
        return asyncio.run(ask_bose(BOSE_IP))
    except Exception as error:
        print(f"Found the speaker but couldn't talk to it: {error}")
        return None


def tidy_up(title, artist):
    """Clean up the text apps send. Returns (title, artist, station)."""
    parts = [p for p in artist.split(SEPARATOR) if p not in JUNK_LABELS]
    artist = SEPARATOR.join(parts)
    station = None

    # Radio sends e.g. artist "Live • Classic FM Calm", title "Communion • Stephan Moccio"
    if artist.startswith("Live" + SEPARATOR):
        station = artist[len("Live" + SEPARATOR):]
        if SEPARATOR in title:
            title, artist = title.split(SEPARATOR, 1)
        else:
            artist = station
    return title, artist, station


def ask_spotify_for_better_details(title):
    """If Spotify is playing this same song, return its (artist, cover_url). Otherwise None."""
    try:
        playback = sp.current_playback()
    except Exception:
        return None
    if not playback or not playback.get("item") or playback["item"].get("type") != "track":
        return None
    item = playback["item"]
    if item["name"].lower().strip() != title.lower().strip():
        return None            # Spotify is playing something else, so ignore it
    images = item["album"]["images"]
    artist = ", ".join(a["name"] for a in item["artists"])
    return artist, (images[0]["url"] if images else None)


def get_now_playing():
    """What's playing on the Bose? Returns a dictionary for draw_screen(), or None."""
    # Make sure we have a valid Bose login. The login "token" expires after a while;
    # getControlToken reuses it while it's valid, and refreshes it when it isn't.
    try:
        bose_auth.getControlToken(os.getenv("BOSE_EMAIL"), os.getenv("BOSE_PASSWORD"))
    except Exception as error:
        print(f"Bose login problem: {error}")
        return None

    reply = ask_bose_finding_it_if_needed()
    if reply is None:
        return None            # speaker asleep, off Wi-Fi or can't be found

    meta = reply.get("metadata") or {}
    if not meta.get("trackName"):
        return None            # nothing playing, or a source with no details (e.g. TV)

    source = (reply.get("source") or {}).get("sourceDisplayName", "Bose")
    cover = ((reply.get("track") or {}).get("contentItem") or {}).get("containerArt") \
        or ((reply.get("container") or {}).get("contentItem") or {}).get("containerArt")

    title, artist, station = tidy_up(meta["trackName"], meta.get("artist", ""))

    better = ask_spotify_for_better_details(title)
    if better:
        artist, spotify_cover = better
        cover = spotify_cover or cover
        source = "Spotify"

    return {
        "id": f"{title}|{artist}",          # no song ID from Bose, so name + artist will do
        "title": title,
        "artist": artist,
        "cover_url": cover,
        "device": station or source,         # shows as "on Classic FM Calm" / "on AirPlay"
    }


# Run this file on its own to test it:  python3 sources.py
if __name__ == "__main__":
    print(get_now_playing())
