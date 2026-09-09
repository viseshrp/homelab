# Gluetun

Gluetun provides the VPN network connection for qBittorrent.

## My setup

Gluetun is part of `/opt/qbit` on `optiplex`, using `qmcgaw/gluetun`. Its provider settings select AirVPN and WireGuard.

The container has the `NET_ADMIN` capability and access to `/dev/net/tun`. WireGuard keys and assigned addresses are private environment settings. `/opt/qbit/gluetun-data` is mounted at `/gluetun`.

## Shared networking

qBittorrent uses `network_mode: service:gluetun`, so Gluetun owns the network namespace and publishes its ports:

| Host port | Purpose |
| --- | --- |
| 8085/TCP | qBittorrent web interface |
| 6881/TCP and UDP | Torrent traffic |

This connection is for the download client's outbound traffic. The Firezone and WG-Easy projects provide separate remote-access VPN configurations.

[Back to homelab](../../README.md)
