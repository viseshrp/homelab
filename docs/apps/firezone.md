# Firezone

LAN-access VPN stack definition with PostgreSQL and a separately proxied management endpoint.

[Homelab index](../../README.md) · [Architecture](../architecture.md) · [Inspection record](../inventory.md)

## Observed setup

The browser’s Firezone destination led to a seventh SSH-accessible host, named `vpn-edge` only in these docs. Its management port 13000 refused the connection.

Host: `vpn-edge`. Definition: `/opt/firezone/docker-compose.yml`.

Source file: `docker-compose/firezone/docker-compose.yml`.

| Service | Image/build recorded | Network / host ports | Restart |
| --- | --- | --- | --- |
| `firezone` | `firezone/firezone:latest` | Compose network; `51820:51820/udp, 13000:13000` | `not specified` |
| `postgres` | `postgres:15` | Compose network; no host mapping declared | `not specified` |

| Service | Declared storage mapping |
| --- | --- |
| `firezone` | `${FZ_INSTALL_DIR:-.}/firezone:/var/firezone` |
| `postgres` | `postgres-data:/var/lib/postgresql/data` |

Relative bind sources resolve beside the Compose file. Named volumes are Docker-managed. Paths outside `/opt` are declarations read from Compose; their contents and mount status were not inspected.

## Recreate the setup

1. Keep the Firezone state under `/opt/firezone/firezone` and provide a private environment file.
2. The inspected definition has Firezone plus PostgreSQL 15, a dedicated bridge network with IPv4/IPv6 addressing, IP forwarding, and network/module capabilities.
3. Its management mapping is 13000/TCP and its VPN mapping is 51820/UDP. NPM currently defines a Firezone route to the management port.
4. Choose one intended owner for UDP 51820 before starting this alongside WG-Easy. Verify the exact Firezone generation and configuration rather than assuming a current release accepts this older deployment shape.

These are owner-run setup instructions; no deployment command was executed during documentation. Pin compatible versions and supply private values before starting a new instance.

## Data and recovery

Preserve Firezone state, PostgreSQL consistently, and private environment credentials as a matched recovery set. Keep network addressing and client enrollment records private.

## Verification and troubleshooting

The management listener refused connections even though NPM labeled the route Online. This is a direct example of configured proxy status differing from a backend response. A UDP handshake was not attempted.

## Deployment notes

Both Firezone and WG-Easy definitions on this host bind the same default host UDP port. Their simultaneous default deployment would conflict. No running-container state was read; neither is declared operational.

Related: [WG-Easy](wg-easy.md), [PostgreSQL](postgresql.md).
