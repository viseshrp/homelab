# Plex

Plex organizes and streams the media library. It shares the OptiPlex with qBittorrent, File Browser, and Reelname.

## My setup

Plex runs from `/opt/plex` on `optiplex`, using `lscr.io/linuxserver/plex`. The container uses host networking and an `unless-stopped` restart policy.

The container passes `/dev/dri` through from the host so Plex can use the OptiPlex Intel GPU for hardware-accelerated transcoding. The Plex **Disable video stream transcoding** setting must remain off; **Use hardware acceleration when available** and **Use hardware-accelerated video encoding** remain on.

`TZ` defaults to `America/New_York`, so Plex interprets its existing 02:00 to 05:00 scheduled-maintenance window in Eastern time. Override `TZ` in the private `.env` only when the host's intended local timezone changes.

Nginx Proxy Manager forwards the `plex` HTTPS hostname to port 32400. Homarr links directly to Plex's web interface.

## Libraries and storage

| Host path | Plex path | Access | Purpose |
| --- | --- | --- | --- |
| `/opt/plex/config` | `/config` | Read-write | Plex configuration and metadata |
| `/mnt/media2` | `/mnt/media` | Read-only | First external media tree |
| `/mnt/media3` | `/mnt/media3` | Read-only | Second external media tree |

The two external media trees also contain qBittorrent's download directories. Separate File Browser instances expose their `Media/` directories through the web.

The external media binds are read-only inside Plex. This blocks Plex from creating, renaming, modifying, or deleting files in those trees, including operations requested through Plex settings or its API. It does not make the host filesystems read-only and does not change qBittorrent's separate read-write `/downloads` and `/downloads2` binds.

The unused `/opt/plex/tv` and `/opt/plex/movies` host directories are deliberately not mounted into Plex. Removing the binds does not remove or modify either host directory. To restore their visibility, add `./tv:/tv` and `./movies:/movies` back to the repository Compose file, validate and synchronize it, then recreate only the `plex` service with the recorded image. The deployment procedure saves the exact pre-change installed Compose file in a timestamped root-only `/opt/plex/backups/plex-remove-unused-mounts-*` directory.

## Library deletion safeguards

Keep **Empty trash automatically after every scan** disabled (`autoEmptyTrash=0`). When a scan cannot find an item, Plex retains its library record as unavailable until the file returns or an operator deliberately empties the trash. This protects library metadata when a media filesystem is temporarily absent. It does not restore a file deleted outside Plex and does not block the manual **Empty Trash** action.

Keep **Allow media deletion** disabled (`allowMediaDeletion=0`). The read-only external media binds provide the filesystem-level barrier; these Plex preferences provide additional application-level safeguards.

Before changing either preference, save and verify a root-only copy of `Preferences.xml`. To restore automatic trash emptying, enable the setting through `Settings > Server > Library`, verify `autoEmptyTrash=1`, and update this reference in the same change. No Plex restart is required for this preference change.

Plex documents both the [library setting](https://support.plex.tv/articles/200289526-library/) and the [risk of automatically emptying library trash](https://support.plex.tv/articles/200289326-emptying-library-trash/).

## Maintenance analysis

Set **Generate intro video markers** to **as a scheduled task** (`GenerateIntroMarkerBehavior=scheduled`). Plex performs future intro analysis during the 02:00 to 05:00 Eastern maintenance window instead of starting it when media is added. Existing intro markers remain available. The analysis reads source media and stores marker data in Plex's writable configuration; it does not modify the source media files.

Set **Generate credits video markers** to **as a scheduled task** (`GenerateCreditsMarkerBehavior=scheduled`). Plex performs future credits analysis during the same maintenance window instead of starting it when media is added. Existing credits markers remain available. Credits analysis also reads source media and stores marker data in Plex's configuration without modifying the source media files.

Before changing either marker preference, save and verify a root-only copy of `Preferences.xml`. To restore either earlier behavior, set only the corresponding marker preference to **as a scheduled task and when media is added**, verify its value is `asap`, and update this reference. No Plex restart is required.

Plex documents the marker modes under [Library settings](https://support.plex.tv/articles/200289526-library/) and explains [intro analysis](https://support.plex.tv/articles/skip-content/).

Disable **Update all libraries during maintenance** (`ButlerTaskRefreshLibraries=0`). Automatic change detection (`FSEventLibraryUpdatesEnabled=1`), partial scans (`FSEventLibraryPartialScanEnabled=1`), and daily periodic scans (`ScheduledLibraryUpdatesEnabled=1`, `ScheduledLibraryUpdateInterval=86400`) remain enabled, so Plex continues discovering new content. Disabling the maintenance task removes a third standard scan from the 02:00 to 05:00 maintenance window.

Before changing the maintenance scan preference, save and verify a root-only copy of `Preferences.xml`. To restore the earlier behavior, enable **Update all libraries during maintenance**, verify `ButlerTaskRefreshLibraries=1`, and update this reference. No Plex restart is required.

Plex describes this task as a standard library scan and notes that it is [disabled by default](https://support.plex.tv/articles/201553286-scheduled-tasks/).

## Remote streaming bandwidth

Set **Internet upload speed** to 300 Mbps (`WanTotalMaxUploadRate=300000` kbps). Plex uses up to 80% of the configured value for streaming, producing a 240 Mbps aggregate remote-streaming budget. Keep **Limit remote stream bitrate** at **Original (No limit)** (`WanPerStreamMaxUploadRate=0`) and **Remote streams allowed per user** at one (`WanPerUserStreamCount=1`) until each is reviewed separately.

The value is based on an early-morning test from `optiplex` on 2026-09-12: three short trials measured 307 to 387 Mbps and a 256 MiB sustained trial measured 420 Mbps by both curl and the host interface counter. This single-destination Cloudflare measurement may overstate evening capacity. Re-test during representative remote-viewing hours after an ISP or network change.

qBittorrent currently has no explicit global upload-speed cap. Plex's total limit does not reserve bandwidth or prioritize Plex against qBittorrent, so a fast torrent upload can still contend for the uplink.

Before changing the total limit, save and verify a root-only copy of `Preferences.xml`. To restore the earlier unset behavior, clear **Internet upload speed**, verify `WanTotalMaxUploadRate=0`, and update this reference. No Plex restart is required.

Plex documents the [Internet upload speed setting and its 80% streaming allowance](https://support.plex.tv/articles/227715247-server-settings-bandwidth-and-transcoding-limits/).

## Container log retention

Docker limits Plex's `json-file` stdout/stderr logs to three files of 10 MB each. `DOCKER_LOG_MAX_SIZE` and `DOCKER_LOG_MAX_FILES` can override those defaults through a private `.env`. This limit does not remove or alter Plex's application logs under `/opt/plex/config`, its metadata, or any media file.

Changing the Docker logging options requires recreating only the `plex` container. Before recreation, save `docker logs plex` and the installed Compose/input files in a root-only backup directory. To restore unbounded Docker logging, restore the saved Compose and example-input files, validate them, and recreate only Plex with the recorded image. The saved pre-change container log remains available in the backup directory, but it cannot be reattached to Docker's live log stream.

Docker documents the [`max-size` and `max-file` rotation options](https://docs.docker.com/engine/logging/drivers/json-file/).

## Verify and recover

Confirm both media filesystems are mounted, then check the direct Plex interface, the `plex` route, library contents, metadata, and playback of a small known item. A loaded UI can hide a missing library mount or failed transcoder.

For a non-destructive transcoder check, confirm `/dev/dri/renderD128` exists inside the container, start a stream that requires a lower output resolution, and require `Transcode (hw)` in the Plex Dashboard. If the container cannot start with the device mapping, restore the saved Compose file and recreate only Plex with the recorded image; if playback fails only after changing the Plex preference, restore its recorded `TranscoderCanOnlyRemuxVideo` value.

Verify external-media protection with Docker mount inspection: both `/mnt/media` and `/mnt/media3` must report `RW=false`. Confirm qBittorrent's `/downloads` and `/downloads2` mounts still report `RW=true`. Do not test the boundary by creating, renaming, modifying, or deleting a media file.

To restore Plex write access, change only the two external Plex media binds back to read-write in the repository, validate and synchronize that Compose file, then recreate only the `plex` service with the recorded image. The deployment procedure also saves the pre-change installed Compose file in a timestamped root-only `/opt/plex/backups/plex-media-readonly-*` directory for emergency rollback. Restoring Plex write access does not require changing qBittorrent or either host filesystem.

Back up `config/` separately from the bulk media trees. Restore the same mount paths and permissions before starting Plex so an empty host directory is not mistaken for the library.

[Compose](../../docker-compose/plex/docker-compose.yml) · [Operations](../operations.md) · [Application index](README.md)
