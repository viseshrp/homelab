# Media automation

Radarr, Sonarr, Seerr, and Bazarr run as one Compose project on `optiplex`. This installation is intentionally read-only with respect to media and downloads.

## My setup

The project lives at `/opt/media-automation`. Each application keeps independent state under its own `config/` directory and exposes a loopback-only web interface until an administrator account is configured.

| Application | Local port | State path | Role in this installation |
| --- | --- | --- | --- |
| Radarr | 7878 | `radarr/config` | Movie manager, installed without a download client or indexer |
| Sonarr | 8989 | `sonarr/config` | TV manager, installed without a download client or indexer |
| Seerr | 5055 | `seerr/config` | Request UI, not connected to Radarr or Sonarr |
| Bazarr | 6767 | `bazarr/config` | Subtitle UI, installed without providers or Arr connections |

The images are pinned by multi-architecture manifest digest. The current pins include `linux/amd64`, which matches `optiplex`.

## Media-safety boundary

Radarr and Sonarr can normally rename, move, replace, recycle, or delete library files and can tell a download client to remove completed downloads. Bazarr normally writes and upgrades subtitle files. Seerr can tell Radarr or Sonarr to search automatically after a request is approved.

This installation blocks those behaviors at several layers:

1. `/mnt/media2` and `/mnt/media3` are Docker bind mounts with `read_only: true` in Radarr, Sonarr, and Bazarr.
2. Those three containers also use a read-only root filesystem and a small `/run` tmpfs. Only their application-specific `/config` mounts are writable.
3. The stack contains no qBittorrent endpoint or credentials, no Docker socket, no indexers, no subtitle providers, and no Seerr-to-Arr service connection.
4. Reelname, Plex, qBittorrent, and Gluetun remain separate projects and are not restarted or reconfigured by this stack.

Docker documents that a read-only bind prevents a container from changing or deleting files on that mount. The Servarr documentation also makes clear that a normal Radarr/Sonarr root folder is a writable import destination, so this safety mode does not claim a working acquisition pipeline.

Do not add root folders, download clients, indexers, Bazarr providers, or Seerr Arr services while the no-media-modification requirement remains. A UI setting alone is not an adequate replacement for the read-only bind mounts.

## Reversible application hardening

The following pre-change values were read from both Radarr 6.3.0.10514 and Sonarr 4.0.19.2979 on 2026-09-10. The apply tool saves the complete three configuration resources plus this controlled subset before changing a setting. It then changes only fields listed in [`safety-policy.json`](../../configs/media-automation/safety-policy.json).

| Setting | Original value | Safety value | Why it is controlled |
| --- | --- | --- | --- |
| Completed Download Handling | `true` | `false` | Prevent automatic import processing |
| Automatically Redownload Failed | `true` | `false` | Prevent an automatic replacement search after a failure |
| Automatically Redownload Failed from Interactive Search | `true` | `false` | Prevent an interactive download failure from starting another search |
| Use Hardlinks instead of Copy | `true` | `false` | Prevent hardlink creation during an import |
| Rescan Movie/Series Folder after Refresh | `always` | `never` | Avoid automatic library reconciliation after a metadata refresh |

These controls were already safe and are recorded in the rollback manifest without being changed: Radarr movie/folder renaming, Sonarr episode renaming, empty-folder deletion, file-date changes, extra-file import, Linux permission changes, and script import.

Before applying, `manage_safety.py` requires zero root folders, download clients, and indexers in both applications. It creates and verifies `/opt/media-automation/backups/settings-before-media-safety-<UTC timestamp>/manifest.json` before the first API write. If any write or verification fails, it automatically restores the recorded values. It does not call a media, queue, command, history, file, or download-client endpoint.

```sh
sudo python3 /opt/media-automation/manage_safety.py audit
sudo python3 /opt/media-automation/manage_safety.py apply
```

The policy was applied on 2026-09-10. Its verified rollback snapshot is `/opt/media-automation/backups/settings-before-media-safety-20260910T194443Z`. The post-change audit found the documented safety values active and still found zero root folders, download clients, and indexers in both applications.

To return only the controlled settings to their exact original values, use the explicit snapshot path printed by `apply`. Restoration also refuses to run if a root folder, download client, or indexer has since been added.

```sh
sudo python3 /opt/media-automation/manage_safety.py restore \
  /opt/media-automation/backups/settings-before-media-safety-<UTC timestamp>
```

Do not restore a snapshot after making unrelated configuration changes without first reviewing its `manifest.json`. The restore operation changes only the controlled fields, so unrelated current settings are preserved.

## Media paths

The containers can read the existing host paths at the same absolute paths:

| Host and container path | Current purpose |
| --- | --- |
| `/mnt/media2/Media/MY MOVIES` | First movie library |
| `/mnt/media2/Media/TV Shows` | First TV library |
| `/mnt/media2/Media/downloads` | First qBittorrent download tree |
| `/mnt/media3/Media/movies` | Second movie library |
| `/mnt/media3/Media/tv` | Second TV library |
| `/mnt/media3/Media/downloads` | Second qBittorrent download tree |

The parent media trees are mounted read-only so path relationships remain visible without granting write access.

## Verify and recover

Before every start, verify that both host media filesystems are mounted and that the four ports are free. After start, inspect every media mount and require `RW=false`; confirm the application UIs respond; confirm Plex and qBittorrent still use their prior image IDs and have not restarted.

The four `config/` directories are the full recovery unit. Stop this project before copying its SQLite-backed state. The setting-level rollback manifest described above is the narrower recovery unit for application hardening. Bulk media is outside this project's writable recovery boundary. Rollback never requires changing or deleting media.

[Docker read-only bind mounts](https://docs.docker.com/engine/storage/bind-mounts/#use-a-read-only-bind-mount) · [Radarr settings](https://wiki.servarr.com/en/radarr/settings) · [Sonarr settings](https://wiki.servarr.com/en/sonarr/settings) · [Seerr services](https://docs.seerr.dev/using-seerr/settings/services/) · [Bazarr settings](https://wiki.bazarr.media/Additional-Configuration/Settings/) · [Compose](../../docker-compose/media-automation/docker-compose.yml) · [Operations](../operations.md) · [Application index](README.md)
