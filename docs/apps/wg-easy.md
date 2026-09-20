# WG-Easy

WG-Easy combines a WireGuard server with a web interface for managing VPN peers.

## My setup

The project is `/opt/wg-easy` on `vpn-edge`, intentionally using the moving `ghcr.io/wg-easy/wg-easy:15` tag so a pull retrieves the current v15 release. The registry's literal `latest` tag still points to the incompatible legacy v14 line. The project directory is mounted at `/etc/wireguard`; v15 stores application, server, and peer state in `wg-easy.db` and regenerates the live `wg0.conf`. The original v7 `wg0.json` and `wg0.conf` are retained in the restricted, verified migration backup rather than used as active state.

The private environment controls the image, published ports, LAN-only insecure HTTP mode, and dedicated Docker network. WG-Easy stores the endpoint hostname, public UDP port, administrator authentication, client DNS, and peer settings in its database. Do not put the administrator password in Compose or `.env` after setup.

## Networking

The container listens on UDP 51820 internally and publishes it as configurable host port `WG_UDP_HOST_PORT`, which defaults to UDP 51822. Configurable host TCP port `WG_UI_HOST_PORT` defaults to 51821 for the LAN administration interface. The container has `NET_ADMIN` and `SYS_MODULE`, the host module tree as a read-only mount, IPv4/IPv6 forwarding, and a dedicated dual-stack Docker network.

Firezone retains UDP 51820 on the same host. The separate WG-Easy host port allows both projects to run at once. The router forwards public UDP 51822 to `rpiproxy:51822`, and Nginx Proxy Manager forwards that UDP stream to `vpn-edge:51822`. WG-Easy advertises public port 51822. Its VPN endpoint uses a DNS-only Cloudflare hostname, while its separate website hostname is proxied through Cloudflare and NPM to TCP 51821. WG-Easy uses an `unless-stopped` restart policy.

WG-Easy advertises only the private Pi-hole LAN address as client DNS, with no public secondary resolver. Its default client routes are `0.0.0.0/0` and `::/0`, so IPv4 and IPv6 traffic use the VPN. Keep any per-client DNS override aligned with the same Pi-hole address and regenerate client profiles after a DNS-policy change.

## Verify and recover

Check the direct port 51821 administration interface, the proxied website hostname, direct host ownership of UDP 51822, and the NPM UDP 51822 stream. Then verify a client handshake, Pi-hole resolution from the refreshed profile, and access to an intended private resource. A running UI does not prove the router-to-NPM-to-WG-Easy UDP path or client DNS works.

The project directory contains the SQLite database, generated WireGuard configuration, private keys, and migrated peer state. Back up the complete directory with restricted access and validate SQLite before an upgrade; retain the verified pre-v15 migration archive as a separate rollback unit. Before changing the database-managed endpoint hostname or port, preserve the existing peer configurations and plan to update or regenerate clients with the new endpoint.


[Compose](../../docker-compose/wg-easy/docker-compose.yml) · [Operations](../operations.md) · [Application index](README.md)
