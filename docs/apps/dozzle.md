# Dozzle

Dozzle provides a browser interface for container logs.

## My setup

Dozzle runs on `rpimon` from `/opt/dozzle`, using a pinned `amir20/dozzle` image. It publishes port 8080, which Homarr opens through a direct LAN shortcut.

The local Docker socket gives it access to containers on `rpimon`. TLS-enabled Dozzle agents on the other Docker hosts publish port 7007 to the trusted LAN and are listed in `DOZZLE_REMOTE_AGENT`.

## Settings

The service uses the `simple` authentication provider and disables analytics. `/opt/dozzle/data` is mounted at `/data` for persistent settings.

The server and agents restart automatically. Authentication details, host addresses, and agent bind addresses stay in private configuration. Dozzle actions and shell access remain disabled.

## Verify and recover

Confirm that authentication works, eight hosts appear, and the container inventory matches Docker on each host. Open a representative log stream from every non-empty host. The default running count does not include a container while it is restarting; use **Show All** to inspect it.

Preserve `data/` and the private users/source configuration. Agent port 7007 is a LAN-only management interface and must not be forwarded through NPM or the router.

[Server Compose](../../docker-compose/dozzle/docker-compose.yml) · [Agent Compose](../../docker-compose/dozzle-agent/docker-compose.yml) · [Home Assistant app](../../home-assistant-dozzle-agent/README.md) · [Operations](../operations.md) · [Application index](README.md)
