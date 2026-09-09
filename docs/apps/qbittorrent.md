# qBittorrent

qBittorrent handles downloads on the OptiPlex. Its network traffic uses a shared network namespace with Gluetun, configured for an AirVPN WireGuard connection.

## My setup

The two-container project lives at `/opt/qbit` on `optiplex`. qBittorrent uses `lscr.io/linuxserver/qbittorrent` with UID/GID 1000 and `network_mode: service:gluetun`.

Gluetun publishes the shared ports: 8085/TCP for the web interface and 6881/TCP+UDP for torrent traffic. Homarr links to port 8085 on the LAN.

## Download directories

| Host path | qBittorrent path |
| --- | --- |
| `/opt/qbit/qbit-data/config` | `/config` |
| `/mnt/media2/Media/downloads` | `/downloads` |
| `/mnt/media3/Media/downloads` | `/downloads2` |

The configuration directory stores client settings and torrent state. The two download directories sit within the media trees mounted by Plex.

Both qBittorrent and [Gluetun](gluetun.md) use `unless-stopped` restart policies.

[Compose](../../docker-compose/qbit/docker-compose.yml) · [Setup](../configuration.md) · [Back to homelab](../../README.md)
