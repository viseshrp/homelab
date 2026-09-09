# Glances

Host metrics tooling represented by a Compose build and a separate systemd service template.

[Homelab index](../../README.md) · [Architecture](../architecture.md) · [Inspection record](../inventory.md)

## Observed setup

Repository files were inspected. No active Glances installation was verified under the accessible hosts’ `/opt` trees.

Source file: `docker-compose/glances/docker-compose.yml`.

| Service | Image/build recorded | Network / host ports | Restart |
| --- | --- | --- | --- |
| `glances` | `Local build` | host; `61208:61208` | `always` |

| Service | Declared storage mapping |
| --- | --- |
| `glances` | `/var/run/docker.sock:/var/run/docker.sock:ro` |

Relative bind sources resolve beside the Compose file. Named volumes are Docker-managed. Paths outside `/opt` are declarations read from Compose; their contents and mount status were not inspected.

## Recreate the setup

1. The Compose option uses host networking, host PID visibility, privileged mode, and a read-only Docker socket mount.
2. Its custom Dockerfile expects `glances.conf`. Supply the intended configuration in the build directory.
3. The separate service file runs `/opt/glances/venv/bin/glances -s --disable-webui --disable-history`; this server mode differs from the web-oriented Compose template.
4. Choose the interface you intend to operate before using the kiosk scripts: web pages and Glances client/server connections are different protocols.

These are owner-run setup instructions; no deployment command was executed during documentation. Pin compatible versions and supply private values before starting a new instance.

## Data and recovery

Preserve the selected configuration, dependency versions, and service definition. No history store or active metrics database was inspected.

## Verification and troubleshooting

Check whether a client expects the web port 61208 or server port 61209. A host-network Compose mapping does not provide an independent port-translation layer.

## Deployment notes

The systemd unit is a repository file only. No `/etc/systemd` directory or running system service was inspected.
