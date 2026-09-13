#!/bin/sh
set -eu

options_file=/data/options.json
token_file=/tmp/diun-ntfy-token

read_required() {
    jq -er ".${1} | select(. != null and . != \"\")" "$options_file"
}

read_bool() {
    jq -r --arg key "$1" \
        '.[$key] | if type == "boolean" then tostring else error("invalid boolean option") end' \
        "$options_file"
}

ntfy_endpoint=$(read_required ntfy_endpoint)
ntfy_topic=$(read_required ntfy_topic)
ntfy_token=$(read_required ntfy_token)
diun_hostname=$(read_required hostname)
timezone=$(read_required timezone)
schedule=$(read_required schedule)
jitter=$(read_required jitter)
notification_test_on_start=$(read_bool notification_test_on_start)
log_level=$(read_required log_level)

umask 077
printf '%s' "$ntfy_token" > "$token_file"
unset ntfy_token

export TZ="$timezone"
export LOG_LEVEL="$log_level"
export LOG_JSON=false
export DIUN_DB_PATH=/data/diun.db
export DIUN_WATCH_WORKERS=10
export DIUN_WATCH_SCHEDULE="$schedule"
export DIUN_WATCH_JITTER="$jitter"
export DIUN_WATCH_FIRSTCHECKNOTIF=false
export DIUN_WATCH_RUNONSTARTUP=true
export DIUN_WATCH_COMPAREDIGEST=true
export DIUN_DEFAULTS_NOTIFYON=update
export DIUN_PROVIDERS_FILE_FILENAME=/etc/diun/custom-images.yml
export DIUN_NOTIF_NTFY_ENDPOINT="$ntfy_endpoint"
export DIUN_NOTIF_NTFY_TOKENFILE="$token_file"
export DIUN_NOTIF_NTFY_TOPIC="$ntfy_topic"
export DIUN_NOTIF_NTFY_PRIORITY=3
export DIUN_NOTIF_NTFY_TAGS=package
export DIUN_NOTIF_NTFY_TIMEOUT=10s
export DIUN_NOTIF_NTFY_TEMPLATETITLE="[$diun_hostname] {{ .Entry.Image }} {{ if eq .Entry.Status \"new\" }}is available{{ else }}has been updated{{ end }}"

if [ "$notification_test_on_start" = true ]; then
    /usr/local/bin/diun serve &
    diun_pid=$!

    stop_test_process() {
        kill -TERM "$diun_pid" 2>/dev/null || true
        wait "$diun_pid" 2>/dev/null || true
    }

    trap 'stop_test_process; exit 0' INT TERM
    trap stop_test_process EXIT

    healthy=false
    attempt=0
    while [ "$attempt" -lt 60 ]; do
        if /usr/local/bin/diun healthcheck >/dev/null 2>&1; then
            healthy=true
            break
        fi
        if ! kill -0 "$diun_pid" 2>/dev/null; then
            wait "$diun_pid"
        fi
        attempt=$((attempt + 1))
        sleep 1
    done

    if [ "$healthy" != true ]; then
        echo "DIUN did not become healthy before the notification test" >&2
        exit 1
    fi

    /usr/local/bin/diun notif test
    kill -TERM "$diun_pid"
    wait "$diun_pid" 2>/dev/null || true
    trap - EXIT
fi

exec /usr/local/bin/diun serve
