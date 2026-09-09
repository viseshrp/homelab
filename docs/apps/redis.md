# Redis

Paperless task broker, configured as the internal service `broker`.

[Homelab index](../../README.md) · [Architecture](../architecture.md) · [Inspection record](../inventory.md)

## Observed setup

Paperless Compose defines `redis:7`, a persistent `redisdata` volume, and `redis://broker:6379`. No Redis commands or queued task content were read.

Host association: `rpimon`.


## Recreate the setup

1. Define the broker in the same Compose network as Paperless.
2. Mount the project’s `redisdata` volume at `/data` and retain the observed `unless-stopped` restart policy.
3. Point Paperless at the internal broker service. The inspected file does not publish Redis to a host port.
4. Confirm worker processing with a disposable document after both broker and Paperless are healthy.

These are owner-run setup instructions; no deployment command was executed during documentation. Pin compatible versions and supply private values before starting a new instance.

## Data and recovery

Coordinate queue-state recovery with Paperless application data. Redis persistence is not a backup of stored documents or the application database.

## Verification and troubleshooting

A reachable Paperless UI would not by itself prove queue processing. Conversely, the refused Paperless port observed here does not identify Redis as the cause.

## Deployment notes

No standalone Redis Compose project exists; operate this dependency within `/opt/paperless`. Private environment overrides remain uninspected.

Related: [Paperless-ngx](paperless.md).
