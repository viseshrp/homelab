# Paperless-ngx

Document archive with Redis task brokering, Tika extraction, and Gotenberg conversion.

[Homelab index](../../README.md) · [Architecture](../architecture.md) · [Inspection record](../inventory.md)

## Observed setup

The Compose stack exists at `/opt/paperless`, but host port 8000 refused the connection. The homepage points to a different historical host whose checked ports timed out.

Host: `rpimon`. Definition: `/opt/paperless/docker-compose.yml`.

Source file: `docker-compose/paperless/docker-compose.yml`.

| Service | Image/build recorded | Network / host ports | Restart |
| --- | --- | --- | --- |
| `broker` | `docker.io/library/redis:7` | Compose network; no host mapping declared | `unless-stopped` |
| `webserver` | `ghcr.io/paperless-ngx/paperless-ngx:latest` | Compose network; `8000:8000` | `unless-stopped` |
| `gotenberg` | `docker.io/gotenberg/gotenberg:7.8` | Compose network; no host mapping declared | `unless-stopped` |
| `tika` | `ghcr.io/paperless-ngx/tika:latest` | Compose network; no host mapping declared | `unless-stopped` |

| Service | Declared storage mapping |
| --- | --- |
| `broker` | `redisdata:/data` |
| `webserver` | `data:/usr/src/paperless/data` |
| `webserver` | `media:/usr/src/paperless/media` |
| `webserver` | `./export:/usr/src/paperless/export` |
| `webserver` | `./consume:/usr/src/paperless/consume` |

Relative bind sources resolve beside the Compose file. Named volumes are Docker-managed. Paths outside `/opt` are declarations read from Compose; their contents and mount status were not inspected.

## Recreate the setup

1. Create the `consume/` and `export/` bind directories and provision the named data, media, and Redis volumes.
2. Provide the private `docker-compose.env` file. The observed web service connects to `redis://broker:6379` and enables Tika/Gotenberg endpoints.
3. Start the broker, conversion services, and webserver. The inspected stack uses Redis 7, Gotenberg 7.8, and floating Paperless/Tika tags.
4. Validate port 8000 and import a disposable document before changing the dashboard URL. A directory on disk is not evidence that ingestion is operating.

These are owner-run setup instructions; no deployment command was executed during documentation. Pin compatible versions and supply private values before starting a new instance.

## Data and recovery

Preserve application data, document media, exports, and unprocessed consumption input. Use a consistent application export/database backup. The Compose file defines no separate SQL database container; the private environment was not read, so an external database cannot be ruled out.

## Verification and troubleshooting

The immediate observed issue is a refused listener on 8000. Establish whether the stack starts successfully before debugging the old dashboard destination. Separate OCR/conversion failures from webserver availability.

## Deployment notes

No personal documents, exports, database files, or named-volume contents were inspected. Conversion dependencies have their own guides below.

Related: [Redis](redis.md), [Apache Tika](tika.md), [Gotenberg](gotenberg.md).
