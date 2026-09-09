# Uptime Kuma

Uptime Kuma checks service availability and provides a web interface for monitors, uptime history, and notifications.

## My setup

Kuma runs on `rpimon` from `/opt/kuma`. The `louislam/uptime-kuma` container publishes port 3001.

Nginx Proxy Manager forwards the `status` HTTPS hostname to `rpimon:3001`. Homarr includes a shortcut to it.

## Data

`/opt/kuma/uptime-kuma-data` is mounted at `/app/data`. This directory holds application state, including monitor and notification settings.

The container restarts automatically. Notification destinations remain private.

[Back to homelab](../../README.md)
