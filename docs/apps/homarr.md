# Homarr

Homarr is the homelab homepage. My board, “Falling Rock,” puts app shortcuts, media widgets, DNS counters, a calendar, weather, and notes on one page.

## My setup

Homarr runs on `rpiblog` from `/opt/homarr`. Its local compatibility image is based on the pinned multi-architecture Homarr 0.16.1 image. The small build-time patch accepts qBittorrent 5.2's port-specific session-cookie name while retaining compatibility with the former `SID` cookie. Nginx Proxy Manager forwards the `home` hostname to port 7575.

| Host directory | Container directory | Contents |
| --- | --- | --- |
| `homarr/configs` | `/app/data/configs` | Board configuration |
| `homarr/icons` | `/app/public/icons` | Custom icons |
| `homarr/data` | `/data` | Application data |

The container also mounts the Docker socket. `OPTIPLEX_IP`, `RPIHASS_IP`, and `RPIMON_IP` configure address mappings so the board can use stable host names when those names are unavailable through Docker's DNS. `HOMARR_BASE_IMAGE` selects the pinned upstream base, and `HOMARR_IMAGE` names the built image. Its healthcheck targets the container hostname because this Homarr release does not listen on loopback.

## Board layout

The board has one tile for each application surface monitored by Uptime Kuma. Host ping monitors, the Pi-hole DNS-function check, and the Scrutiny collector heartbeat are infrastructure checks rather than separate applications, so they do not get duplicate tiles. Paperless remains as one additional shortcut even while its container is absent.

The left sidebar contains Plex, Firezone, NPM, Planka, the blog, Linkding, File Browser on media3, qBittorrent, Anki, File Browser on media2, and Homarr. The right sidebar contains ArchiveBox, Pi-hole, Uptime Kuma, Homebridge, Dozzle, Home Assistant, Vaultwarden, Paperless, ntfy, pywb, and Scrutiny.

Some shortcuts use HTTPS hostnames; others open a host's LAN port directly. The board also includes Plex sessions, a torrent widget, and Pi-hole counters. Widget credentials are stored privately with the board configuration.

Paperless remains as a shortcut, but Homarr does not poll it while its container is absent. Homebridge is monitored by both Kuma and Homarr.

The checked-in `configs/homarr/vis.json` is a sanitized board policy and deployment template. It is installed as `homarr/templates/vis.json`, not over the private live board. Run `reconcile-board.py` while Homarr is stopped to merge that policy into `homarr/configs/vis.json`; the reconciler preserves live URLs, layout, widgets, and integration credentials while adding missing applications and aligning names and status-check settings.

## Verify and recover

Check the `home` route, load the board, open representative public and LAN shortcuts, and confirm each credentialed widget fetches data. Run the reconciler with `--check` to prove all template applications and status-check settings are present in the private board. A rendered board can still contain stale links or broken integrations.

The qBittorrent compatibility build intentionally stops if the base image no longer contains `@ctrl/qbittorrent` 6.1.0 or the expected code. Review and remove the patch when Homarr is migrated to a release with native qBittorrent 5.2 support.

Back up all three Homarr directories and the private integration settings. Because Homarr mounts the Docker socket, keep its password and public exposure under the same review as other privileged management tools.

[Compose](../../docker-compose/homarr/docker-compose.yml) · [Operations](../operations.md) · [Application index](README.md)
