# Inventory

This page answers four operational questions: which host owns a project, where its directory lives, how clients reach it, and what was observed live.

## Evidence and freshness

| Evidence | Scope | Freshness |
| --- | --- | --- |
| [`deployments.json`](../deployments.json) | Intended Compose host and project directory | Current checkout |
| [`configs/nginx/routes.json`](../configs/nginx/routes.json) | Sanitized reference for proxy destinations | Current checkout |
| Mac `/etc/hosts` | Local aliases used from the operator Mac | Read-only observation on September 9, 2026 |
| Nginx Proxy Manager proxy-host page | Live hostname, backend, certificate, access-list, and enabled status | Read-only observation on September 9, 2026 |
| Direct host/port probe | Earlier point-in-time SSH and service reachability | September 9, 2026; not rerun during this edit |

The NPM status below is not an application health check. “Online” is the state NPM displayed for an enabled proxy entry. Direct-port results are also snapshots, not continuous monitoring.

## Host name resolution

The Mac's `/etc/hosts` file defines these homelab aliases:

```text
rpiblog   rpihass   rpihole   rpimon   rpinfs   rpipass
rpiproxy  rpivpn    rpizwcal  rpiz2w   optiplex
```

Private addresses are intentionally omitted here. The aliases `rpiblog`, `rpihass`, `rpihole`, `rpimon`, `rpinfs`, `rpiproxy`, and `optiplex` match names used by this repository. `rpipass`, `rpivpn`, `rpizwcal`, and `rpiz2w` have no project assignment in [`deployments.json`](../deployments.json).

`vpn-edge` is a logical name in this repository for the machine hosting Firezone and WG-Easy. It was not present in the Mac's `/etc/hosts` file when checked. The live NPM Firezone route uses that machine's LAN address, while the sanitized route reference uses `vpn-edge`. Do not assume the logical name resolves until it is defined on the machine performing the lookup.

## Deployment hosts

| Host | Role | Project → installed directory |
| --- | --- | --- |
| `rpiproxy` | Ingress and blocking | [`npm`](apps/nginx-proxy-manager.md) → `/opt/nginx`; [`fail2ban`](apps/fail2ban.md) → `/opt/fail2ban` |
| `rpiblog` | Web apps and automation | [`blog`](apps/blog.md) → `/opt/blog`; [`gh-runner`](apps/github-runner.md) → `/opt/gh-runner`; [`anki`](apps/anki.md) → `/opt/anki`; [`planka`](apps/planka.md) → `/opt/planka`; [`linkding`](apps/linkding.md) → `/opt/linkding`; [`homarr`](apps/homarr.md) → `/opt/homarr`; [`vaultwarden`](apps/vaultwarden.md) → `/opt/vw`; [`fbn`](apps/fbn.md) → `/opt/fbn-compose` |
| `rpimon` | Monitoring, documents, and archives | [`uptime-kuma`](apps/uptime-kuma.md) → `/opt/kuma`; [`dozzle`](apps/dozzle.md) → `/opt/dozzle`; [`archivebox`](apps/archivebox.md) → `/opt/archivebox`; [`paperless`](apps/paperless.md) → `/opt/paperless` |
| `optiplex` | Media and downloads | [`plex`](apps/plex.md) → `/opt/plex`; [`qbit`](apps/qbittorrent.md) → `/opt/qbit`; [`filebrowser`](apps/filebrowser.md) → `/opt/filebrowser`; [Reelname](apps/reelname.md) is a host-installed CLI under `/opt/reelname` |
| `rpihole` | DNS | [`pihole`](apps/pihole.md) → `/opt/pihole-docker` |
| `rpihass` | Home automation | [Home Assistant](apps/home-assistant.md); retained [`homebridge`](apps/homebridge.md) template with no asserted live project directory |
| `rpinfs` | File transfer | [`ftp`](apps/ftp.md) → `/opt/ftp` |
| `vpn-edge` | Remote access | [`firezone`](apps/firezone.md) → `/opt/firezone`; [`wg-easy`](apps/wg-easy.md) → `/opt/wg-easy` |

## HTTPS ingress

The domain is shown as `<domain>` to keep the checked-in documentation reusable. NPM displayed a Let's Encrypt certificate, Public access, and Online status for every row.

| Public name | HTTP destination | Application | NPM status |
| --- | --- | --- | --- |
| `anki.<domain>` | `rpiblog:8080` | Anki sync | Online |
| `boards.<domain>` | `rpiblog:3001` | Planka | Online |
| `firezone.<domain>` | `vpn-edge:13000` | Firezone management | Online |
| `home.<domain>` | `rpiblog:7575` | Homarr | Online |
| `links.<domain>` | `rpiblog:9090` | Linkding | Online |
| `pass.<domain>` | `rpiblog:8089` | Vaultwarden | Online |
| `plex.<domain>` | `optiplex:32400` | Plex | Online |
| `status.<domain>` | `rpimon:3001` | Uptime Kuma | Online |
| `<domain>`, `www.<domain>` | `rpiblog:80` | Hugo site | Online |

There is no observed NPM proxy entry for Home Assistant, Homebridge, Paperless, ArchiveBox, Dozzle, File Browser, qBittorrent, Pi-hole administration, pywb, or WG-Easy administration. Those interfaces use direct LAN access unless another layer not represented here publishes them.

## Direct LAN interfaces

| Host and port | Service | Notes |
| --- | --- | --- |
| `rpiproxy:81` | Nginx Proxy Manager administration | Management surface; not one of the public proxy rows |
| `rpiblog:80` | Blog | Also the backend for the apex/`www` route |
| `rpiblog:8080` | Anki | Also behind NPM |
| `rpiblog:3001` | Planka | Also behind NPM |
| `rpiblog:7575` | Homarr | Also behind NPM |
| `rpiblog:9090` | Linkding | Also behind NPM |
| `rpiblog:8089` | Vaultwarden | Also behind NPM; Compose also publishes 3012 |
| `rpimon:3001` | Uptime Kuma | Also behind NPM |
| `rpimon:8080` | Dozzle | Homarr direct link |
| `rpimon:8002` / `rpimon:8082` | ArchiveBox / pywb | Capture UI and WARC replay |
| `rpimon:8000` | Paperless | Web interface |
| `optiplex:32400` | Plex | Also behind NPM |
| `optiplex:8080` / `optiplex:8081` | File Browser | One instance per media tree |
| `optiplex:8085` | qBittorrent | Published by Gluetun |
| `rpihole:80` | Pi-hole administration | DNS service uses port 53 |
| `rpihass:8123` / `rpihass:8581` | Home Assistant / Homebridge | Homarr direct links |
| `vpn-edge:13000` / `vpn-edge:51821` | Firezone / WG-Easy administration | The Firezone port is also behind NPM |

## Non-HTTP ports

| Endpoint | Purpose | Constraint |
| --- | --- | --- |
| `rpihole:53` TCP/UDP | LAN DNS | Clients depend on this address through their DNS configuration |
| `rpinfs:20-21`, `40000-40009` TCP | FTP control, data, and passive range | Host firewall and passive-mode routing must allow the full range |
| `optiplex:6881` TCP/UDP | qBittorrent peer traffic | Published by Gluetun's network namespace |
| `vpn-edge:51820` UDP | WireGuard | Firezone and WG-Easy both claim this default host port |
| `rpiproxy:51820` UDP | Port published by the NPM Compose template | No corresponding NPM proxy-host row; verify the intended owner before relying on it |

## Reachability snapshot

The earlier September 9 direct probe produced these results. “Refused” means the host answered but nothing accepted the connection on that port; “timeout” means the check received no answer within its bound.

| Host | SSH | Application result |
| --- | --- | --- |
| `rpiblog` | Connected | Blog, Anki, Planka, Homarr, Linkding, and Vaultwarden ports answered |
| `rpiproxy` | Connected | HTTP, HTTPS TCP, and NPM administration answered |
| `rpimon` | Connected | Uptime Kuma, Dozzle, ArchiveBox, and pywb answered; Paperless 8000 refused |
| `optiplex` | Connected | Plex, both File Browser instances, and qBittorrent answered |
| `rpihole` | Connected | DNS TCP 53 and web port 80 answered |
| `rpinfs` | Connected | FTP 21 refused |
| `vpn-edge` | Connected | Firezone 13000 returned HTTP 200; WG-Easy 51821 refused |
| `rpihass` | Refused | Home Assistant 8123 answered; Homebridge 8581 refused |

The [operations runbook](operations.md#diagnose-a-public-url) starts with the public route, then checks NPM, the backend port, the Compose project, and persistent storage in that order.

[Back to homelab](../README.md)
