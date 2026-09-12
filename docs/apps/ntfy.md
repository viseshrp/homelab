# ntfy

ntfy receives Uptime Kuma alerts and delivers them to the ntfy mobile app.

## Deployment

| Item | Value |
| --- | --- |
| Host | `rpimon` |
| Project directory | `/opt/ntfy` |
| Compose project | [`docker-compose/ntfy`](../../docker-compose/ntfy/docker-compose.yml) |
| Image | `binwiederhier/ntfy:latest` |
| LAN backend | `rpimon:2586` |
| Public route | `https://ntfy.<domain>` through NPM and Cloudflare |
| Persistent state | `/opt/ntfy/data` |

The container runs as UID/GID 1000, listens on unprivileged container port 8080, and publishes port 2586 only on `rpimon`'s private LAN address. NPM terminates TLS and forwards WebSockets with buffering disabled and three-minute proxy timeouts. The `latest` image includes ARM64 support. Because the tag moves, record its resolved digest and current application version before every pull.

## Authentication and delivery

The installed private environment declares three non-admin users and one topic:

- `kuma-publisher` has write-only access and uses a dedicated access token from Uptime Kuma.
- `scrutiny-publisher` has write-only access and uses a separate token from Scrutiny.
- `mobile-subscriber` has read-only access and uses a separate password in the mobile app.
- Anonymous access is denied, account signup is disabled, and attachment uploads are disabled.

Run [`generate-private.py`](../../configs/ntfy/generate-private.py) outside the repository to create `.env`, `mobile-subscription.txt`, `kuma-ntfy.env`, and `scrutiny-ntfy.env` with mode 0600. It generates a random topic, independent credentials, cost-12 bcrypt password hashes, and separate Kuma and Scrutiny tokens without printing them. [`add-scrutiny-publisher.py`](../../configs/ntfy/add-scrutiny-publisher.py) adds the Scrutiny identity to an existing installation without rotating the established topic or credentials. Never commit or paste private files into logs.

On September 12, 2026, the installed server was extended with the Scrutiny publisher. The resulting ACL inventory showed separate write-only Kuma and Scrutiny identities, the mobile account remained read-only, both publisher tokens were rotated after verification, and the Kuma and Scrutiny application-level notification tests succeeded.

`NTFY_UPSTREAM_BASE_URL=https://ntfy.sh` supports timely iOS push delivery. The upstream receives a poll request containing the message ID and a hash of the topic URL, not the alert body. The public `NTFY_BASE_URL` must match the server configured in the iOS app.

The message cache retains alerts for 72 hours so a temporarily offline phone can catch up. The cache and auth database are in `data/`; the mobile credential file is a separate private recovery item in `/opt/ntfy`.

On September 12, 2026, `latest` resolved to the same ntfy 2.28.0 image that was already running. The live service matched this policy and passed its direct and public health checks, topic ACL matrix, TLS validation, Cloudflare/NPM WebSocket subscription, and Kuma test-message readback. Changing the reference therefore caused no application or database migration. Future pulls may resolve to a newer image. This is a dated runtime observation, not a guarantee of future availability.

## Mobile setup

Read `/opt/ntfy/mobile-subscription.txt` locally on `rpimon`. In the ntfy app, add its server, sign in with the listed mobile account, then subscribe to the listed topic. Do not use the Kuma publisher token on a phone.

## Verify and recover

Run these checks without printing the private environment:

```sh
cd /opt/ntfy
sudo docker compose config --quiet
sudo docker compose ps
curl --fail --silent --show-error http://rpimon:2586/v1/health
```

Then verify the public `/v1/health` endpoint over HTTPS, a WebSocket subscription through Cloudflare and NPM, and all four ACL outcomes: anonymous read/write denied, Kuma publish allowed/read denied, and mobile read allowed/write denied. Send a Kuma test notification and confirm that the same message is readable through the mobile account.

Back up `data/`, `.env`, and `mobile-subscription.txt` as one restricted recovery set. Stop ntfy before replacing its SQLite files during a restore. Start the recorded pre-update image, check both databases with SQLite `quick_check`, then repeat the health, ACL, public-route, and Kuma delivery tests.

Kuma and ntfy share `rpimon`. A host, Docker, LAN, power, NPM, or Cloudflare failure can therefore prevent the alert about that failure. Use an external dead-man check or move one side to another failure domain if loss-of-host alerting is required.

[Compose](../../docker-compose/ntfy/docker-compose.yml) · [Uptime Kuma](uptime-kuma.md) · [Operations](../operations.md) · [Application index](README.md)
