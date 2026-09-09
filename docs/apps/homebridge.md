# Homebridge

HomeKit bridge represented by a repository Compose file and a homepage shortcut.

[Homelab index](../../README.md) · [Architecture](../architecture.md) · [Inspection record](../inventory.md)

## Observed setup

The dashboard targets `rpihass:8581`, which refused the connection. SSH access was also refused, so host installation and current configuration are unverified.

Host association: `rpihass`.

Source file: `docker-compose/homebridge/docker-compose.yml`.

| Service | Image/build recorded | Network / host ports | Restart |
| --- | --- | --- | --- |
| `homebridge` | `oznu/homebridge:latest` | host; no host mapping declared | `always` |

| Service | Declared storage mapping |
| --- | --- |
| `homebridge` | `/mnt/data/supervisor/homeassistant/homebridge:/homebridge` |

Relative bind sources resolve beside the Compose file. Named volumes are Docker-managed. Paths outside `/opt` are declarations read from Compose; their contents and mount status were not inspected.

## Recreate the setup

1. The repository image is `oznu/homebridge:latest` with host networking.
2. Its persistent `/homebridge` directory is sourced from a path under a Home Assistant supervisor tree. This is a configuration clue, not confirmation of the current host installation mode.
3. Provide plugins, pairing state, and credentials privately. The repository does not include that application state.
4. Validate the bridge’s management UI and device discovery independently; the browser shortcut alone does not show a functioning HomeKit bridge.

These are owner-run setup instructions; no deployment command was executed during documentation. Pin compatible versions and supply private values before starting a new instance.

## Data and recovery

Preserve the complete Homebridge data directory, plugin configuration, and pairing state securely. A Compose file alone cannot restore pairings.

## Verification and troubleshooting

A refused 8581 listener is the observed issue. Establish the deployment and listening port before changing dashboard links. Host networking is relevant to local discovery but does not prove it works.

## Deployment notes

No HomeKit devices, pairing codes, or Home Assistant supervisor directories were read.

Related: [Home Assistant](home-assistant.md).
