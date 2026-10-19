"""
now_playing.py - prints what's currently playing on your Spotify account.

Tasks 7-8 of the Pi "now playing" display project.
Run it with:  python3 now_playing.py
"""

import os                                   # lets us read settings from the computer
from dotenv import load_dotenv              # reads your secret settings from the .env file
import spotipy                              # the library that talks to Spotify for us
from spotipy.oauth2 import SpotifyOAuth     # handles the "log in to Spotify" part

# 1. Load your Client ID, Secret and Redirect URI from the .env file,
#    so they never have to be written inside this script.
load_dotenv()

# 2. Say what we want permission to see. These "scopes" are what you'll
#    be asked to approve in the browser the first time you run this.
SCOPES = "user-read-currently-playing user-read-playback-state"

# 3. Create a Spotify connection. The first time, this opens your browser
#    to log in. After that, it remembers you using a small ".cache" file.
sp = spotipy.Spotify(
    auth_manager=SpotifyOAuth(
        client_id=os.getenv("SPOTIFY_CLIENT_ID"),
        client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
        redirect_uri=os.getenv("SPOTIFY_REDIRECT_URI"),
        scope=SCOPES,
    )
)

# 4. Ask Spotify: "what's playing right now, and on which device?"
playback = sp.current_playback(additional_types="episode")

# 5. Work out what to print.
if playback is None or playback.get("item") is None:
    # Spotify returns nothing when nothing is playing (or it's been paused a while)
    print("Nothing is playing right now.")
else:
    item = playback["item"]
    device = playback["device"]["name"]
    status = "Playing" if playback["is_playing"] else "Paused"

    if item["type"] == "track":
        # A song: join multiple artists with commas, e.g. "Artist A, Artist B"
        artists = ", ".join(artist["name"] for artist in item["artists"])
        album = item["album"]["name"]
        cover_url = item["album"]["images"][0]["url"] if item["album"]["images"] else "none"
        print(f"{status} on {device}")
        print(f"  Song:   {item['name']}")
        print(f"  Artist: {artists}")
        print(f"  Album:  {album}")
        print(f"  Cover:  {cover_url}")
    else:
        # A podcast episode looks different, so handle it separately
        print(f"{status} on {device}")
        print(f"  Podcast: {item['show']['name']}")
        print(f"  Episode: {item['name']}")
