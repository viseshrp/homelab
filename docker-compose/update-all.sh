#!/usr/bin/env bash
# No implicit host-wide project discovery, OS updates, or storage pruning.
set -euo pipefail
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
apply=false
if [[ ${1:-} == --apply ]]; then apply=true; shift; fi
if [[ $# == 0 ]]; then
  printf 'Usage: %s [--apply] PROJECT_DIRECTORY [...]\n' "$0" >&2; exit 2
fi
# Reject missing paths before applying any project.
for directory in "$@"; do
  if [[ ! -f $directory/docker-compose.yml && ! -f $directory/compose.yaml ]]; then
    printf 'No Compose file in %s\n' "$directory" >&2; exit 2
  fi
done
for directory in "$@"; do
  if "$apply"; then
    bash "$script_dir/update.sh" --apply "$directory"
  else
    bash "$script_dir/update.sh" "$directory"
  fi
done
