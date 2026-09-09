# Operations and recovery

[Homelab index](../README.md) · [Inspection record](inventory.md)

These notes describe owner-run operations. The documentation task performed no deployment, restart, upgrade, backup, remote write, or permission change.

## Configuration layout

Most inspected applications use `/opt/<app>/docker-compose.yml` with relative bind directories next to it. FBN uses `/opt/fbn-compose/compose.yaml`; Reelname is an installed Python environment. Application directories include `/opt/nginx` for NPM, `/opt/kuma` for Kuma, `/opt/vw` for Vaultwarden, and `/opt/pihole-docker` for Pi-hole.

Each app guide records service images, ports, storage, dependencies, and private inputs from the available evidence.

## Rebuild one application

1. Select a specific app guide and obtain its compatible source/Compose definition. Confirm the image generation and host architecture yourself; neither is established by an unpinned image tag.
2. Prepare its persistent directories, named volumes, and any external storage. Choose ownership compatible with the container user before importing existing data.
3. Supply private environment files, credentials, and domain values. Resolve the configuration privately; do not publish expanded Compose output.
4. Start and validate the app on a test destination before updating its proxy route and dashboard shortcut.

A reconstruction also needs application state and private inputs: database contents, build configuration, integration settings, and any included Home Assistant configuration files.

## Updates

The per-project repository script runs Compose pull/up with orphan removal and prunes images. The global script also upgrades OS packages and prunes Docker volumes. Neither was run. Global pruning is not a backup procedure and can remove recovery data.

Use an application-specific update window:

1. Record the current image revision and preserve a consistent backup of the app’s data and private configuration.
2. Review migration requirements for the selected version, especially database versions and volume-layout changes.
3. Update one Compose project and verify its authenticated workflow, data, and proxy path.
4. Keep the prior image and backup until recovery has been tested; an older image may not accept a migrated database.

## Recovery coverage

| Data class | Examples | What a recovery set needs |
| --- | --- | --- |
| SQLite/application state | Vaultwarden, Kuma, Linkding, FBN, File Browser | Consistent database plus related files and private configuration |
| PostgreSQL-backed apps | Planka, Firezone, Cal.com template | Consistent database backup, matching app files, secrets, version information |
| Document archives | Paperless, ArchiveBox/pywb | Application metadata, source/output files, WARC/media data, ingestion/export state |
| Media stack | Plex, qBittorrent, external media roots | Metadata/client state plus an explicit policy for original media and unfinished downloads |
| Network/access state | NPM, Pi-hole, WireGuard definitions | Configurations, certificates/keys, DNS settings, peer state, and private recovery access |

An `/opt` copy misses Docker-managed named volumes and external media. Reading a volume declaration did not verify a backup of it. Named `backups` directories were not opened, and no restore was attempted.

[Stashfleet](apps/stashfleet.md) can be configured as a backup client, but the included implementation has not been verified with real lab transfers. It does not quiesce applications or automatically make database snapshots consistent. Its separate [full guide](../stashfleet/README.md) documents scheduling, retention, encryption options, and limitations.

## Private configuration

Keep passwords, SMTP credentials, database URLs containing credentials, runner tokens, Cloudflare identifiers, WireGuard keys, browser profiles, cookies, and app integration tokens out of public Markdown and screenshots. A raw dashboard export or resolved Compose configuration can include several of these at once.

The new README and docs use aliases, placeholder domains, and generic account paths. They omit private IPs, personal device names, account-specific dashboard links, and authentication values.

Access policy is part of reconstructing the setup. Explicitly configure authentication for dashboards and file interfaces, isolate database and management ports, and review Docker-socket mounts. Compose declarations alone do not prove the effective controls of a running service.

## Keep the docs current

When an app moves, update the app guide, host inventory, NPM destination, and Homarr link as one change. Record the new check date and distinguish a listening port from a working authenticated workflow. Retire obsolete links explicitly rather than treating old addresses as current topology.
