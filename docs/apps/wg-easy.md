# WG-Easy

WG-Easy combines a WireGuard server with a web interface for managing VPN peers.

## My setup

The project is `/opt/wg-easy` on `vpn-edge`, using `weejewel/wg-easy`. The project directory is mounted at `/etc/wireguard` to retain server and peer configuration.

Private environment settings provide the endpoint hostname and management password. Client DNS is set through `WG_DEFAULT_DNS`.

## Networking

The container publishes UDP 51820 for WireGuard and TCP 51821 for administration. It has `NET_ADMIN` and `SYS_MODULE`, with IP forwarding and source-valid-mark sysctls enabled.

Firezone's configuration on the same host also binds UDP 51820. Only one can use that host port at a time. WG-Easy uses an `unless-stopped` restart policy.

[Compose](../../docker-compose/wg-easy/docker-compose.yml) · [Setup](../configuration.md) · [Back to homelab](../../README.md)
