# Homarr

The homelab homepage, titled “Falling Rock,” groups app shortcuts and shows calendar, media, DNS, weather, and notes widgets.

[Homelab index](../../README.md) · [Architecture](../architecture.md) · [Inspection record](../inventory.md)

## Observed setup

The existing homepage rendered in the in-app browser. Direct port 7575 returned HTTP 307. Both sidebars were inspected.

Host: `rpiblog`. Definition: `/opt/homarr/docker-compose.yml`.

Source file: `docker-compose/homarr/docker-compose.yml`.

| Service | Image/build recorded | Network / host ports | Restart |
| --- | --- | --- | --- |
| `homarr` | `ghcr.io/ajnart/homarr:latest` | Compose network; `7575:7575` | `always` |

| Service | Declared storage mapping |
| --- | --- |
| `homarr` | `./homarr/configs:/app/data/configs` |
| `homarr` | `./homarr/icons:/app/public/icons` |
| `homarr` | `/var/run/docker.sock:/var/run/docker.sock` |
| `homarr` | `./homarr/data:/data` |

Relative bind sources resolve beside the Compose file. Named volumes are Docker-managed. Paths outside `/opt` are declarations read from Compose; their contents and mount status were not inspected.

## Recreate the setup

1. Create `/opt/homarr/homarr/{configs,icons,data}` for the observed bind layout. The inspected image is `ghcr.io/ajnart/homarr` family.
2. Configure a private dashboard password and your own base URL. Publish port 7575 behind the `home.example.com` proxy route.
3. Add the app URLs from this inventory. The dashboard links directly to several LAN ports; those links require LAN or suitable VPN access.
4. Configure integrations separately from shortcuts. A working link does not establish that its API credentials or widget are configured.

These are owner-run setup instructions; no deployment command was executed during documentation. Pin compatible versions and supply private values before starting a new instance.

## Data and recovery

Preserve configuration, icons, and the additional `homarr/data` directory present on the host. Board exports can contain API credentials and private links; do not publish a raw export.

## Verification and troubleshooting

The torrent widget reported no supported client. Pi-hole counters displayed zeros. These UI observations do not prove qBittorrent or DNS is down: their service ports responded. Fix integration settings independently of app reachability.

## Deployment notes

The live sidebar points ArchiveBox and Paperless at a host that timed out. The host mounts `./homarr/data:/data` and the Docker socket.

Related: [Nginx Proxy Manager](nginx-proxy-manager.md), [qBittorrent](qbittorrent.md), [Pi-hole](pihole.md).
