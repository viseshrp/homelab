# Redis

Redis is the task broker for Paperless-ngx, supporting its background document-processing work.

## My setup

The `broker` service is part of `/opt/paperless` on `rpimon`. It uses Redis 7 and an `unless-stopped` restart policy.

Paperless connects over the Compose network at `redis://broker:6379`. Redis has no published host port.

## Data

The `redisdata` volume is mounted at `/data`, retaining Redis state across container replacement. Document files and Paperless application data have their own volumes.

[Back to homelab](../../README.md)
