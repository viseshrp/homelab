# Linkding

Linkding stores bookmarks in a searchable web interface.

## My setup

Linkding runs from `/opt/linkding` on `rpiblog`, using `sissbruecker/linkding`. The `links` HTTPS route forwards to host port 9090.

A private `.env` file supplies application settings. The Compose definition allows the container name, host port, and data directory to be set through `LD_CONTAINER_NAME`, `LD_HOST_PORT`, and `LD_HOST_DATA_DIR`.

## Storage

The default data directory is `/opt/linkding/data`, mounted at `/etc/linkding/data` inside the container. It holds the application's persistent bookmark data.

The container has an automatic restart policy.

[Back to homelab](../../README.md)
