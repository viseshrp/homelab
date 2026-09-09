# File Browser

Two web file interfaces, each rooted at a different media tree.

[Homelab index](../../README.md) · [Architecture](../architecture.md) · [Inspection record](../inventory.md)

## Observed setup

Ports 8080 and 8081 both returned HTTP 200. Homarr links to the second instance. No directory contents or downloads were opened.

Host: `optiplex`. Definition: `/opt/filebrowser/docker-compose.yml`.

Source file: `docker-compose/filebrowser/docker-compose.yml`.

| Service | Image/build recorded | Network / host ports | Restart |
| --- | --- | --- | --- |
| `filebrowser2` | `filebrowser/filebrowser:latest` | Compose network; `8080:80` | `unless-stopped` |
| `filebrowser3` | `filebrowser/filebrowser:latest` | Compose network; `8081:80` | `unless-stopped` |

| Service | Declared storage mapping |
| --- | --- |
| `filebrowser2` | `./filebrowser2-data:/database` |
| `filebrowser2` | `./settings.json:/config/settings.json` |
| `filebrowser2` | `/mnt/media2/Media:/srv` |
| `filebrowser3` | `./filebrowser3-data:/database` |
| `filebrowser3` | `./settings3.json:/config/settings.json` |
| `filebrowser3` | `/mnt/media3/Media:/srv` |

Relative bind sources resolve beside the Compose file. Named volumes are Docker-managed. Paths outside `/opt` are declarations read from Compose; their contents and mount status were not inspected.

## Recreate the setup

1. Create distinct `filebrowser2-data` and `filebrowser3-data` database directories.
2. Provide separate `settings.json` and `settings3.json` files; the Compose project mounts each into its corresponding container.
3. Map the first external media tree to `/srv` on the 8080 instance and the second to `/srv` on the 8081 instance.
4. Configure explicit authentication and limit each instance to the intended data root before allowing access beyond a trusted LAN. Verify effective permissions with a disposable directory.

These are owner-run setup instructions; no deployment command was executed during documentation. Pin compatible versions and supply private values before starting a new instance.

## Data and recovery

Preserve both databases and settings files. Back up the two external media trees separately; File Browser’s database is not a copy of the files it exposes.

## Verification and troubleshooting

If the wrong files appear, first check which instance and mount root the URL selects. If configuration changes fail, inspect database ownership and settings mounts. A 200 response does not establish safe authentication or write permissions.

## Deployment notes

The host has two instances and separate database directories. No effective access-control or filesystem-write test was performed.
