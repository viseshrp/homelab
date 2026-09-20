# Scrutiny

Scrutiny records S.M.A.R.T. health and temperature history for physical drives. The hub runs privately on `rpimon`; the only current collector runs on `optiplex`, where the media disks are attached.

## Deployment

| Component | Host | Installed directory | Image |
| --- | --- | --- | --- |
| Web/API | `rpimon` | `/opt/scrutiny` | `ghcr.io/analogj/scrutiny:v0.9.3-web` with the checked-in index digest |
| InfluxDB | `rpimon` | `/opt/scrutiny` | `influxdb:2.8` with the checked-in index digest |
| Collector | `optiplex` | `/opt/scrutiny-collector` | Local wrapper built from pinned `v0.9.3-collector` |

The web UI binds only to `rpimon`'s private LAN address on port 8083. It has no NPM or Cloudflare route. InfluxDB is available only on the Compose network. The hub keeps its SQLite settings in `config/` and time-series data in `influxdb/` and `influxdb-config/`.

The collector sees only the three declared whole devices. Its private environment maps the two USB media disks by stable `/dev/disk/by-id` paths and maps the single NVMe controller. It receives `SYS_RAWIO` for ATA/SATA commands and `SYS_ADMIN` for NVMe admin commands; it does not mount media filesystems or the Docker socket.

## Collection and alerts

The collector runs once at startup and daily at 03:15. It retries bounded SMART identity probes before collection because the USB bridges can reject the first command after standby. A scan counts as successful only when all three expected devices publish results. That full scan updates the container health marker and calls a private Uptime Kuma push monitor; a partial scan sends an immediate `down` result instead. Kuma allows 25 hours between collection heartbeats, so a stopped container, failed cron job, unreachable hub, or skipped drive becomes an ntfy alert instead of leaving stale Scrutiny data looking current.

Scrutiny sends drive-health alerts through a separate `scrutiny-publisher` ntfy token. That identity has write-only access to the existing private monitoring topic. The mobile subscriber remains read-only. The private token URL stays in `/opt/scrutiny/.env` and `/opt/ntfy/scrutiny-ntfy.env`.

The standard ntfy generator creates the Kuma, Scrutiny, and mobile identities for new installations. An existing installation can add the Scrutiny identity without rotating the mobile password, topic, or Kuma token. Run the helper on a trusted administrative machine that has `htpasswd`, using a mode-0600 copy of the installed ntfy environment; the current `rpimon` host does not provide `htpasswd`:

```sh
python3 configs/ntfy/add-scrutiny-publisher.py \
  --env-file PRIVATE_WORKING_DIRECTORY/.env \
  --output PRIVATE_WORKING_DIRECTORY/scrutiny-ntfy.env
```

Back up ntfy before running the command, install both resulting files with mode 0600, and recreate only ntfy. The helper refuses to overwrite an existing Scrutiny credential file or duplicate the publisher.

## Current devices and test policy

The September 12, 2026 preflight detected two USB Easystore rotational disks and one NVMe system disk on `optiplex`. All three passed SMART; both HDDs reported zero reallocated, pending, and offline-uncorrectable sectors. The first deployed collection reported 59°C and 57°C for the HDDs and 44°C for the NVMe. An earlier ephemeral preflight reported 70°C for the NVMe, so cooling and temperature trends still need review. Do not schedule sustained long SMART self-tests until the two hot HDDs have been cooled.

The media volumes use NTFS through `ntfs-3g`, and the system volume uses ext4. They have no ZFS/Btrfs/RAID scrub facility. Scrutiny reads SMART telemetry but does not prove every stored sector is readable. After cooling is corrected, add scheduled short and long SMART self-tests and verify their completion separately. Do not substitute `ntfsfix` for a surface scan or Windows `chkdsk`.

Raspberry Pi microSD boot media does not expose standard SMART telemetry and is therefore outside Scrutiny. Monitor those hosts for free space, I/O errors, read-only remounts, and restore-ready backups.

## Deployment verification

On September 12, 2026, the hub and collector were deployed from this repository. Both hub containers and the collector were healthy without restart loops; `/api/health` returned HTTP 200; the summary API contained exactly one host and three SMART-capable devices; and the initial collector run published all three results. A final direct SMART check reported 60°C and 57°C for the HDDs and 42°C for the NVMe, with all three passing and no critical ATA or NVMe media-error counters. The Kuma policy reconciled idempotently at 31 active monitors, all 31 had a latest up result, and the collector push monitor retained its 90,000-second interval. Scrutiny's notification test returned success and ntfy recorded use of the separate write-only publisher. Port 8083 listened only on the private address, and no repository route, live NPM proxy host, or public DNS record existed for Scrutiny.

The first scheduled 03:15 run exposed a USB standby failure: both media drives rejected their first SMART identity command, Scrutiny skipped them, and its collector process still exited zero after publishing only the NVMe result. The wrapper now warms each declared device with bounded retries and requires exactly three publish messages before reporting `up` to Kuma. The post-fix startup scan published all three drives in three seconds, the hub summary returned three devices, all three direct SMART health checks passed, and Kuma stored the new successful heartbeat.

## Verify and recover

1. Render both projects with their private environments and verify repository/host checksums for every non-secret file.
2. Require both hub containers and the collector to be healthy without restart loops.
3. Call `http://rpimon:8083/api/health`, then confirm the dashboard lists exactly the three OptiPlex drives under one host.
4. Run one collector scan, require three publish messages, and require a fresh successful Kuma push heartbeat. A process exit code of zero without all three publish messages is a failed scan.
5. Call Scrutiny's `/api/health/notify` endpoint and read the resulting message through the mobile subscriber. Confirm the Scrutiny token can publish but cannot read, and anonymous access remains denied.

Back up `/opt/scrutiny/config`, `/opt/scrutiny/influxdb`, `/opt/scrutiny/influxdb-config`, and the private `.env` as one recovery set. Quiesce both hub containers before copying InfluxDB. The collector has no durable application data; preserve its Compose files, private device mapping, and Kuma token. Rollback of this new deployment stops only the Scrutiny projects and leaves their bind-mounted state in place.

[Official project](https://github.com/AnalogJ/scrutiny) · [Hub/spoke example](https://github.com/AnalogJ/scrutiny/blob/master/docker/example.hubspoke.docker-compose.yml) · [Device collector troubleshooting](https://github.com/AnalogJ/scrutiny/blob/master/docs/TROUBLESHOOTING_DEVICE_COLLECTOR.md) · [Application index](README.md)
