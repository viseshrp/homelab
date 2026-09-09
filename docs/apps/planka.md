# Planka

Kanban boards backed by a private PostgreSQL service.

[Homelab index](../../README.md) · [Architecture](../architecture.md) · [Inspection record](../inventory.md)

## Observed setup

Port 3001 returned HTTP 200 and matches `boards.example.com`. The inspected host definition pins Planka 2.2.1 by image digest.

Host: `rpiblog`. Definition: `/opt/planka/docker-compose.yml`.

Source file: `docker-compose/planka/docker-compose.yml`.

| Service | Image/build recorded | Network / host ports | Restart |
| --- | --- | --- | --- |
| `planka` | `ghcr.io/plankanban/planka:2.2.1 (digest pinned)` | Compose network; `3001:1337` | `unless-stopped` |
| `postgres` | `postgres:14-alpine` | Compose network; no host mapping declared | `unless-stopped` |

| Service | Declared storage mapping |
| --- | --- |
| `planka` | `data:/app/data` |
| `postgres` | `db-data:/var/lib/postgresql/data` |

Relative bind sources resolve beside the Compose file. Named volumes are Docker-managed. Paths outside `/opt` are declarations read from Compose; their contents and mount status were not inspected.

## Recreate the setup

1. Use the host’s two-service structure: Planka on host 3001/container 1337 and PostgreSQL 14 on the internal Compose network.
2. Provide a private secret key and database URL, set the HTTPS base URL, and account for the reverse proxy.
3. Persist the current Planka `/app/data` volume plus the PostgreSQL data volume. Use database authentication appropriate to your own deployment.
4. Route `boards.example.com` to host port 3001 and verify board creation, attachments, and access through HTTPS.

These are owner-run setup instructions; no deployment command was executed during documentation. Pin compatible versions and supply private values before starting a new instance.

## Data and recovery

Back up PostgreSQL consistently and the complete application data volume as a matching set. The observed `backups/` directory exists, but no backup contents or schedule were inspected.

## Verification and troubleshooting

If boards load without attachments, check the `/app/data` mount. If startup fails, inspect database readiness and credentials. `depends_on` without a readiness condition does not by itself establish database health.

## Deployment notes

The inspected host uses digest-pinned Planka 2.2.1 with `data:/app/data` and a separate PostgreSQL volume.

Related: [PostgreSQL](postgresql.md).
