"""
test_screen.py - checks the 3.7" e-paper screen works, before we involve Spotify or the Bose.

Run it ON THE PI with:  python3 test_screen.py
"""

from PIL import Image, ImageDraw, ImageFont
from waveshare_epd import epd3in7          # Waveshare's driver for this exact screen

epd = epd3in7.EPD()        # "epd" = electronic paper display - our handle on the screen
epd.init(1)                # wake it up in black & white mode (1 = two colours, 0 = 4 greys)
epd.Clear(0xFF, 1)         # wipe it to white (0xFF means white)

# The screen is 280 x 480 standing up. epd.height x epd.width gives us landscape: 480 x 280.
image = Image.new("1", (epd.height, epd.width), 255)
draw = ImageDraw.Draw(image)
draw.rectangle([10, 10, epd.height - 10, epd.width - 10], outline=0)
draw.text((40, 100), "Hello Peter!", font=ImageFont.load_default(size=56), fill=0)

epd.display_1Gray(epd.getbuffer(image))   # send the picture to the screen
epd.sleep()                               # put it back to sleep - protects the screen
print("Done - check the screen!")
