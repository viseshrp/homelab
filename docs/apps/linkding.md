# Linkding

Linkding stores bookmarks in a searchable web interface.

## My setup

Linkding runs from `/opt/linkding` on `rpiblog`, using `sissbruecker/linkding`. The `links` HTTPS route forwards to host port 9090.

A private `.env` file supplies application settings. The Compose definition allows the container name, host port, and data directory to be set through `LD_CONTAINER_NAME`, `LD_HOST_PORT`, and `LD_HOST_DATA_DIR`.

## Storage

The default data directory is `/opt/linkding/data`, mounted at `/etc/linkding/data` inside the container. It holds the application's persistent bookmark data.

The container has an automatic restart policy.

## Verify and recover

Check `rpiblog:9090` and the `links` route, then sign in and search for known bookmarks. This verifies the route, authentication, and existing database together.

Back up the configured data directory consistently with the private application settings. Restore it at the same container path and verify bookmark counts, tags, archived snapshots when used, and search.

[Compose](../../docker-compose/linkding/docker-compose.yml) · [Operations](../operations.md) · [Application index](README.md)
