# Linkding

Bookmark storage behind `links.example.com`.

[Homelab index](../../README.md) · [Architecture](../architecture.md) · [Inspection record](../inventory.md)

## Observed setup

Port 9090 returned HTTP 302. The route and Compose default agree. The application data directory denied listing and was not opened.

Host: `rpiblog`. Definition: `/opt/linkding/docker-compose.yml`.

Source file: `docker-compose/linkding/docker-compose.yml`.

| Service | Image/build recorded | Network / host ports | Restart |
| --- | --- | --- | --- |
| `linkding` | `sissbruecker/linkding:latest` | Compose network; `${LD_HOST_PORT:-9090}:9090` | `always` |

| Service | Declared storage mapping |
| --- | --- |
| `linkding` | `${LD_HOST_DATA_DIR:-./data}:/etc/linkding/data` |

Relative bind sources resolve beside the Compose file. Named volumes are Docker-managed. Paths outside `/opt` are declarations read from Compose; their contents and mount status were not inspected.

## Recreate the setup

1. Create `/opt/linkding` with the Compose definition and a private `.env`.
2. Choose `LD_CONTAINER_NAME`, `LD_HOST_PORT`, and `LD_HOST_DATA_DIR` if overriding the observed defaults.
3. Mount the persistent data directory at `/etc/linkding/data`; the default host port is 9090.
4. Configure the HTTPS proxy route and application account, then save and retrieve a test bookmark.

These are owner-run setup instructions; no deployment command was executed during documentation. Pin compatible versions and supply private values before starting a new instance.

## Data and recovery

Preserve the data directory consistently and protect the environment file separately. An inaccessible directory still needs an owner-run backup plan.

## Verification and troubleshooting

A redirect is a reachable HTTP response. For a login or proxy failure, inspect the final application URL and account configuration. Actual `.env` overrides were not read.

## Deployment notes

No bookmark content or API token was accessed. The `LD_*` interpolation defaults in this page are defaults from Compose, not proof of every expanded runtime value.
