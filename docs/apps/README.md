# Application index

The pages in this directory document how each service fits this lab: deployment host, access path, dependencies, private inputs, and persistent state. Use [the operations runbook](../operations.md) for the shared update and recovery workflow.

## Public web applications

| Application | Host | Public route | Durable state |
| --- | --- | --- | --- |
| [Hugo blog](blog.md) | `rpiblog` | Apex and `www` | Generated `public/`; source lives elsewhere |
| [Homarr](homarr.md) | `rpiblog` | `home` | `homarr/configs`, `homarr/icons`, `homarr/data` |
| [Anki](anki.md) | `rpiblog` | `anki` | `data/` |
| [Planka](planka.md) | `rpiblog` | `boards` | App `data` and PostgreSQL `db-data` volumes |
| [Linkding](linkding.md) | `rpiblog` | `links` | Configured data directory |
| [Vaultwarden](vaultwarden.md) | `rpiblog` | `pass` | `vw-data/` |
| [Plex](plex.md) | `optiplex` | `plex` | `config/` plus both media trees |
| [Uptime Kuma](uptime-kuma.md) | `rpimon` | `status` | `uptime-kuma-data/` |
| [Firezone](firezone.md) | `vpn-edge` | `firezone` | `firezone/`, PostgreSQL volume, private keys/settings |

## LAN and internal applications

| Application | Host | Access | Durable state |
| --- | --- | --- | --- |
| [Dozzle](dozzle.md) | `rpimon` | LAN port 8080 | `data/`; private users and remote-source settings |
| [Paperless-ngx](paperless.md) | `rpimon` | LAN port 8000 | Data/media volumes, consume/export directories |
| [ArchiveBox](archivebox.md) and [pywb](pywb.md) | `rpimon` | LAN ports 8002/8082 | Shared `data/` capture tree |
| [File Browser](filebrowser.md) | `optiplex` | LAN ports 8080/8081 | Separate databases/settings plus media trees |
| [qBittorrent](qbittorrent.md) through [Gluetun](gluetun.md) | `optiplex` | LAN port 8085 | Client config, VPN state, download trees |
| [Pi-hole](pihole.md) | `rpihole` | DNS 53 and LAN web UI | `etc-pihole`, `etc-dnsmasq.d` |
| [Home Assistant](home-assistant.md) | `rpihass` | LAN port 8123 and `hass` tunnel route | Host-managed Home Assistant configuration/state |
| [Homebridge](homebridge.md) | `rpihass` | LAN port 8581 | Supervisor-managed app configuration mapped to `/homebridge` |
| [WG-Easy](wg-easy.md) | `vpn-edge` | UDP 51820, LAN admin 51821 | WireGuard project directory |
| [FTP server](ftp.md) | `rpinfs` | FTP and passive port range | External media directory plus private account settings |

## Workers and supporting components

| Component | Parent stack | Job |
| --- | --- | --- |
| [Dozzle Agent](dozzle.md) | Docker hosts | Sends container metadata and logs to the central Dozzle server over TLS |
| [GitHub Actions runner](github-runner.md) | Blog | Builds Hugo and writes generated output to `/opt/blog` |
| [FBN](fbn.md) | Standalone on `rpiblog` | Monitors a Facebook group and queues Apprise deliveries |
| [PostgreSQL](postgresql.md) | Planka and Firezone | Application databases on isolated Compose networks |
| [Redis](redis.md) | Paperless | Task broker |
| [Apache Tika](tika.md) | Paperless | Text and metadata extraction |
| [Gotenberg](gotenberg.md) | Paperless | Document conversion |
| [Reelname](reelname.md) | Media host | Command-line media filename cleanup |
| [Kiosk](kiosk.md) | Desktop helper | Rotates selected monitoring pages |

## Ingress and security

| Component | Host | Job |
| --- | --- | --- |
| [Nginx Proxy Manager](nginx-proxy-manager.md) | `rpiproxy` | TLS termination and HTTP routing |
| [Fail2ban](fail2ban.md) | `rpiproxy` | Detects hostile paths in NPM logs and applies source-IP bans |
| [Cloudflare](cloudflare.md) | External edge/API and `rpiproxy` connector | DNS, Home Assistant tunnel, and owned block rules |

[Back to homelab](../../README.md)
