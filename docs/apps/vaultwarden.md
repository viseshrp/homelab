# Vaultwarden

Vaultwarden hosts a password vault for Bitwarden-compatible clients.

## My setup

Vaultwarden runs on `rpiblog` from `/opt/vw`, using `vaultwarden/server`. Its web interface is published on host port 8089 and reached through the `pass` HTTPS hostname.

New account signups are disabled. SMTP settings provide email delivery, and the domain setting identifies the public vault URL. These values are kept in private configuration.

## Storage and networking

`/opt/vw/vw-data` is mounted at `/data`, keeping the database, attachments, and other vault state together.

The Compose file also publishes port 3012 and enables its WebSocket setting. The main proxy route forwards to port 8089. The container restarts automatically.

[Compose](../../docker-compose/vaultwarden/docker-compose.yml) · [Setup](../configuration.md) · [Back to homelab](../../README.md)
