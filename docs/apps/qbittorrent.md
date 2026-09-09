# qBittorrent

Download client sharing Gluetun’s network namespace, with two media-download destinations.

[Homelab index](../../README.md) · [Architecture](../architecture.md) · [Inspection record](../inventory.md)

## Observed setup

Its configured web UI on host port 8085 returned HTTP 200. The Gluetun and qBittorrent service relationship was read from Compose. No download or torrent list was opened.

Host: `optiplex`. Definition: `/opt/qbit/docker-compose.yml`.

| Service | Image/build recorded | Network / host ports | Restart |
| --- | --- | --- | --- |
| `qbittorrent` | `lscr.io/linuxserver/qbittorrent:latest` | service:gluetun; no host mapping declared | `unless-stopped` |

| Service | Declared storage mapping |
| --- | --- |
| `qbittorrent` | `./qbit-data/config:/config` |
| `qbittorrent` | `/mnt/media2/Media/downloads:/downloads` |
| `qbittorrent` | `/mnt/media3/Media/downloads:/downloads2` |

Relative bind sources resolve beside the Compose file. Named volumes are Docker-managed. Paths outside `/opt` are declarations read from Compose; their contents and mount status were not inspected.

## Recreate the setup

1. Create `/opt/qbit/qbit-data/config` and provide the two external download directories before startup.
2. Configure qBittorrent with `network_mode: service:gluetun` and a dependency on Gluetun. Publish ports on Gluetun, which owns the shared network namespace.
3. The observed settings use UID/GID 1000, web UI port 8085, and torrenting port 6881. Map the two host download trees to `/downloads` and `/downloads2`.
4. Set private UI credentials and test the VPN exit path before transferring data. Confirm the completed-download directory matches the path Plex or an owner-run rename step will use.

These are owner-run setup instructions; no deployment command was executed during documentation. Pin compatible versions and supply private values before starting a new instance.

## Data and recovery

Preserve the entire client configuration/state directory and any partial downloads needed for resume. Data stored in the external download trees requires a separate backup decision.

## Verification and troubleshooting

If the web UI is unreachable, check Gluetun and the shared port mapping before changing qBittorrent. A responding UI does not establish a working VPN tunnel, provider port forwarding, or a tested kill switch.

## Deployment notes

The two-service structure was inspected on the host. Homarr’s torrent-widget error is separate from the reachable client UI.

Related: [Gluetun](gluetun.md), [Plex](plex.md).
