# Cal.com

Scheduling application described by the available Compose configuration.

[Homelab index](../../README.md) · [Architecture](../architecture.md) · [Inspection record](../inventory.md)

## Observed setup

Deployment was not verified during the `/opt` inspection or in the live dashboard.

Source file: `docker-compose/calcom/docker-compose.yml`.

| Service | Image/build recorded | Network / host ports | Restart |
| --- | --- | --- | --- |
| `database` | `postgres` | Compose network; no host mapping declared | `always` |
| `calcom` | `calcom.docker.scarf.sh/calcom/cal.com` | Compose network; `3000:3000` | `always` |

| Service | Declared storage mapping |
| --- | --- |
| `database` | `database-data:/var/lib/postgresql/data/` |

Relative bind sources resolve beside the Compose file. Named volumes are Docker-managed. Paths outside `/opt` are declarations read from Compose; their contents and mount status were not inspected.

## Recreate the setup

1. The template pairs Cal.com with PostgreSQL and publishes host port 3000 on a dedicated `stack` network.
2. Provide a private `.env` containing the application URL, database configuration, authentication secret, and encryption key required by the chosen release.
3. Supply the Dockerfile and build context referenced by Compose, or configure an image-only deployment for the selected version.
4. Initialize and test the app with a non-production calendar before publishing a scheduling endpoint. No calendar connection was inspected.

These are owner-run setup instructions; no deployment command was executed during documentation. Pin compatible versions and supply private values before starting a new instance.

## Data and recovery

Preserve PostgreSQL and the encryption/authentication secrets together. Without the original encryption material, stored integration credentials may not be recoverable.

## Verification and troubleshooting

Check the build context, environment variables, and PostgreSQL connection if startup fails. A running web interface still requires a separate calendar-integration test.

## Deployment notes

The template uses unpinned application/database images. No Cal.com version, active host, or external calendar account is claimed.
