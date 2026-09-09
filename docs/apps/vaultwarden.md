# Vaultwarden

Provides the password-vault service behind `pass.example.com`.

[Homelab index](../../README.md) · [Architecture](../architecture.md) · [Inspection record](../inventory.md)

## Observed setup

The host’s port 8089 returned HTTP 200 and matches the NPM route. No login, vault item, administration token, or database content was inspected.

Host: `rpiblog`. Definition: `/opt/vw/docker-compose.yml`.

Source file: `docker-compose/vaultwarden/docker-compose.yml`.

| Service | Image/build recorded | Network / host ports | Restart |
| --- | --- | --- | --- |
| `vaultwarden` | `vaultwarden/server:latest` | Compose network; `8089:80, 3012:3012` | `always` |

| Service | Declared storage mapping |
| --- | --- |
| `vaultwarden` | `./vw-data:/data` |

Relative bind sources resolve beside the Compose file. Named volumes are Docker-managed. Paths outside `/opt` are declarations read from Compose; their contents and mount status were not inspected.

## Recreate the setup

1. Create `/opt/vw/vw-data` and mount it at `/data` for `vaultwarden/server`.
2. Set the HTTPS domain and private SMTP configuration. The inspected file disables new signups.
3. Use host port 8089 for the current proxy route.
4. The observed file also publishes 3012 and enables the legacy WebSocket setting. Confirm notification behavior for the image version you deliberately deploy.

These are owner-run setup instructions; no deployment command was executed during documentation. Pin compatible versions and supply private values before starting a new instance.

## Data and recovery

Preserve all of `vw-data`, including database and attachments, using a consistent backup. Store SMTP credentials and any administration secret privately. Test recovery with a non-production account.

## Verification and troubleshooting

If the web vault loads but a client fails, check its server URL, HTTPS, and authentication. SMTP delivery and sync are separate checks from the root-page response.

## Deployment notes

The historical `rpipass` host refuses SSH; the current route and `/opt/vw` both locate this deployment on `rpiblog`. A floating image tag does not identify the installed server version.
