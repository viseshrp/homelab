# Architecture

The lab separates services by host role. Each Compose project has its own directory beneath `/opt`, while Nginx Proxy Manager provides a shared HTTPS entry point.

## Web access

`rpiproxy` runs Nginx Proxy Manager on ports 80 and 443, with administration on port 81. Its hostname routes lead to web apps on `rpiblog`, Uptime Kuma on `rpimon`, Plex on `optiplex`, and the Firezone management endpoint on `vpn-edge`.

Homarr is the homepage on `rpiblog:7575`. Its sidebars mix HTTPS app names with direct LAN links to tools such as Dozzle, File Browser, and qBittorrent.

Fail2ban shares the proxy host. It reads NPM's access/error logs and has Cloudflare and UFW ban actions configured.

## Application hosts

`rpiblog` contains the blog, Homarr, Anki, Vaultwarden, Planka, Linkding, FBN, and the GitHub Actions runner. The runner builds the Hugo site and copies it into `/opt/blog`, where Nginx serves the generated files.

`rpimon` contains Uptime Kuma, Dozzle, ArchiveBox with pywb, and the Paperless stack. Paperless has separate Redis, Tika, and Gotenberg containers for background processing and document conversion.

Pi-hole has its own host, `rpihole`. Home Assistant's web interface is on `rpihass`; the dashboard also points Homebridge there.

## Media storage

The OptiPlex groups Plex, qBittorrent, Gluetun, File Browser, and Reelname around two media trees.

| Host directory | qBittorrent | Plex | File Browser |
| --- | --- | --- | --- |
| `/mnt/media2` | `Media/downloads` → `/downloads` | `/mnt/media` | `Media` → `/srv`, port 8080 |
| `/mnt/media3` | `Media/downloads` → `/downloads2` | `/mnt/media3` | `Media` → `/srv`, port 8081 |

Plex configuration lives under `/opt/plex/config`; qBittorrent state lives under `/opt/qbit/qbit-data/config`. Each File Browser instance has its own database and settings file.

## VPN connections

qBittorrent shares Gluetun's network namespace. Gluetun is configured for AirVPN over WireGuard and publishes qBittorrent's web and torrent ports.

The separate `vpn-edge` host contains Firezone and WG-Easy projects for remote access. Both configurations bind UDP 51820, so they cannot use that host port simultaneously. Firezone's management port is 13000; WG-Easy's is 51821.

[Back to homelab](../README.md)
