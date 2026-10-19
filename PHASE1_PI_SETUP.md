# Phase 1 – Set up the Raspberry Pi (no screen, keyboard or mouse needed)

You need: the Pi 3B, the microSD card, the official power supply, and your Mac (plus a card reader if your Mac has no SD slot).

**SSH** = typing commands on your Mac that run on the Pi, over Wi-Fi. "Headless" = running the Pi with no screen attached.

## Step 1 – Prepare the memory card (on your Mac)
1. Download **Raspberry Pi Imager** from raspberrypi.com/software and install it.
2. Put the microSD card in your Mac.
3. In Imager choose:
   - Device: **Raspberry Pi 3**
   - OS: **Raspberry Pi OS (other) → Raspberry Pi OS Lite (64-bit)**
   - Storage: your microSD card (check the size matches!)
4. Say **yes** to customising settings:
   - Hostname: `peterpi`
   - Username + password: `p2nash` + something memorable (**write both down**)
   - Wi-Fi name + password, Wi-Fi country **GB**
   - Time zone Europe/London, keyboard gb
   - **SSH: ON** (password login)
   - ⚠️ The Pi 3 only uses **2.4 GHz** Wi-Fi. If your router has a separate "-5G" network, pick the other one.
5. Click **Write** (5–10 mins), then eject the card.

## Step 2 – Start the Pi and connect
1. Card into the Pi (slot underneath, contacts facing the board).
2. Plug in power. Red light = power, flickering green = working.
3. Wait **3 minutes** (first start is slow).
4. On your Mac open Terminal (Cmd + Space → "Terminal") and type:
   ```
   ssh p2nash@peterpi.local
   ```
5. First time only: type `yes` to trust the Pi.
6. Type your Pi password – **nothing shows as you type**, that's normal – and press Enter.
7. You're in when the line reads `p2nash@peterpi:~ $`. (Type `exit` to leave.)

**"Connection refused"?** The Pi is on Wi-Fi but SSH is off. Unplug the Pi, put the card in your Mac, run `touch /Volumes/bootfs/ssh`, eject (`diskutil eject /Volumes/bootfs`), put it back in the Pi and power on. Wait 2 minutes and try again.

**"Could not resolve hostname"?** Wait 2 more minutes and retry. Still failing → check Wi-Fi details / 2.4 GHz and redo Step 1.

## Step 3 – Update the software (10–20 mins)
```
sudo apt update && sudo apt full-upgrade -y
```
`sudo` = as administrator · `apt` = the Pi's app store · `update` = check · `full-upgrade` = install · `-y` = auto-yes.
Finished when you're back at `p2nash@peterpi:~ $`.

## Step 4 – Switch on the screen connection (SPI)
1. `sudo raspi-config`  (arrow keys to move, Enter to select, Tab to reach Finish – no mouse)
2. **Interface Options → SPI → Yes**
3. Tab to **Finish**, reboot if asked, wait a minute, reconnect: `ssh p2nash@peterpi.local`
4. Check: `ls /dev/spi*` → should show `/dev/spidev0.0  /dev/spidev0.1`

## Step 5 – Always shut down properly
```
sudo shutdown now
```
Wait for the green light to stop (~10 secs), then unplug. Pulling the plug while running can damage the card.

## Checklist
- [ ] Card set up with Pi OS Lite, Wi-Fi + SSH configured
- [ ] Pi starts and joins Wi-Fi
- [ ] `ssh` connects from Terminal
- [ ] Software updated
- [ ] SPI on and checked
- [ ] Know how to shut down safely
