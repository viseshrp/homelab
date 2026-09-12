#!/bin/bash
set -u

state_dir=/run/scrutiny
mkdir -p "$state_dir"
started=$(date +%s)

if /opt/scrutiny/bin/scrutiny-collector-metrics run; then
    collector_status=0
    push_status=up
    push_message=SMART%20collection%20succeeded
    touch "$state_dir/last-success"
else
    collector_status=$?
    push_status=down
    push_message=SMART%20collection%20failed
fi

elapsed_ms=$(( ($(date +%s) - started) * 1000 ))
push_path="/api/push/${KUMA_PUSH_TOKEN}?status=${push_status}&msg=${push_message}&ping=${elapsed_ms}"

if exec 3<>"/dev/tcp/${KUMA_PUSH_HOST}/${KUMA_PUSH_PORT}"; then
    printf 'GET %s HTTP/1.1\r\nHost: %s:%s\r\nConnection: close\r\n\r\n' \
        "$push_path" "$KUMA_PUSH_HOST" "$KUMA_PUSH_PORT" >&3
    IFS= read -r response <&3 || true
    exec 3<&-
    exec 3>&-
    case "$response" in
        *" 200 "*) printf 'kuma_push=ok\n' ;;
        *) printf 'kuma_push=failed\n' >&2 ;;
    esac
else
    printf 'kuma_push=unreachable\n' >&2
fi

exit "$collector_status"
