# ntfy

ntfy receives Uptime Kuma, Scrutiny, DIUN, and FBN notifications and delivers them to the ntfy mobile app.

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

The installed private environment uses separate non-admin publisher identities and two topics:

- `kuma-publisher` has write-only access and uses a dedicated access token from Uptime Kuma.
- `scrutiny-publisher` has write-only access and uses a separate token from Scrutiny.
- Each DIUN host has a separate write-only identity and token on the monitoring topic.
- `fbn-publisher` has a separate write-only token on a separate random FBN topic.
- `mobile-subscriber` has read-only access to both topics and uses one password in the mobile app.
- Anonymous access is denied, account signup is disabled, and attachment uploads are disabled.

Run [`generate-private.py`](../../configs/ntfy/generate-private.py) outside the repository to create the base Kuma, Scrutiny, and mobile inputs with mode 0600. [`add-diun-publishers.py`](../../configs/ntfy/add-diun-publishers.py) adds per-host DIUN identities on the monitoring topic. [`add-fbn-publisher.py`](../../configs/ntfy/add-fbn-publisher.py) creates the isolated FBN topic, its write-only identity, a private Apprise URL, and the additional mobile read ACL. The extension helpers preserve existing users, topics, and tokens and refuse duplicate identities. Never commit or paste private files into logs.

On September 12, 2026, the installed server was extended with the Scrutiny publisher. The resulting ACL inventory showed separate write-only Kuma and Scrutiny identities, the mobile account remained read-only, both publisher tokens were rotated after verification, and the Kuma and Scrutiny application-level notification tests succeeded.

Later that day, the server was extended with the isolated FBN topic without rotating or changing any existing auth entry. The stopped-state backup is `/opt/ntfy/backups/pre-fbn-publisher-20260912T181431Z`; both copied SQLite databases passed `quick_check`. After the same 2.28.0 image was recreated, direct and public health passed, all seven negative FBN/mobile ACL probes returned 403, mobile read both topics, FBN's application-level test was present only on its topic, and a fresh Kuma test still reached the monitoring topic.

The same-day DIUN extension added eight separate write-only publisher identities without changing the established Kuma, Scrutiny, FBN, or mobile credentials. Its verified stopped-state recovery archive is `/opt/backups/ntfy-diun-20260912T174749Z/ntfy-recovery.tar.gz`; both copied SQLite databases passed `quick_check`. Native DIUN tests from all eight hosts reached the mobile subscriber with the correct hostname, each DIUN token received HTTP 403 when used to read, and anonymous read/write remained denied.

`NTFY_UPSTREAM_BASE_URL=https://ntfy.sh` supports timely iOS push delivery. The upstream receives a poll request containing the message ID and a hash of the topic URL, not the alert body. The public `NTFY_BASE_URL` must match the server configured in the iOS app.

The message cache retains alerts for 72 hours so a temporarily offline phone can catch up. The cache and auth database are in `data/`; the mobile credential file is a separate private recovery item in `/opt/ntfy`.

On September 12, 2026, `latest` resolved to the same ntfy 2.28.0 image that was already running. The live service matched this policy and passed its direct and public health checks, topic ACL matrix, TLS validation, Cloudflare/NPM WebSocket subscription, and Kuma test-message readback. Changing the reference therefore caused no application or database migration. Future pulls may resolve to a newer image. This is a dated runtime observation, not a guarantee of future availability.

## Mobile setup

Read `/opt/ntfy/mobile-subscription.txt` locally on `rpimon`. In the ntfy app, add its server and sign in with the listed mobile account. Subscribe to the monitoring topic in that file and the FBN topic in `/opt/ntfy/fbn-private/mobile-subscription.txt`. Both subscriptions use the same mobile login. Do not use a publisher token on a phone.

## Verify and recover

Run these checks without printing the private environment:

```sh
cd /opt/ntfy
sudo docker compose config --quiet
sudo docker compose ps
curl --fail --silent --show-error http://rpimon:2586/v1/health
```

Then verify the public `/v1/health` endpoint over HTTPS and a WebSocket subscription through Cloudflare and NPM. For each topic, require anonymous read/write to fail, its intended publisher to write but not read, and the mobile account to read but not write. Send application-level tests from Kuma, Scrutiny, and FBN and read each through the mobile account.

Back up `data/`, `.env`, `mobile-subscription.txt`, `fbn-private/`, and all other restricted publisher output directories as one recovery set. Stop ntfy before replacing its SQLite files during a restore. Start the recorded pre-update image, check both databases with SQLite `quick_check`, then repeat the health, ACL, public-route, and application delivery tests.

Kuma and ntfy share `rpimon`. A host, Docker, LAN, power, NPM, or Cloudflare failure can therefore prevent the alert about that failure. Use an external dead-man check or move one side to another failure domain if loss-of-host alerting is required.

[Compose](../../docker-compose/ntfy/docker-compose.yml) · [Uptime Kuma](uptime-kuma.md) · [FBN](fbn.md) · [Official access-control documentation](https://docs.ntfy.sh/config/#access-control) · [Operations](../operations.md) · [Application index](README.md)
