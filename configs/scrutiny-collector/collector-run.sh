#!/bin/bash
set -uo pipefail

state_dir=/run/scrutiny
mkdir -p "$state_dir"
started=$(date +%s)

case "${SCRUTINY_EXPECTED_DEVICE_COUNT:-3}" in
    ''|*[!0-9]*)
        printf 'invalid SCRUTINY_EXPECTED_DEVICE_COUNT\n' >&2
        exit 2
        ;;
esac
case "${SCRUTINY_SMART_RETRIES:-3}" in
    ''|*[!0-9]*)
        printf 'invalid SCRUTINY_SMART_RETRIES\n' >&2
        exit 2
        ;;
esac
case "${SCRUTINY_SMART_RETRY_DELAY_SECONDS:-5}" in
    ''|*[!0-9]*)
        printf 'invalid SCRUTINY_SMART_RETRY_DELAY_SECONDS\n' >&2
        exit 2
        ;;
esac

expected_count=${SCRUTINY_EXPECTED_DEVICE_COUNT:-3}
retry_count=${SCRUTINY_SMART_RETRIES:-3}
retry_delay=${SCRUTINY_SMART_RETRY_DELAY_SECONDS:-5}
device_specs=${SCRUTINY_DEVICE_SPECS:-/dev/sda:sat,/dev/sdb:sat,/dev/nvme0:nvme}

# Some USB bridges return smartctl exit 2 on the first command after standby.
# Warm each declared device with bounded retries before the real collection.
IFS=',' read -r -a specs <<< "$device_specs"
for spec in "${specs[@]}"; do
    device=${spec%:*}
    device_type=${spec##*:}
    ready=0
    for ((attempt = 1; attempt <= retry_count; attempt++)); do
        if smartctl --info --json --device "$device_type" "$device" >/dev/null 2>&1; then
            ready=1
            break
        fi
        printf 'smart_preflight=retry device=%s attempt=%s/%s\n' \
            "$device" "$attempt" "$retry_count" >&2
        if [ "$attempt" -lt "$retry_count" ]; then
            sleep "$retry_delay"
        fi
    done
    if [ "$ready" -ne 1 ]; then
        printf 'smart_preflight=failed device=%s\n' "$device" >&2
    fi
done

collector_log="$state_dir/collector-last.log"
/opt/scrutiny/bin/scrutiny-collector-metrics run 2>&1 | tee "$collector_log"
collector_command_status=${PIPESTATUS[0]}
published_count=$(grep -c 'Publishing smartctl results for' "$collector_log" || true)

if [ "$collector_command_status" -eq 0 ] && [ "$published_count" -eq "$expected_count" ]; then
    collector_status=0
    push_status=up
    push_message=SMART%20collection%20succeeded
    touch "$state_dir/last-success"
else
    collector_status=1
    push_status=down
    push_message="SMART%20collection%20incomplete%20${published_count}%20of%20${expected_count}"
    printf 'collector_validation=failed command_status=%s published=%s expected=%s\n' \
        "$collector_command_status" "$published_count" "$expected_count" >&2
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
