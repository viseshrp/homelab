# pywb / Webrecorder

Replays ArchiveBox WARC captures through a separate web interface.

[Homelab index](../../README.md) · [Architecture](../architecture.md) · [Inspection record](../inventory.md)

## Observed setup

Host port 8082 returned HTTP 200. Compose pairs this service with ArchiveBox; no stored page was replayed during inspection.

Host: `rpimon`. Definition: `/opt/archivebox/docker-compose.yml`.

| Service | Image/build recorded | Network / host ports | Restart |
| --- | --- | --- | --- |
| `pywb` | `webrecorder/pywb:latest` | Compose network; `8082:8080` | `always` |

| Service | Declared storage mapping |
| --- | --- |
| `pywb` | `./data:/archivebox` |
| `pywb` | `./data/wayback:/webarchive` |

Relative bind sources resolve beside the Compose file. Named volumes are Docker-managed. Paths outside `/opt` are declarations read from Compose; their contents and mount status were not inspected.

## Recreate the setup

1. Mount the ArchiveBox data tree at `/archivebox` and its `data/wayback` subdirectory at `/webarchive`.
2. Use `webrecorder/pywb` and publish host 8082 to container 8080.
3. The observed entrypoint initializes a `default` collection, adds `/archivebox/archive/*/warc/*.warc.gz`, and starts `wayback`.
4. Validate indexing with an authorized test capture. The startup command does not establish that newly added captures are continuously reindexed.

These are owner-run setup instructions; no deployment command was executed during documentation. Pin compatible versions and supply private values before starting a new instance.

## Data and recovery

Preserve the WARC source files and replay collection state. Rebuilding an index requires that the underlying captures still exist.

## Verification and troubleshooting

If the web UI responds but an archived URL is missing, check capture presence and collection indexing. Do not interpret a root-page 200 as proof that each WARC replays.

## Deployment notes

This is a service within the ArchiveBox Compose project. Operate it with that project’s data ownership and lifecycle.

Related: [ArchiveBox](archivebox.md).
