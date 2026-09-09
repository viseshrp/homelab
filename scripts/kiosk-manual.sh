#!/usr/bin/env bash
# Open the same page set without automatic tab rotation.
set -euo pipefail
if [[ $# != 1 ]]; then printf 'Usage: %s URL_FILE\n' "$0" >&2; exit 2; fi
urls=()
while IFS= read -r url || [[ -n $url ]]; do
  [[ -z $url || $url == \#* ]] && continue
  [[ $url == http://* || $url == https://* ]] || { printf 'Only HTTP(S) URLs are accepted\n' >&2; exit 2; }
  urls+=("$url")
done < "$1"
[[ ${#urls[@]} -gt 0 ]] || { printf 'URL file is empty\n' >&2; exit 2; }
exec "${KIOSK_BROWSER:-chromium}" --new-window "${urls[@]}"
