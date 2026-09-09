# ArchiveBox

Captures web pages locally and shares its archive directory with a pywb replay service.

[Homelab index](../../README.md) · [Architecture](../architecture.md) · [Inspection record](../inventory.md)

## Observed setup

Port 8002 returned HTTP 302; pywb on 8082 returned 200. The dashboard’s ArchiveBox shortcut still points to a historical host that timed out.

Host: `rpimon`. Definition: `/opt/archivebox/docker-compose.yml`.

Source file: `docker-compose/archivebox/docker-compose.yml`.

| Service | Image/build recorded | Network / host ports | Restart |
| --- | --- | --- | --- |
| `archivebox` | `${DOCKER_IMAGE:-archivebox/archivebox:dev}` | Compose network; `8002:8000` | `always` |
| `pywb` | `webrecorder/pywb:latest` | Compose network; `8082:8080` | `always` |

| Service | Declared storage mapping |
| --- | --- |
| `archivebox` | `./data:/data` |
| `pywb` | `./data:/archivebox` |
| `pywb` | `./data/wayback:/webarchive` |

Relative bind sources resolve beside the Compose file. Named volumes are Docker-managed. Paths outside `/opt` are declarations read from Compose; their contents and mount status were not inspected.

## Recreate the setup

1. Create `/opt/archivebox/data` and mount it at `/data` for ArchiveBox.
2. The image expression defaults to `archivebox/archivebox:dev`; choose and retain a tested release for your own install rather than assuming the floating default is reproducible.
3. The inspected settings disable the public index, snapshots, and add view; SSL checking is enabled, timeout is 120 seconds, and the media-size setting is `1500m`.
4. Publish 8002 for ArchiveBox and 8082 for the paired replay service. Validate a disposable capture and replay before updating dashboard shortcuts.

These are owner-run setup instructions; no deployment command was executed during documentation. Pin compatible versions and supply private values before starting a new instance.

## Data and recovery

Preserve the entire shared data tree, including archive metadata, captured assets, WARC files, and replay collection state. Captures can contain private or authenticated pages.

## Verification and troubleshooting

A working login redirect does not prove new captures work. If capture succeeds but replay fails, inspect pywb’s indexing and WARC mounts. A saved dashboard URL may be stale independently of both services.

## Deployment notes

Both services mount the same host data tree through different container paths. The Compose command was present; no captures were initiated and no archived content was opened.

Related: [pywb / Webrecorder](pywb.md).
