#!/usr/bin/env bash
# Preview by default. Operates only on the explicitly named local project directory.
set -euo pipefail
apply=false
if [[ ${1:-} == --apply ]]; then apply=true; shift; fi
if [[ $# != 1 || ! -d $1 ]]; then
  printf 'Usage: %s [--apply] PROJECT_DIRECTORY\n' "$0" >&2
  exit 2
fi
cd -- "$1"
if [[ ! -f docker-compose.yml && ! -f compose.yaml ]]; then
  printf 'No Compose file in %s\n' "$PWD" >&2; exit 2
fi
run() {
  printf '%q ' "$@"; printf '\n'
  if "$apply"; then "$@"; fi
}
# Validation happens before pull/build/up. Never source .env as shell code.
run docker compose config --quiet
run docker compose pull --ignore-buildable
run docker compose build
run docker compose up -d
