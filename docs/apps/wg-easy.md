# WG-Easy

Alternative WireGuard server definition with a browser-based management port.

[Homelab index](../../README.md) · [Architecture](../architecture.md) · [Inspection record](../inventory.md)

## Observed setup

`/opt/wg-easy` and its Compose file were inspected. TCP 51821 refused the connection. UDP WireGuard operation was not tested.

Host: `vpn-edge`. Definition: `/opt/wg-easy/docker-compose.yml`.

Source file: `docker-compose/wg-easy/docker-compose.yml`.

| Service | Image/build recorded | Network / host ports | Restart |
| --- | --- | --- | --- |
| `wg-easy` | `weejewel/wg-easy:latest` | Compose network; `51820:51820/udp, 51821:51821/tcp` | `unless-stopped` |

| Service | Declared storage mapping |
| --- | --- |
| `wg-easy` | `.:/etc/wireguard` |

Relative bind sources resolve beside the Compose file. Named volumes are Docker-managed. Paths outside `/opt` are declarations read from Compose; their contents and mount status were not inspected.

## Recreate the setup

1. Keep the Compose project in `/opt/wg-easy`; its current-directory bind supplies `/etc/wireguard`.
2. Provide the private endpoint hostname and management password. The observed image is the older `weejewel/wg-easy` family.
3. Configure UDP 51820, TCP management 51821, network/module capabilities, and the listed forwarding sysctls.
4. Choose the intended LAN DNS server for clients and validate access from a real peer. The DNS address in the inspected file differs from the current Pi-hole inventory address.

These are owner-run setup instructions; no deployment command was executed during documentation. Pin compatible versions and supply private values before starting a new instance.

## Data and recovery

Preserve the WireGuard configuration and peer keys securely. Restore with a compatible image and protect the management interface before bringing peers back.

## Verification and troubleshooting

Check the management listener separately from UDP handshakes. Resolve the UDP 51820 conflict with the Firezone definition before attempting to run both unchanged.

## Deployment notes

The stale DNS reference is documented as a mismatch without publishing its address. The host is distinct from the `rpivpn` alias, whose SSH address timed out.

Related: [Firezone](firezone.md), [Pi-hole](pihole.md).
