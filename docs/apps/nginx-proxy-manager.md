# Nginx Proxy Manager

HTTPS entry point for the web apps. Each hostname forwards to a host and application port on the LAN.

[Homelab index](../../README.md) · [Architecture](../architecture.md) · [Inspection record](../inventory.md)

## Observed setup

Admin UI loaded in the in-app browser; direct HTTP on port 81 returned 200. TCP 443 accepted a connection. The UI displayed version 2.15.1 and nine configured proxy-host rows.

Host: `rpiproxy`. Definition: `/opt/nginx/docker-compose.yml`.

Source file: `docker-compose/npm/docker-compose.yml`.

| Service | Image/build recorded | Network / host ports | Restart |
| --- | --- | --- | --- |
| `app` | `jc21/nginx-proxy-manager:latest` | Compose network; `80:80, 443:443, 81:81, 51820:51820/udp` | `unless-stopped` |

| Service | Declared storage mapping |
| --- | --- |
| `app` | `./data:/data` |
| `app` | `./letsencrypt:/etc/letsencrypt` |

Relative bind sources resolve beside the Compose file. Named volumes are Docker-managed. Paths outside `/opt` are declarations read from Compose; their contents and mount status were not inspected.

## Recreate the setup

1. Create `/opt/nginx` with persistent `data/` and `letsencrypt/` directories. The inspected Compose file publishes HTTP 80, HTTPS 443, and admin 81.
2. Choose your own domain and LAN address reservations. Configure DNS and the upstream router separately; neither router forwarding nor authoritative DNS was inspected.
3. Create one Proxy Host per route in the table below. Use the destination host port, request the appropriate certificate, and set access policy explicitly.
4. Keep the administration interface on a trusted management network. Set forwarded headers and WebSocket behavior according to each app; those per-route switches were not inspected.

These are owner-run setup instructions; no deployment command was executed during documentation. Pin compatible versions and supply private values before starting a new instance.

## Data and recovery

Preserve `data/` and `letsencrypt/` together, including the configuration database and certificate state. Protect the archive as credential material. Restore the pair with a compatible NPM version before testing routes.

## Verification and troubleshooting

Compare an app’s direct LAN response with its proxied response. A refused backend port is a backend/listener problem; a working backend with a failing hostname points toward DNS, TLS, or proxy configuration. An HTTP 404 at the proxy IP is compatible with host-based routing.

## Deployment notes

The Compose file also publishes UDP 51820. No stream configuration or WireGuard handshake was inspected, so that mapping alone does not establish a VPN forwarding path. All nine rows showed Let’s Encrypt, Public, and Online; these are NPM configuration labels, not proof of backend health or Internet reachability.

Related: [Homarr](homarr.md), [Fail2ban](fail2ban.md), [Cloudflare integration](cloudflare.md).

## Configured routes

All destinations use HTTP behind the HTTPS hostname. Names are placeholders.

| Hostname | Backend |
| --- | --- |
| `anki.example.com` | `rpiblog:8080` |
| `boards.example.com` | `rpiblog:3001` |
| `firezone.example.com` | `vpn-edge:13000` |
| `home.example.com` | `rpiblog:7575` |
| `links.example.com` | `rpiblog:9090` |
| `pass.example.com` | `rpiblog:8089` |
| `plex.example.com` | `optiplex:32400` |
| `status.example.com` | `rpimon:3001` |
| `example.com`, `www.example.com` | `rpiblog:80` |

The Firezone backend refused the direct check. No current proxy row for the dashboard’s Home Assistant hostname appeared in the inspected table.
