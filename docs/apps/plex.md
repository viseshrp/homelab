# Plex

Plex organizes and streams the media library. It shares the OptiPlex with qBittorrent, File Browser, and Reelname.

## My setup

Plex runs from `/opt/plex` on `optiplex`, using `lscr.io/linuxserver/plex`. The container uses host networking and an `unless-stopped` restart policy.

Nginx Proxy Manager forwards the `plex` HTTPS hostname to port 32400. Homarr links directly to Plex's web interface.

## Libraries and storage

| Host path | Plex path | Purpose |
| --- | --- | --- |
| `/opt/plex/config` | `/config` | Plex configuration and metadata |
| `/opt/plex/tv` | `/tv` | TV directory |
| `/opt/plex/movies` | `/movies` | Movie directory |
| `/mnt/media2` | `/mnt/media` | First media tree |
| `/mnt/media3` | `/mnt/media3` | Second media tree |

The two external media trees also contain qBittorrent's download directories. Separate File Browser instances expose their `Media/` directories through the web.

## Verify and recover

Confirm both media filesystems are mounted, then check the direct Plex interface, the `plex` route, library contents, metadata, and playback of a small known item. A loaded UI can hide a missing library mount or failed transcoder.

Back up `config/` separately from the bulk media trees. Restore the same mount paths and permissions before starting Plex so an empty host directory is not mistaken for the library.

[Compose](../../docker-compose/plex/docker-compose.yml) · [Operations](../operations.md) · [Application index](README.md)
