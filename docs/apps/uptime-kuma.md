# Uptime Kuma

Uptime Kuma checks service availability and provides a web interface for monitors, uptime history, and notifications.

## My setup

Kuma runs on `rpimon` from `/opt/kuma`. The `louislam/uptime-kuma` container publishes port 3001.

Nginx Proxy Manager forwards the `status` HTTPS hostname to `rpimon:3001`. Homarr includes a shortcut to it.

## Data

`/opt/kuma/uptime-kuma-data` is mounted at `/app/data`. This directory holds application state, including monitor and notification settings.

The container restarts automatically. Notification destinations remain private.

## Verify and recover

Check `rpimon:3001` and the `status` route, then confirm at least one monitor executes and records a fresh result. Test a notification path separately when changing notification configuration.

Back up `uptime-kuma-data/` consistently because it contains the SQLite database, monitors, history, and notification settings. After a restore, verify timestamps and live monitor execution rather than relying on historical green rows.

[Compose](../../docker-compose/uptime-kuma/docker-compose.yml) · [Operations](../operations.md) · [Application index](README.md)
