#!/usr/bin/env bash
# Run in an X11 desktop session. URLs are newline-separated; # starts a comment.
set -euo pipefail
if [[ $# != 1 ]]; then printf 'Usage: %s URL_FILE\n' "$0" >&2; exit 2; fi
browser=${KIOSK_BROWSER:-chromium}
interval=${KIOSK_INTERVAL:-15}
[[ $interval =~ ^[1-9][0-9]*$ ]] || { printf 'KIOSK_INTERVAL must be a positive integer\n' >&2; exit 2; }
urls=()
while IFS= read -r url || [[ -n $url ]]; do
  [[ -z $url || $url == \#* ]] && continue
  [[ $url == http://* || $url == https://* ]] || { printf 'Only HTTP(S) URLs are accepted\n' >&2; exit 2; }
  urls+=("$url")
done < "$1"
[[ ${#urls[@]} -gt 0 ]] || { printf 'URL file is empty\n' >&2; exit 2; }
for command in "$browser" xset xdotool; do command -v "$command" >/dev/null; done
xset s off
xset s noblank
xset -dpms
profile=${KIOSK_PROFILE_DIR:-${XDG_STATE_HOME:-$HOME/.local/state}/homelab-kiosk}
"$browser" --user-data-dir="$profile" --new-window --kiosk "${urls[@]}" &
browser_pid=$!
trap 'kill "$browser_pid" 2>/dev/null || true' EXIT
# Target this process's window so rotation cannot send keys to another application.
window=$(xdotool search --sync --onlyvisible --pid "$browser_pid" | head -n 1)
while kill -0 "$browser_pid" 2>/dev/null; do
  sleep "$interval"
  xdotool key --window "$window" ctrl+Tab
done
