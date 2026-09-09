# Pi-hole

LAN DNS filtering service with a web administration interface.

[Homelab index](../../README.md) · [Architecture](../architecture.md) · [Inspection record](../inventory.md)

## Observed setup

SSH succeeded, TCP DNS port 53 accepted a connection, and the web root returned HTTP 403. No DNS query, DHCP lease, client list, or query log was inspected.

Host: `rpihole`. Definition: `/opt/pihole-docker/docker-compose.yml`.

Source file: `docker-compose/pihole/docker-compose.yml`.

| Service | Image/build recorded | Network / host ports | Restart |
| --- | --- | --- | --- |
| `pihole` | `pihole/pihole:latest` | host; no host mapping declared | `always` |

| Service | Declared storage mapping |
| --- | --- |
| `pihole` | `./etc-pihole:/etc/pihole` |
| `pihole` | `./etc-dnsmasq.d:/etc/dnsmasq.d` |

Relative bind sources resolve beside the Compose file. Named volumes are Docker-managed. Paths outside `/opt` are declarations read from Compose; their contents and mount status were not inspected.

## Recreate the setup

1. Use `/opt/pihole-docker` with persistent `etc-pihole` and `etc-dnsmasq.d` directories.
2. The observed container uses host networking and `NET_ADMIN`. Check host-port conflicts before starting the DNS service.
3. Set a private admin credential and configure clients or the router to use the intended DNS address. Client DNS assignment was not verified here.
4. Use the dashboard’s `/admin` link for management. Validate DNS resolution and filtering separately from the web UI.

These are owner-run setup instructions; no deployment command was executed during documentation. Pin compatible versions and supply private values before starting a new instance.

## Data and recovery

Preserve DNS/filter configuration and private settings. Query history can reveal household browsing behavior; exclude it from public exports.

## Verification and troubleshooting

A TCP connection on 53 does not prove DNS answers over UDP or TCP. The homepage’s zero-valued widget is not a substitute for a DNS query test. A root-path 403 does not establish whether `/admin` is healthy.

## Deployment notes

The inspected Compose definition uses a floating image tag. Router DHCP and local DNS records were outside the inspected scope.
