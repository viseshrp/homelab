# Homarr

Homarr is the homelab homepage. My board, “Falling Rock,” puts app shortcuts, media widgets, DNS counters, a calendar, weather, and notes on one page.

## My setup

Homarr runs on `rpiblog` from `/opt/homarr`, using `ghcr.io/ajnart/homarr`. Nginx Proxy Manager forwards the `home` hostname to port 7575.

| Host directory | Container directory | Contents |
| --- | --- | --- |
| `homarr/configs` | `/app/data/configs` | Board configuration |
| `homarr/icons` | `/app/public/icons` | Custom icons |
| `homarr/data` | `/data` | Application data |

The container also mounts the Docker socket.

## Board layout

The left sidebar contains Plex, Firezone, NPM, Planka, the blog, Linkding, File Browser, and qBittorrent. The right sidebar contains ArchiveBox, Pi-hole, Uptime Kuma, Homebridge, Dozzle, Home Assistant, Vaultwarden, and Paperless.

Some shortcuts use HTTPS hostnames; others open a host's LAN port directly. The board also includes Plex sessions, a torrent widget, and Pi-hole counters. Widget credentials are stored privately with the board configuration.

## Verify and recover

Check the `home` route, load the board, open representative public and LAN shortcuts, and confirm each credentialed widget fetches data. A rendered board can still contain stale links or broken integrations.

Back up all three Homarr directories and the private integration settings. Because Homarr mounts the Docker socket, keep its password and public exposure under the same review as other privileged management tools.

[Compose](../../docker-compose/homarr/docker-compose.yml) · [Operations](../operations.md) · [Application index](README.md)
