# Anki sync server

Hosts a private Anki synchronization endpoint behind its own HTTPS name.

[Homelab index](../../README.md) · [Architecture](../architecture.md) · [Inspection record](../inventory.md)

## Observed setup

Port 8080 accepted TCP and returned HTTP 404 at `/`. NPM routes `anki.example.com` to this port. An authenticated synchronization was not attempted.

Host: `rpiblog`. Definition: `/opt/anki/docker-compose.yml`.

| Service | Image/build recorded | Network / host ports | Restart |
| --- | --- | --- | --- |
| `anki` | `ghcr.io/luckyturtledev/anki` | Compose network; `8080:8080` | `unless-stopped` |

| Service | Declared storage mapping |
| --- | --- |
| `anki` | `./data:/data` |

Relative bind sources resolve beside the Compose file. Named volumes are Docker-managed. Paths outside `/opt` are declarations read from Compose; their contents and mount status were not inspected.

## Recreate the setup

1. Use the observed `ghcr.io/luckyturtledev/anki` image and persist `/opt/anki/data` at container `/data`.
2. Provide `SYNC_USER1` privately and configure `SYNC_HOST`, `SYNC_PORT`, and the public base URL for your chosen deployment.
3. Publish host port 8080 and configure the Anki HTTPS proxy route.
4. Set the custom sync endpoint in each compatible client and test with a disposable collection before using personal decks.

These are owner-run setup instructions; no deployment command was executed during documentation. Pin compatible versions and supply private values before starting a new instance.

## Data and recovery

Preserve the complete data directory with writes quiesced and keep credentials separately. Verify collection and media synchronization after a restore.

## Verification and troubleshooting

An HTTP 404 at the root establishes an HTTP responder, not a broken sync API. Test the client’s actual sync route and credentials. No collection contents were opened.

## Deployment notes

The observed container is configured with user `0:0`. Image and mount details come from `/opt/anki/docker-compose.yml`.
