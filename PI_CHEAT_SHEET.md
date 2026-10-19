# Now Playing Pi – Daily Cheat Sheet

## Turn it ON
Plug in the power. That's it.
Wait ~1–2 minutes – the display starts by itself and shows what's playing.

## Turn it OFF (on your Mac, in Terminal)
One line – shuts the Pi down safely:
```
ssh -t p2nash@peterpi.local sudo shutdown now
```
Type your Pi password (twice if asked). Wait until the green light stops flickering (~10 secs), then unplug.
Never just pull the plug while it's running – it can damage the memory card.

## Restart it (if it seems stuck)
```
ssh -t p2nash@peterpi.local sudo reboot
```

## Restart just the display (Pi stays on)
```
ssh -t p2nash@peterpi.local sudo systemctl restart nowplaying
```

## Check what it's doing
```
ssh p2nash@peterpi.local
journalctl -u nowplaying -f
```
Ctrl + C to stop watching, `exit` to leave the Pi.

## After changing code on the Mac
1. Test on Mac:  `cd ~/Claude/Projects/"Learn to code"/spotify-now-playing` → `source venv/bin/activate` → `python3 display_preview.py` (Ctrl + C to stop)
2. Copy to Pi:
```
rsync -av --exclude venv --exclude __pycache__ --exclude preview.png --exclude .cache ~/Claude/Projects/"Learn to code"/spotify-now-playing/ p2nash@peterpi.local:~/spotify-now-playing/
```
3. Restart the display (command above).

## Where am I?
- `pear@Peters-MacBook-Pro` = your Mac
- `p2nash@peterpi` = the Pi
