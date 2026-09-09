# Kiosk display

The kiosk scripts rotate a display through monitoring pages or Glances terminal sessions.

## Browser display

`scripts/kiosk.sh` disables screen blanking and DPMS, hides the pointer with `unclutter`, and launches Chromium in kiosk mode.

An `xdotool` loop switches to the next tab and refreshes it every ten seconds. The configured pages include Glances, Home Assistant, and Pi-hole.

## Terminal display

`scripts/kiosk-manual.sh` opens Glances clients in GNOME Terminal tabs and switches between them every fifteen seconds.

Both scripts use an X11 desktop. Their endpoint lists and executable paths are machine-specific.

[Back to homelab](../../README.md)
