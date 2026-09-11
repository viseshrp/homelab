# Uptime Kuma

Uptime Kuma checks service availability and provides a web interface for monitors, uptime history, and notifications.

## My setup

Kuma runs on `rpimon` from `/opt/kuma`. The `louislam/uptime-kuma` container publishes port 3001.

Nginx Proxy Manager forwards the `status` HTTPS hostname to `rpimon:3001`. Homarr includes a shortcut to it.

## Data

`/opt/kuma/uptime-kuma-data` is mounted at `/app/data`. This directory holds application state, including monitor and notification settings.

The container restarts automatically. Notification destinations remain private.

[`configs/uptime-kuma/monitors.json`](../../configs/uptime-kuma/monitors.json) is the declarative source for the live monitor set and public status-page grouping. [`reconcile.py`](../../configs/uptime-kuma/reconcile.py) resolves the real public domain and host targets from the installed private `.env`, then audits or applies the policy through Kuma's authenticated local socket interface.

The installed Uptime Kuma 1.23.17 native JSON export is unsuitable for source control: it includes private notification configuration and does not include status-page groups. Do not commit a native export. The reconciler preserves the existing private default notification and commits only sanitized logical targets.

All intended monitors are active. Public HTTP monitors cover the external route, while LAN port and ping monitors cover services and hosts that are not publicly routed. The inverted `Pi-hole Blocking` DNS monitor stays up only while Pi-hole rejects the documented telemetry hostname. Services without a running endpoint are omitted instead of remaining as disabled monitors.

On September 11, 2026, the live database matched the sanitized reference: 28 active monitors in four status-page groups, each with a fresh successful result and the existing private default notification. The container stayed healthy with no restart or image change during the cleanup. This is a dated runtime observation, not a guarantee of future availability.

## Verify and recover

From `/opt/kuma`, audit without changing Kuma:

```sh
sudo python3 reconcile.py
```

The audit lists additions, updates, and extra monitors without printing private target values. To apply the exact declared set after reviewing the output:

```sh
sudo python3 reconcile.py --apply --prune
```

`--apply` creates and validates a SQLite backup before the first write. `--prune` is required when undeclared monitors exist; omitting it refuses the change. The command verifies a second audit is idempotent after applying.

Check `rpimon:3001` and the `status` route, then confirm every monitor records a fresh result. Test a notification path separately when changing notification configuration.

Back up `uptime-kuma-data/` consistently because it contains the SQLite database, monitors, history, and notification settings. After a restore, verify timestamps and live monitor execution rather than relying on historical green rows.

[Compose](../../docker-compose/uptime-kuma/docker-compose.yml) · [Operations](../operations.md) · [Application index](README.md)
