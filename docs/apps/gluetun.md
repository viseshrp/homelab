# Gluetun

VPN network container for qBittorrent’s outbound traffic.

[Homelab index](../../README.md) · [Architecture](../architecture.md) · [Inspection record](../inventory.md)

## Observed setup

Compose selects AirVPN over WireGuard and attaches qBittorrent to this service’s network namespace. No handshake, egress address, or leak test was performed.

Host: `optiplex`. Definition: `/opt/qbit/docker-compose.yml`.

| Service | Image/build recorded | Network / host ports | Restart |
| --- | --- | --- | --- |
| `gluetun` | `qmcgaw/gluetun` | Compose network; `6881:6881, 6881:6881/udp, 8085:8085` | `unless-stopped` |

| Service | Declared storage mapping |
| --- | --- |
| `gluetun` | `./gluetun-data:/gluetun` |

Relative bind sources resolve beside the Compose file. Named volumes are Docker-managed. Paths outside `/opt` are declarations read from Compose; their contents and mount status were not inspected.

## Recreate the setup

1. Create `/opt/qbit/gluetun-data` and mount it at `/gluetun`.
2. Provide WireGuard private key, preshared key, and assigned addresses through private configuration. They are intentionally absent from this documentation.
3. Grant the configured `NET_ADMIN` capability and TUN device. Gluetun publishes 8085/TCP and 6881/TCP+UDP for the shared namespace.
4. Validate DNS, tunnel establishment, and behavior during tunnel loss from the consuming workload before relying on VPN-only egress.

These are owner-run setup instructions; no deployment command was executed during documentation. Pin compatible versions and supply private values before starting a new instance.

## Data and recovery

Protect VPN credentials and the Gluetun state directory. Restore provider configuration separately from qBittorrent’s client state.

## Verification and troubleshooting

Check provider configuration, device access, and network namespace coupling. A Docker host port does not imply the VPN provider forwards that port. No runtime firewall behavior was inspected.

## Deployment notes

This outbound application VPN is separate from the LAN-access VPN definitions on `vpn-edge`. The diagram shows the configured dependency, not a verified encrypted session.

Related: [qBittorrent](qbittorrent.md).
