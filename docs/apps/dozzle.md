# Dozzle

Dozzle provides a browser interface for container logs.

## My setup

Dozzle runs on `rpimon` from `/opt/dozzle`, using `amir20/dozzle`. It publishes port 8080, which Homarr opens through a direct LAN shortcut.

The local Docker socket gives it access to containers on the host. Environment settings also provide remote Docker-source and container-filter configuration.

## Settings

The service uses the `simple` authentication provider and disables analytics. `/opt/dozzle/data` is mounted at `/data` for persistent settings.

The container restarts automatically. Authentication details and remote-source addresses stay in private configuration.

[Compose](../../docker-compose/dozzle/docker-compose.yml) · [Setup](../configuration.md) · [Back to homelab](../../README.md)
