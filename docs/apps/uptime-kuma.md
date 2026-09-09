# Uptime Kuma

Service monitoring and the status web endpoint.

[Homelab index](../../README.md) · [Architecture](../architecture.md) · [Inspection record](../inventory.md)

## Observed setup

Port 3001 returned HTTP 302. NPM routes `status.example.com` to this host. Monitor definitions, notification destinations, and uptime history were not read.

Host: `rpimon`. Definition: `/opt/kuma/docker-compose.yml`.

Source file: `docker-compose/uptime-kuma/docker-compose.yml`.

| Service | Image/build recorded | Network / host ports | Restart |
| --- | --- | --- | --- |
| `uptime-kuma` | `louislam/uptime-kuma:latest` | Compose network; `3001:3001` | `always` |

| Service | Declared storage mapping |
| --- | --- |
| `uptime-kuma` | `./uptime-kuma-data:/app/data` |

Relative bind sources resolve beside the Compose file. Named volumes are Docker-managed. Paths outside `/opt` are declarations read from Compose; their contents and mount status were not inspected.

## Recreate the setup

1. Create `/opt/kuma/uptime-kuma-data` and mount it at `/app/data`.
2. Publish host port 3001 and configure the status hostname in NPM.
3. Add separate direct-LAN and proxied checks where they answer different questions. Use protocol-aware checks for DNS or VPN services.
4. Configure notification destinations privately and perform an owner-controlled test failure before relying on alerts.

These are owner-run setup instructions; no deployment command was executed during documentation. Pin compatible versions and supply private values before starting a new instance.

## Data and recovery

Preserve the complete application data directory consistently, including monitor and notification configuration. A sibling backup-named directory was listed; its existence does not verify recoverability.

## Verification and troubleshooting

If the status UI loads but alerts do not arrive, check monitor state and notification delivery separately. The NPM “Online” label does not represent Kuma’s monitored uptime.

## Deployment notes

The current browser route and host definition use `rpimon`. Access to the live Kuma data directory was denied and not elevated.
