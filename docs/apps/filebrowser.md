# File Browser

File Browser gives each media drive its own web file interface.

## My setup

The project lives at `/opt/filebrowser` on `optiplex`. It runs two `filebrowser/filebrowser` containers:

| Instance | Host port | File root mounted at `/srv` |
| --- | --- | --- |
| `filebrowser2` | 8080 | `/mnt/media2/Media` |
| `filebrowser3` | 8081 | `/mnt/media3/Media` |

Homarr links to the second instance on port 8081.

## Separate settings

Each instance has its own database directory: `filebrowser2-data/` or `filebrowser3-data/`, mounted at `/database`.

The first instance uses `settings.json`; the second uses `settings3.json`. Each file is mounted at `/config/settings.json` in its container. Both containers use `unless-stopped`.

## Verify and recover

Confirm both host mounts before opening either UI, then verify each instance shows the intended drive. An empty `/srv` can mean the media filesystem is absent, not that File Browser deleted data.

Back up each database/settings pair separately from the bulk media trees. Restore with the same root mapping and authentication choice; the checked-in template defaults `FB_NOAUTH` to `false`.

[Compose](../../docker-compose/filebrowser/docker-compose.yml) · [Operations](../operations.md) · [Application index](README.md)
