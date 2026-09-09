# Kiosk

The kiosk opens monitoring pages on an X11 desktop display.

## Setup

Copy [the URL example](../../configs/kiosk.urls.example) to a private file and replace the addresses. `scripts/kiosk.sh URL_FILE` opens Chromium in kiosk mode and rotates tabs every 15 seconds. `scripts/kiosk-manual.sh URL_FILE` opens the pages for manual navigation.

`KIOSK_BROWSER` selects the browser executable; `KIOSK_INTERVAL` changes the rotation interval. `KIOSK_PROFILE_DIR` selects the dedicated browser profile. Automatic rotation requires `xset` and `xdotool` and targets the browser's window. Launch it in a dedicated desktop session with Chromium closed so the process owns its window.

[Back to homelab](../../README.md)
