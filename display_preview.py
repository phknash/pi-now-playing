"""
display_preview.py - Tasks 10 & 11 of the Pi "now playing" display.

Every 15 seconds it asks the Bose (and Spotify) what's playing. When the song changes,
it draws the picture the e-paper screen WILL show and saves it as
preview.png, so you can design the screen before the hardware arrives.

Run it with:  python3 display_preview.py      (press Ctrl + C to stop)
"""

import os
import sys
import time
import subprocess
from io import BytesIO

import requests                                   # downloads the album cover
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont       # Pillow: draws the picture
from sources import get_now_playing           # our own file: asks the Bose (and Spotify)

# ---- The e-paper screen (only exists on the Pi) ---------------------------
# Try to load the screen driver. On the Mac it isn't there, so Python raises
# an ImportError - we catch it and remember that we're NOT on the Pi.
try:
    from waveshare_epd import epd3in7
    epd = epd3in7.EPD()        # our handle on the screen - created once, reused for every song
    ON_PI = True
except ImportError:
    ON_PI = False

# ---- Settings you can play with -------------------------------------------
SCREEN_WIDTH = 480      # the 2.7" e-paper screen is 264 x 176 pixels
SCREEN_HEIGHT = 280     # (a 4.2" screen would be 400 x 300)
CHECK_EVERY = 10        # seconds between asking Spotify
PREVIEW_ZOOM = 5        # makes preview.png 3x bigger so it's easy to see

load_dotenv()


def wrap_text(draw, text, font, max_width, max_lines):
    """Split text into lines that fit the width. Adds '...' if it's too long."""
    words = text.split()
    lines, current = [], ""
    for word in words:
        attempt = f"{current} {word}".strip()
        if draw.textlength(attempt, font=font) <= max_width:
            current = attempt
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)

    if len(lines) > max_lines:
        lines = lines[:max_lines]
        last = lines[-1]
        while draw.textlength(last + "...", font=font) > max_width and last:
            last = last[:-1]
        lines[-1] = last.rstrip() + "..."
    return lines


def draw_screen(info):
    """Draw the greyscale picture for the e-paper screen."""
    # "1" means 1-bit: every pixel is either black (0) or white (255), "L" any shade of grey from black to white
    image = Image.new("L", (SCREEN_WIDTH, SCREEN_HEIGHT), 255)
    draw = ImageDraw.Draw(image)

    small = ImageFont.load_default(size=12)
    big = ImageFont.load_default(size=32)
    medium = ImageFont.load_default(size=22)

    if info is None:
        draw.text((SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2), "Nothing playing",
                  font=big, fill=0, anchor="mm")
        return image

    # --- Album cover on the left ---
    cover_size = 256
    cover_x, cover_y = 8, (SCREEN_HEIGHT - cover_size) // 2
    if info["cover_url"]:
        try:
            response = requests.get(info["cover_url"], timeout=10)
            cover = Image.open(BytesIO(response.content)).convert("L")  # greyscale
            cover = cover.resize((cover_size, cover_size))
            image.paste(cover, (cover_x, cover_y))
        except Exception as error:
            print("Cover problem:", error)
            draw.rectangle([cover_x, cover_y, cover_x + cover_size, cover_y + cover_size], outline=0)
    draw.rectangle([cover_x - 1, cover_y - 1, cover_x + cover_size, cover_y + cover_size], outline=0)

    # --- Text on the right ---
    text_x = cover_x + cover_size + 10
    text_width = SCREEN_WIDTH - text_x - 6
    y = cover_y

    draw.text((text_x, y), "NOW PLAYING", font=small, fill=0)
    y += 18

    for line in wrap_text(draw, info["title"], big, text_width, 3):
        draw.text((text_x, y), line, font=big, fill=0)
        y += 32
    y += 6

    for line in wrap_text(draw, info["artist"], medium, text_width, 2):
        draw.text((text_x, y), line, font=medium, fill=0)
        y += 24

    # Device name along the bottom
    device_lines = wrap_text(draw, "on " + info["device"], small, text_width, 1)
    draw.text((text_x, cover_y + cover_size - 12), device_lines[0], font=small, fill=0)

    return image


def show(image):
    """On the Pi: send the picture to the e-paper screen. On the Mac: save and open a preview."""
    if ON_PI:
        epd.init(0)                                     # 1. wake the screen in 4-grey mode (full refresh)
        image = image.rotate(angle=180)                 # 2. rotate the image 180 degrees
        epd.display_4Gray(epd.getbuffer_4Gray(image))   # 3. send the picture - flashes to wipe the old one
        epd.sleep()                                     # 4. back to sleep until the next song
    else:
        big = image.resize((SCREEN_WIDTH * PREVIEW_ZOOM, SCREEN_HEIGHT * PREVIEW_ZOOM), Image.NEAREST)
        big.save("preview.png")
        if sys.platform == "darwin":               # on a Mac, open it in Preview
            subprocess.run(["open", "preview.png"])


# ---- The main loop: check, compare, redraw only if something changed ------
print("Watching the Bose... press Ctrl + C to stop.")
last_id = "start"

while True:
    try:
        info = get_now_playing()
        current_id = info["id"] if info else None

        if current_id != last_id:           # only redraw when the song changes
            if info:
                print(f"New: {info['title']} - {info['artist']}")
            else:
                print("Nothing playing")
            show(draw_screen(info))
            last_id = current_id

    except Exception as error:
        # No internet, Spotify hiccup etc. - print it and try again next time
        print(f"Problem getting what's playing, will retry: {error}")

    time.sleep(CHECK_EVERY)
