# Homarr

Homarr is the homelab homepage. My board, “Falling Rock,” puts app shortcuts, media widgets, DNS counters, a calendar, weather, and notes on one page.

## My setup

Homarr runs on `rpiblog` from `/opt/homarr`. Its local compatibility image is based on the pinned multi-architecture Homarr 0.16.1 image. The small build-time patch accepts qBittorrent 5.2's port-specific session-cookie name while retaining compatibility with the former `SID` cookie. Nginx Proxy Manager forwards the `home` hostname to port 7575.

| Host directory | Container directory | Contents |
| --- | --- | --- |
| `homarr/configs` | `/app/data/configs` | Board configuration |
| `homarr/icons` | `/app/public/icons` | Custom icons |
| `homarr/data` | `/data` | Application data |

The container also mounts the Docker socket. `OPTIPLEX_IP`, `RPIHASS_IP`, and `RPIMON_IP` configure address mappings used by Homarr's server-side status checks. `HOMARR_BASE_IMAGE` selects the pinned upstream base, and `HOMARR_IMAGE` names the built image. Its healthcheck targets the container hostname because this Homarr release does not listen on loopback.

## Board layout

The board has one tile for every web application that is reachable from a LAN client, including each application surface monitored by Uptime Kuma. Host ping monitors, the Pi-hole DNS-function check, and the Scrutiny collector heartbeat are infrastructure checks rather than separate applications, so they do not get duplicate tiles. Background services and dependencies such as DIUN, Dozzle agents, FBN, the GitHub runner, databases, Cloudflared, Fail2ban, Gluetun, and the FTP server have no separate browser UI. Paperless remains as a shortcut even while its container is absent.

The left sidebar contains Plex, Firezone, NPM, Planka, the blog, Linkding, File Browser on media3, qBittorrent, Anki, File Browser on media2, Homarr, and WG-Easy. The right sidebar contains ArchiveBox, Pi-hole, Uptime Kuma, Homebridge, Dozzle, Home Assistant, Vaultwarden, Paperless, ntfy, pywb, Scrutiny, and PairDrop.

Every shortcut opens the application's direct LAN IPv4 address and published port. This avoids dependence on LAN DNS and public ingress for tile clicks, but it means the client must be on the trusted LAN or connected through a VPN that routes the LAN subnet. The board also includes Plex sessions, a torrent widget, and Pi-hole counters. Widget credentials are stored privately with the board configuration.

Paperless remains as a shortcut, but Homarr does not poll it while its container is absent. Homebridge is monitored by both Kuma and Homarr.

Radarr, Sonarr, Seerr, and Bazarr are intentionally absent. Their web ports bind only to OptiPlex loopback, Radarr and Sonarr have no authentication method configured, and Seerr has not completed initial setup. Adding direct-IP tiles would create dead links unless those applications were exposed to the LAN, which requires a separate security decision and administrator setup.

The checked-in `configs/homarr/vis.json` is a sanitized board policy and deployment template. It is installed as `homarr/templates/vis.json`, not over the private live board. `configs/homarr/lan-links.json` maps each tile to a logical host, port, and path. The private `/opt/homarr/lan-addresses.json` maps those logical hosts to RFC1918 addresses and is created from `lan-addresses.json.example`; never commit the live file.

Run `reconcile-board.py` while Homarr is stopped to merge the board policy into `homarr/configs/vis.json`. With `--lan-links` and `--lan-addresses`, it preserves each existing status URL, layout, widgets, and integration credentials while setting every click target to the exact direct-IP URL. Missing applications use that direct URL for both the status and click targets.

## Verify and recover

Check the `home` route, load the board from a LAN or VPN client, open every shortcut, and confirm each credentialed widget fetches data. Run the reconciler with `--check --lan-links /opt/homarr/lan-links.json --lan-addresses /opt/homarr/lan-addresses.json` to prove all template applications, status-check settings, and exact direct-IP click targets are present in the private board. A rendered board can still contain a stopped backend, a browser secure-context limitation, or a broken integration.

The qBittorrent compatibility build intentionally stops if the base image no longer contains `@ctrl/qbittorrent` 6.1.0 or the expected code. Review and remove the patch when Homarr is migrated to a release with native qBittorrent 5.2 support.

Back up all three Homarr directories and the private integration settings. Because Homarr mounts the Docker socket, keep its password and public exposure under the same review as other privileged management tools.

[Compose](../../docker-compose/homarr/docker-compose.yml) · [Operations](../operations.md) · [Application index](README.md)
