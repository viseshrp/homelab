# Dozzle

Dozzle provides a browser interface for container logs.

## My setup

Dozzle runs on `rpimon` from `/opt/dozzle`, using a pinned `amir20/dozzle` image. It publishes port 8080, which Homarr opens through a direct LAN shortcut.

The local Docker socket gives it access to containers on `rpimon`. TLS-enabled Dozzle agents on the other Docker hosts publish port 7007 to the trusted LAN and are listed in `DOZZLE_REMOTE_AGENT`.

## Settings

The service uses the `simple` authentication provider and disables analytics. `/opt/dozzle/data` is mounted at `/data` for persistent settings.

The server and agents restart automatically. Authentication details, host addresses, and agent bind addresses stay in private configuration. Dozzle actions and shell access remain disabled.

## Verify and recover

Confirm that authentication works, eight hosts appear, and the container inventory matches Docker on each host. Open a representative log stream from every non-empty host. The default running count does not include a container while it is restarting; enable **Show stopped containers** in Settings to inspect it.

Preserve `data/` and the private users/source configuration. Agent port 7007 is a LAN-only management interface and must not be forwarded through NPM or the router.

## Verified state

The September 9, 2026 cutover showed eight hosts and 49 containers in Dozzle. The per-host total matched the aggregate Docker inventory: `optiplex` 6, `rpiblog` 11, `rpihass` 14, `rpihole` 2, `rpimon` 4, `rpinfs` 1, `rpiproxy` 8, and `rpivpn` 3. The host cards showed 38 running containers; Docker also reported `gh-runner-worker-1` in its existing restarting state, and it appeared when stopped containers were enabled.

All seven remote agents accepted TLS connections on port 7007, and every former port-2375 endpoint refused connections. A log stream was opened from a container on every host, including Firezone and Home Assistant Supervisor.

[Server Compose](../../docker-compose/dozzle/docker-compose.yml) · [Agent Compose](../../docker-compose/dozzle-agent/docker-compose.yml) · [Home Assistant app](../../home-assistant-dozzle-agent/README.md) · [Operations](../operations.md) · [Application index](README.md)
