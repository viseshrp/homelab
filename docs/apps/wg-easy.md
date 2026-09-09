# WG-Easy

WG-Easy combines a WireGuard server with a web interface for managing VPN peers.

## My setup

The project is `/opt/wg-easy` on `vpn-edge`, using `weejewel/wg-easy`. The project directory is mounted at `/etc/wireguard` to retain server and peer configuration.

Private environment settings provide the endpoint hostname and management password. Client DNS is set through `WG_DEFAULT_DNS`.

## Networking

The container publishes UDP 51820 for WireGuard and TCP 51821 for administration. It has `NET_ADMIN` and `SYS_MODULE`, with IP forwarding and source-valid-mark sysctls enabled.

Firezone's configuration on the same host also binds UDP 51820. Only one can use that host port at a time. WG-Easy uses an `unless-stopped` restart policy.

## Verify and recover

Check the port 51821 administration interface, then verify a client handshake, assigned DNS, and access to an intended private resource. A running UI does not prove UDP 51820 is reachable or that forwarding works.

The project directory contains WireGuard private keys and peer state. Back it up with restricted access and retain the private environment. Confirm Firezone is not using UDP 51820 before starting WG-Easy.

[Compose](../../docker-compose/wg-easy/docker-compose.yml) · [Operations](../operations.md) · [Application index](README.md)
