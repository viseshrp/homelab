# DIUN

DIUN runs locally on every Docker host and sends image-update notifications through ntfy. There is no central watcher or DIUN control plane. Each instance owns its providers, rules, schedule, notification identity, and persistent history.

DIUN is notification-only. It reads image metadata and registry manifests; it never pulls an image, stops a workload, recreates a container, or runs an upgrade command.

## Placement and behavior

| Host type | Runtime | Providers | Persistent state |
| --- | --- | --- | --- |
| `optiplex`, `rpiblog`, `rpihole`, `rpimon`, `rpinfs`, `rpiproxy`, `vpn-edge` | One `diun` container in `/opt/diun-agent` on each host | Local Docker provider plus that host's `custom-images.yml` file provider | `/opt/diun-agent/data/diun.db` |
| `rpihass` | Home Assistant OS app [`home-assistant-diun-agent`](../../home-assistant-diun-agent) | Local file provider only, containing Homebridge and PairDrop | App `/data/diun.db` |

Every instance checks on startup and at 00:00, 06:00, 12:00, and 18:00 local time, with up to 45 minutes of host-local jitter. First checks establish a silent baseline. Later matching changes produce ntfy notifications.

On the seven conventional hosts, the Docker provider:

- connects only to that host's local Docker socket;
- watches containers by default, including containers that are already stopped;
- reads the configured image reference while workloads continue running;
- compares registry digests and notifies on updates;
- automatically includes a newly added public container unless it has an explicit `diun.enable=false` label.

The file provider runs inside the same `diun` process. Its small host-specific rule file fills gaps the Docker provider cannot reliably infer, such as a fixed application tag, a local image's public base image, or the next major-version tag. It is not a separate service.

The HAOS app deliberately has no Docker provider. Its local file contains only Homebridge and PairDrop, so Home Assistant core, Supervisor, and the other apps cannot generate DIUN alerts.

## Host-specific file rules

The Docker provider dynamically covers each conventional host's public container images. The checked-in file rules supplement that inventory as follows:

| Host | Exact moving channels checked for digest updates | Bounded repository discovery checked for a new tag |
| --- | --- | --- |
| `optiplex` | DIUN `latest`; Dozzle `latest`; Bazarr, Sonarr, and Radarr `latest`; Seerr `latest`; Scrutiny `latest-collector` | None |
| `rpiblog` | DIUN `latest`; Dozzle `latest`; Planka `latest`; legacy Homarr `latest`; Nginx `latest`; Ubuntu `24.04` | PostgreSQL Alpine majors 15 and newer, seeded from `14-alpine` |
| `rpihole` | DIUN `latest`; Dozzle `latest` | None |
| `rpimon` | DIUN `latest`; Dozzle `latest`; ArchiveBox `dev`; pywb `latest`; Scrutiny `latest-web`; InfluxDB `2` | Uptime Kuma major 3 and newer; InfluxDB major 3 and newer `-core` tags |
| `rpinfs` | DIUN `latest`; Dozzle `latest` | None |
| `rpiproxy` | DIUN `latest`; Dozzle `latest`; Cloudflared `latest` | None |
| `vpn-edge` | DIUN `latest`; Dozzle `latest` | WG-Easy majors 16 and newer; PostgreSQL majors 16 and newer |
| `rpihass` | Homebridge `latest`; PairDrop `latest` | None |

Rules live under [`docker-compose/diun-agent/rules`](../../docker-compose/diun-agent/rules). `deployments.json` maps exactly one of those sources to `custom-images.yml` for each conventional target. The HAOS file is [`home-assistant-diun-agent/custom-images.yml`](../../home-assistant-diun-agent/custom-images.yml).

An exact channel rule, such as `planka:latest`, reports when the digest behind that tag changes. A bounded `watch_repo` rule reports when a new matching tag appears. The regular expressions are anchored so DIUN does not enumerate unrelated tags.

This tailored policy is intentional:

- a container already using `latest` or another moving channel is handled by the Docker provider;
- a fixed tag such as `planka:2.2.1` needs an explicit `planka:latest` rule to reveal a later release;
- a major-version jump needs a bounded `watch_repo` rule because neither `postgres:14-alpine` nor `postgres:15` will move to the next major;
- a locally built image needs a rule for its public base image because the local image itself has no public registry manifest;
- a digest-only reference is ambiguous because DIUN treats it as `latest`, so the intended non-`latest` channel is stated explicitly where needed.

Because monitoring is deliberately distributed, the same shared component can send one notification from each host that runs it. DIUN and Dozzle are examples. There is no cross-host deduplication service.

## Configuration and security

The Compose service uses DIUN 4.33.0 pinned to a reviewed multi-architecture index digest. It runs `diun serve`, mounts `/data`, exposes no port, uses a read-only root filesystem, drops all capabilities, enables `no-new-privileges`, and uses the native `diun healthcheck` command.

The Docker socket bind is marked read-only, but Docker API access remains a host-level trust boundary. Keep the pinned DIUN image and do not expose a remote Docker API. The HAOS app avoids that boundary entirely because it uses only the file provider.

Every host has a separate non-admin ntfy identity named `diun-<host>`. Its token can publish to the private monitoring topic but cannot read it. Compose deployments mount a mode-0600 token file. The HAOS app writes its private option to container-local tmpfs. Never commit or print the endpoint, topic, token, rendered Compose configuration, or database.

## Deployment and verification

Follow [Deploy and verify DIUN](../operations.md#deploy-and-verify-diun). In summary:

1. Reconcile each host's Docker inventory and local-build bases with its rule file.
2. Create a verified DIUN-only backup before replacing files or state.
3. Build one isolated payload per target with `scripts/prepare.py diun-agent DESTINATION --host HOST`.
4. Install only `docker-compose.yml` and that host's `custom-images.yml`; preserve its private `.env`, token, and database.
5. Validate the real Compose model without displaying private substitutions, then recreate only `diun`.
6. Require both `docker` and `file` providers, the six-hour schedule, a completed scan, and zero failed checks. Reconcile any skipped count with intentionally filter-excluded repository seed tags or known local-only images.
7. Restart only DIUN once more and require a clean unchanged scan, proving the database survived.
8. Confirm every application container ID and start time is unchanged. Reconcile Dozzle with `docker ps -a` and the DIUN provider output.
9. On HAOS, require only the file provider and exactly the two selected images. Preserve the operator's Protection mode, Watchdog, Automatic updates, and other app choices; only Start on boot and running state are changed by the approved rollout.

The notification path can be tested with:

```sh
cd /opt/diun-agent
sudo docker compose exec -T diun diun notif test
```

Confirm the mobile message identifies the correct host. Independently prove that the same publisher token is denied read access. Do not leave the HAOS `notification_test_on_start` option enabled after its one-time test.

## Verified rollout on September 13, 2026

The distributed rollout completed on all eight hosts. Each conventional host passed its real Compose render, native healthcheck, persistent-database restart check, notification test, write-only token check, and byte-for-byte comparison of the deployed Compose and rule files with its isolated repository payload. The latest completed scans were:

| Host | Docker-provider inputs | File-provider rules | Latest completed result |
| --- | ---: | ---: | --- |
| `optiplex` | 11 | 7 | 18 unchanged, 0 skipped, 0 failed |
| `rpiblog` | 8 | 7 | 18 unchanged, 1 intentionally filtered seed, 0 failed |
| `rpihole` | 3 | 2 | 5 unchanged, 0 skipped, 0 failed |
| `rpimon` | 8 | 8 | 15 unchanged, 2 intentionally filtered seeds, 0 failed |
| `rpinfs` | 2 | 2 | 4 unchanged, 0 skipped, 0 failed |
| `rpiproxy` | 5 | 3 | 8 unchanged, 0 skipped, 0 failed |
| `vpn-edge` | 5 | 4 | 10 unchanged, 2 intentionally filtered seeds, 0 failed |
| `rpihass` | Not enabled | 2 | 2 unchanged, 0 skipped, 0 failed |

The conventional Docker-provider counts reconcile with the unique registry-backed image references visible in the live container inventory. Two containers on `optiplex` intentionally share the same File Browser image reference. The three unique local-build references on `rpiblog` are not registry images; the host-specific file rules cover the selected upstream channels and version boundaries that must be monitored independently. No conventional container had a `diun.enable=false` label.

Dozzle reported all eight hosts and 64 containers, including exited containers. One DIUN log stream was opened for every host. The seven conventional instances were healthy, the HAOS app was running, and every stream showed a completed scan with the six-hour schedule and zero failures.

All eight native ntfy tests succeeded. Each host's DIUN publisher token was independently denied subscriber access with HTTP 403. On HAOS, the one-time test option was returned to `false` before the final DIUN-only restart.

The conventional rollback archives are under `/opt/backups/diun-local-20260913T035739Z` on their respective hosts and passed archive listing and SHA-256 verification. HAOS backup `279e9904` is a completed full backup named `pre-diun-local-20260913T0022EDT`; the narrower package archive is `/share/diun-agent-backups/diun-agent-pre-4.33.0-5-20260913T0025EDT.tar.gz` with SHA-256 `2ddbaea62ec5cb5f9b02328d6216e188a216964f35dc20e696aa7a743943c42d`.

The obsolete central `diun-release-watch` container, release catalog, data directory, and its two private profile settings were removed from `rpimon` only after backup and local-provider verification. No application workload was stopped or recreated. Homebridge and PairDrop remained running. No rollback was performed.

## Alignment with upstream documentation

| Official DIUN behavior | This deployment |
| --- | --- |
| [Docker installation](https://crazymax.dev/diun/install/docker/) uses `serve`, `/data`, the Docker socket, and `diun healthcheck` | Every conventional host uses those elements in one local Compose service. |
| [Docker provider](https://crazymax.dev/diun/providers/docker/) supports `watchByDefault`, `watchStopped`, and labels | Both running and already-stopped containers are included by default without stopping workloads. Labels remain the narrow opt-out. |
| [File provider](https://crazymax.dev/diun/providers/file/) accepts explicit images, `watch_repo`, tag filters, and notification states | Each host mounts one local, bounded rule file; HAOS mounts only its two selected channels. |
| [Docker and file providers](https://crazymax.dev/diun/user-guides/docker-file-providers/) can run together in one DIUN process | Each conventional host uses exactly that combined-provider model. |
| [Watch configuration](https://crazymax.dev/diun/config/watch/) defines cron schedule, jitter, startup checks, first-check notifications, and digest comparison | Checks run every six hours with jitter, run on startup, compare digests, and suppress first-check notifications. |
| [FAQ guidance](https://crazymax.dev/diun/faq/) warns that `watch_repo` fetches all tags and that digest-only references are analyzed as `latest` | Fixed/local-build gaps have exact rules; new majors use narrowly filtered repository rules; intended non-`latest` channels are explicit. |
| [ntfy notifier](https://crazymax.dev/diun/notif/ntfy/) supports `tokenFile`, endpoint, topic, priority, tags, timeout, and title templates | Each instance uses a unique write-only token, priority 3, `package` tag, ten-second timeout, and hostname-prefixed title. |

The deliberate policy differences from the examples are update-only notifications, an immutable DIUN image digest, host-specific file rules, and additional container hardening. All settings themselves are documented DIUN features.

## Backup and recovery

For a consistent Compose-agent backup, stop only that host's `diun` container and archive `/opt/diun-agent/data`, `.env`, `ntfy-token`, `docker-compose.yml`, and `custom-images.yml`. Start DIUN immediately afterward and verify its scan. The HAOS app belongs in a Home Assistant full backup.

The database contains replaceable manifest history. Losing it creates a new silent baseline because first-check notifications are disabled; it does not affect workloads. Restore nothing without operator approval.

To remove DIUN, stop and remove only the local DIUN project or HAOS app. Do not prune Docker images, delete application data, or alter other containers. Remove the corresponding ntfy identity only through a separate reviewed change.
