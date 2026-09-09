# Dozzle

Web interface for container logs, with configuration for remote Docker sources.

[Homelab index](../../README.md) · [Architecture](../architecture.md) · [Inspection record](../inventory.md)

## Observed setup

Port 8080 returned HTTP 307. The host definition enables the simple authentication provider and disables analytics. No log streams or remote Docker endpoints were opened.

Host: `rpimon`. Definition: `/opt/dozzle/docker-compose.yml`.

Source file: `docker-compose/dozzle/docker-compose.yml`.

| Service | Image/build recorded | Network / host ports | Restart |
| --- | --- | --- | --- |
| `dozzle` | `amir20/dozzle:latest` | Compose network; `8080:8080` | `always` |

| Service | Declared storage mapping |
| --- | --- |
| `dozzle` | `./data:/data` |
| `dozzle` | `/var/run/docker.sock:/var/run/docker.sock` |

Relative bind sources resolve beside the Compose file. Named volumes are Docker-managed. Paths outside `/opt` are declarations read from Compose; their contents and mount status were not inspected.

## Recreate the setup

1. Create `/opt/dozzle/data` for the host’s persistent authentication/settings mount.
2. Mount the local Docker socket and publish 8080. Configure trusted remote Docker connectivity only if needed.
3. Provide private authentication data compatible with the selected image.
4. Link the LAN interface from Homarr and verify each intended source independently; a listening UI does not prove remote sources are connected.

These are owner-run setup instructions; no deployment command was executed during documentation. Pin compatible versions and supply private values before starting a new instance.

## Data and recovery

Back up the data directory and private remote-source settings. Container logs are not a substitute for application data backups.

## Verification and troubleshooting

If the UI redirects but containers are missing, check authentication, Docker connectivity, and source filtering. Avoid exposing unauthenticated Docker TCP endpoints to make a dashboard work.

## Deployment notes

The host persists settings with `./data:/data`. Docker socket access and logs can expose credentials; neither belongs in a public screenshot or copied diagnostic transcript.
