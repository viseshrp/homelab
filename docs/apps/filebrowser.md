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

[Compose](../../docker-compose/filebrowser/docker-compose.yml) · [Setup](../configuration.md) · [Back to homelab](../../README.md)
