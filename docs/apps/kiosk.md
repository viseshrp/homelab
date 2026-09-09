# Kiosk display scripts

Rotates a physical display through monitoring pages or terminal tabs.

[Homelab index](../../README.md) · [Architecture](../architecture.md) · [Inspection record](../inventory.md)

## Observed setup

Two repository shell scripts were read. Their configured endpoints are historical; neither script was run and no display host was identified.


## Recreate the setup

1. Use an X11 desktop with the required tools: `xset`, `unclutter`, `xdotool`, and the browser or terminal selected by the script.
2. `scripts/kiosk.sh` disables blanking/DPMS, hides the cursor, launches Chromium kiosk pages, and switches and refreshes tabs every 10 seconds.
3. `scripts/kiosk-manual.sh` instead opens Glances client commands in GNOME Terminal tabs and switches tabs every 15 seconds.
4. Replace all historical endpoint addresses and machine-specific executable paths with a private inventory before installing a startup entry.

These are owner-run setup instructions; no deployment command was executed during documentation. Pin compatible versions and supply private values before starting a new instance.

## Data and recovery

Keep a sanitized script template and private endpoint list. Browser profiles can contain sessions and should not be committed.

## Verification and troubleshooting

Keyboard automation depends on focus. A missing X11 tool, browser executable, Glances environment, or display session can prevent rotation even if the monitored services work.

## Deployment notes

The repository’s scripts contain commented browser-profile edits and old addresses. They were inspected as source only; no kiosk process or autostart configuration was verified.
