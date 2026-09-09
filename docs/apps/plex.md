# Plex

Media server on the OptiPlex, with libraries backed by two externally mounted media trees.

[Homelab index](../../README.md) · [Architecture](../architecture.md) · [Inspection record](../inventory.md)

## Observed setup

Port 32400 accepted TCP and returned HTTP 401. The NPM Plex route points to this host. No library, playback session, or media file was opened.

Host: `optiplex`. Definition: `/opt/plex/docker-compose.yml`.

Source file: `docker-compose/plex/docker-compose.yml`.

| Service | Image/build recorded | Network / host ports | Restart |
| --- | --- | --- | --- |
| `plex` | `lscr.io/linuxserver/plex:latest` | host; no host mapping declared | `unless-stopped` |

| Service | Declared storage mapping |
| --- | --- |
| `plex` | `./config:/config` |
| `plex` | `./tv:/tv` |
| `plex` | `./movies:/movies` |
| `plex` | `/mnt/media2:/mnt/media` |
| `plex` | `/mnt/media3:/mnt/media3` |

Relative bind sources resolve beside the Compose file. Named volumes are Docker-managed. Paths outside `/opt` are declarations read from Compose; their contents and mount status were not inspected.

## Recreate the setup

1. Create `/opt/plex/config`, `tv`, and `movies` for the observed local bind directories.
2. Provide the two media mounts before starting Plex. The host definition maps one to container `/mnt/media` and the other to `/mnt/media3`.
3. Use the observed LinuxServer Plex image with host networking; configure library paths using container paths, not unmounted host paths.
4. Route `plex.example.com` to port 32400 and test authenticated browsing and playback from the intended client network.

These are owner-run setup instructions; no deployment command was executed during documentation. Pin compatible versions and supply private values before starting a new instance.

## Data and recovery

Back up Plex’s complete configuration/metadata directory consistently. Back up media separately; the external media trees are not inside `/opt/plex`.

## Verification and troubleshooting

An HTTP 401 establishes an HTTP responder requiring authorization, not playback health. Empty libraries can result from missing external mounts or mismatched container paths. Hardware transcoding and device access were not verified.

## Deployment notes

The host uses `/mnt/media2` and `/mnt/media3`. These path names were read from Compose only. No mount contents, storage protocol, disk capacity, or NFS relationship was inspected.

Related: [qBittorrent](qbittorrent.md), [Reelname](reelname.md), [File Browser](filebrowser.md).
