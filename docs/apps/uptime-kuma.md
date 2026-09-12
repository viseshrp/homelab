# Uptime Kuma

Uptime Kuma checks service availability and provides a web interface for monitors, uptime history, and notifications.

## My setup

Kuma runs on `rpimon` from `/opt/kuma`. The repository and installed environment use the recommended moving v2 tag, `louislam/uptime-kuma:2`, and the container publishes port 3001. Uptime Kuma's deprecated `latest` tag remains on v1. A v1 installation must follow the [official v2 migration procedure](https://github.com/louislam/uptime-kuma/wiki/Migration-From-v1-To-v2) before adopting `:2`.

Nginx Proxy Manager forwards the `status` HTTPS hostname to `rpimon:3001`. Homarr includes a shortcut to it.

## Data

`/opt/kuma/uptime-kuma-data` is mounted at `/app/data`. This directory holds application state, including monitor and notification settings.

The container restarts automatically. Notification destinations remain private.

[`configs/uptime-kuma/monitors.json`](../../configs/uptime-kuma/monitors.json) is the declarative source for the live monitor set and public status-page grouping. [`reconcile.py`](../../configs/uptime-kuma/reconcile.py) resolves the real public domain and host targets from the installed private `.env`, then audits or applies the policy through Kuma's authenticated local socket interface.

[`notification.json`](../../configs/uptime-kuma/notification.json) and [`reconcile-notification.py`](../../configs/uptime-kuma/reconcile-notification.py) declare the provider shape without its private server, topic, or token. The installed default is the built-in ntfy provider with token authentication. It is applied to every monitor; the earlier Gmail/Apprise destination is removed after a successful test delivery.

The former Uptime Kuma 1.23.17 native JSON export was unsuitable for source control: it included private notification configuration and omitted status-page groups. Uptime Kuma v2 removes that deprecated backup/restore feature. The monitor and notification reconcilers commit only sanitized policy and resolve private inputs at runtime.

All intended monitors are active. Public HTTP monitors cover the external route, while LAN port and ping monitors cover services and hosts that are not publicly routed. The inverted `Pi-hole Blocking` DNS monitor stays up only while Pi-hole rejects the documented telemetry hostname. Services without a running endpoint are omitted instead of remaining as disabled monitors.

The `:2` tag moves within the stable v2 release line. Record its platform-specific digest and application version before every pull. Major-version rollback requires restoring the entire quiesced pre-migration data directory before starting the recorded v1 image; never start v1 against a database migrated by v2.

On September 11, 2026, `:2` resolved to Uptime Kuma 2.5.4 on ARM64. Before the v1-to-v2 cutover, the complete stopped v1 data directory and project inputs were copied to `/opt/kuma/backups/pre-v2-migration-20260912T022729Z` and verified with SQLite and SHA-256 checks. At the operator's direction, the working copy's heartbeat rows were removed before v2's first start; monitor, group, status-page, user, and notification records were retained. The v2 migration then reported no history to aggregate. All 29 monitors produced fresh successful results, both reconciliation audits were idempotent, and the direct endpoint, public status page, public Socket.IO handshake, and Kuma-to-ntfy delivery/readback passed. The full pre-migration backup remains the recovery source for the discarded history.

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
