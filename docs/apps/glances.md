# Glances

Glances displays host resource usage in a browser or terminal client.

## Compose setup

The local Docker setup builds from `nicolargo/glances` and supplies a custom `glances.conf`. It uses host networking, the host PID namespace, privileged mode, and a read-only Docker socket mount.

The web interface uses port 61208.

## Terminal server

A separate service configuration starts Glances from `/opt/glances/venv`:

```sh
/opt/glances/venv/bin/glances -s --disable-webui --disable-history
```

The terminal kiosk script connects Glances clients to server port 61209. The browser kiosk opens the web interface instead.

[Back to homelab](../../README.md)
