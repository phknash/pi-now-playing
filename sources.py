"""
sources.py - works out what's playing on the Bose, from any source.

1. Ask the Bose speaker what it's playing (works for AirPlay, Spotify, radio...).
2. Tidy up the messy text some apps send (radio stations, "Video Available").
3. If Spotify is playing the same song, use Spotify's cleaner details and cover.

Other scripts use it with:  from sources import get_now_playing
"""

import os
import asyncio
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from pybose import BoseAuth, BoseSpeaker

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

# ---- Bose login: done once, then reused -----------------------------------
BOSE_IP = os.getenv("BOSE_IP")
bose_auth = BoseAuth()
bose_logged_in = False

# Extra labels some apps tack onto the artist, which we don't want on screen
JUNK_LABELS = {"Video Available", "Explicit"}
SEPARATOR = " • "      # " • " - the dot apps use to squeeze two things into one field


async def ask_bose():
    """Connect to the speaker, ask what's playing, hang up. Returns Bose's raw reply."""
    speaker = BoseSpeaker(host=BOSE_IP, bose_auth=bose_auth)
    await speaker.connect()
    reply = await speaker.get_now_playing()
    try:
        await asyncio.wait_for(speaker.disconnect(), timeout=3)   # pybose bug workaround
    except (asyncio.TimeoutError, Exception):
        pass
    return reply


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
    global bose_logged_in
    if not bose_logged_in:
        bose_auth.getControlToken(os.getenv("BOSE_EMAIL"), os.getenv("BOSE_PASSWORD"))
        bose_logged_in = True

    try:
        reply = asyncio.run(ask_bose())
    except Exception:
        return None            # speaker asleep, off Wi-Fi or out of range

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
