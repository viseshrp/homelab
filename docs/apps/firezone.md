# Firezone

Firezone provides a WireGuard-based remote-access VPN with a web management interface.

## My setup

The project lives at `/opt/firezone` on `vpn-edge`. It pairs `firezone/firezone` with PostgreSQL 15 on a dedicated IPv4/IPv6 bridge network.

The configuration enables IP forwarding and grants `NET_ADMIN` and `SYS_MODULE`. Nginx Proxy Manager's `firezone` route points to the management interface on port 13000.

## Ports and data

| Mapping | Purpose |
| --- | --- |
| 13000/TCP | Management interface |
| 51820/UDP | WireGuard |
| `firezone/` → `/var/firezone` | Firezone state |
| `postgres-data` → `/var/lib/postgresql/data` | Database volume |

A private environment file supplies application and database settings. WG-Easy is also configured on this host with UDP 51820, so the two default port bindings cannot run together unchanged.

[Back to homelab](../../README.md)
