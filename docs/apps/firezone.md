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

A private environment file supplies application and database settings. Firezone retains UDP 51820 while WG-Easy publishes its internal WireGuard listener on host UDP 51822, allowing both projects to run together. NPM keeps separate UDP streams for Firezone on 51820 and WG-Easy on 51822. Firezone's database-managed default client DNS uses the private Pi-hole LAN address; keep the literal address on the host and re-download client configurations after changing it.

## Verify and recover

Check the management page through `vpn-edge:13000` and the proxied website hostname, then verify a client handshake through the DNS-only VPN hostname and NPM UDP 51820 stream. From a client using a freshly downloaded configuration, resolve a public name through Pi-hole and reach an intended private resource. HTTP 200 from the management page does not prove that the WireGuard data path or client DNS works.

Recover `firezone/`, the PostgreSQL data, and the complete private environment as one version-compatible set. Preserve salts, keys, database credentials, and the external URL. Verify Firezone still owns UDP 51820 after starting or recreating WG-Easy.

[Compose](../../docker-compose/firezone/docker-compose.yml) · [Operations](../operations.md) · [Application index](README.md)
