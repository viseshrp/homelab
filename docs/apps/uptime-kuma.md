# Uptime Kuma

Uptime Kuma checks service availability and provides a web interface for monitors, uptime history, and notifications.

## My setup

Kuma runs on `rpimon` from `/opt/kuma`. The repository and installed environment use `louislam/uptime-kuma:latest`, and the container publishes port 3001. Uptime Kuma's [Docker tag documentation](https://github.com/louislam/uptime-kuma/wiki/Docker-Tags) marks this tag deprecated and keeps it on v1; upgrading to v2 requires the separate `:2` tag and the [official migration procedure](https://github.com/louislam/uptime-kuma/wiki/Migration-From-v1-To-v2).

Nginx Proxy Manager forwards the `status` HTTPS hostname to `rpimon:3001`. Homarr includes a shortcut to it.

## Data

`/opt/kuma/uptime-kuma-data` is mounted at `/app/data`. This directory holds application state, including monitor and notification settings.

The container restarts automatically. Notification destinations remain private.

[`configs/uptime-kuma/monitors.json`](../../configs/uptime-kuma/monitors.json) is the declarative source for the live monitor set and public status-page grouping. [`reconcile.py`](../../configs/uptime-kuma/reconcile.py) resolves the real public domain and host targets from the installed private `.env`, then audits or applies the policy through Kuma's authenticated local socket interface.

[`notification.json`](../../configs/uptime-kuma/notification.json) and [`reconcile-notification.py`](../../configs/uptime-kuma/reconcile-notification.py) declare the provider shape without its private server, topic, or token. The installed default is the built-in ntfy provider with token authentication. It is applied to every monitor; the earlier Gmail/Apprise destination is removed after a successful test delivery.

The installed Uptime Kuma 1.23.17 native JSON export is unsuitable for source control: it includes private notification configuration and does not include status-page groups. Do not commit a native export. The monitor and notification reconcilers commit only sanitized policy and resolve private inputs at runtime.

All intended monitors are active. Public HTTP monitors cover the external route, while LAN port and ping monitors cover services and hosts that are not publicly routed. The inverted `Pi-hole Blocking` DNS monitor stays up only while Pi-hole rejects the documented telemetry hostname. Services without a running endpoint are omitted instead of remaining as disabled monitors.

On September 12, 2026, `latest` resolved to the same Uptime Kuma 1.23.17 image that was already running. The live database matched the sanitized reference: 29 active monitors in four status-page groups, each with a fresh successful result and the private ntfy default notification. The old Gmail/Apprise notification was absent. Changing the reference therefore caused no application or database migration. Future pulls of `latest` may change the v1 image. This is a dated runtime observation, not a guarantee of future availability.

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

Audit the default notification and monitor assignments without sending a message:

```sh
sudo python3 reconcile-notification.py --prune
```

After reviewing the audit, configure ntfy, send a test message, apply it to every monitor, and remove other notification providers:

```sh
sudo python3 reconcile-notification.py --apply --prune
```

The cutover creates a separate consistent SQLite backup before changing Kuma. It tests ntfy before making it the default, reconciles all monitor links, removes the previous provider only after the new path succeeds, and finishes with an exact audit.

Check `rpimon:3001` and the `status` route, then confirm every monitor records a fresh result. Test the ntfy route and read the test message with the mobile subscriber credentials.

Back up `uptime-kuma-data/` consistently because it contains the SQLite database, monitors, history, and notification settings. Record the resolved image digest before pulling the moving tag. After a restore, run the recorded pre-update image and verify timestamps and live monitor execution rather than relying on historical green rows.

[Compose](../../docker-compose/uptime-kuma/docker-compose.yml) · [Operations](../operations.md) · [Application index](README.md)
