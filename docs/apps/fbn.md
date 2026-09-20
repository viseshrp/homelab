# FBN

FBN watches recent posts in a Facebook group and sends notifications to the private ntfy server through Apprise. It uses Chromium with a dedicated browser profile and stores scan and delivery state in SQLite.

## My setup

The Compose project lives at `/opt/fbn-compose` on `rpiblog`. `COMPOSE_FILE=docker-compose.yml` makes the homelab-managed file authoritative even though the source checkout also contains its own `compose.yaml`. Its local image uses Ubuntu 24.04 and Playwright 1.61.0 with Chromium. The application runs as a non-root user with 1 GiB of shared memory for the browser.

Two services share the application-data volume:

| Service | Job |
| --- | --- |
| `bootstrap` | Initializes the browser profile from a private authentication export |
| `fbn` | Starts monitoring after bootstrap completes successfully |

The monitor uses `restart: no`, allowing account-action failures to stop it until the session is recovered.

## Configuration and state

Private settings select the group, Apprise destination, authentication file, timezone, and interval bounds. `FBN_DATA_VOLUME` selects the external data volume, mounted at `/home/fbn/.local/share/fbn`.

FBN has its own random ntfy topic and `fbn-publisher` identity. Its access token grants write-only access to that topic; it cannot read any topic or publish to the monitoring topic. The existing `mobile-subscriber` has read-only access to both topics. The private `FBN_APPRISE_URL` has this shape:

```dotenv
FBN_APPRISE_URL=ntfys://tk_REPLACE_WITH_29_RANDOM_CHARACTERS@ntfy.example.com/replace_with_random_fbn_topic?auth=token
```

Create the identity and private FBN input with [`add-fbn-publisher.py`](../../configs/ntfy/add-fbn-publisher.py). Run it against a mode-0600 copy of the installed ntfy environment after creating a consistent ntfy backup:

```sh
python3 configs/ntfy/add-fbn-publisher.py \
  --env-file PRIVATE_WORKING_DIRECTORY/.env \
  --output-dir PRIVATE_WORKING_DIRECTORY/fbn-private
```

Install the updated ntfy environment and `fbn-private/fbn-ntfy.env` with mode 0600. Replace only `FBN_APPRISE_URL` in FBN's private `.env`, recreate the ntfy and FBN containers without rebuilding either image, and retain the old files until verification passes. The helper creates a separate topic and refuses to overwrite an existing output directory, duplicate `fbn-publisher`, or reuse an existing topic.

The first successful scan establishes a baseline by default. New posts enter a persistent delivery queue. Pending notifications survive a restart; a retry can produce a duplicate if a send succeeded before its completion was recorded.

On September 12, 2026, the installed destination was changed from `ntfy.sh` to the private server without changing the FBN image or data volume. ntfy received a separate FBN topic, write-only publisher token, and mobile read ACL. A stopped-state FBN backup was saved under `/opt/fbn-compose/backups/pre-private-ntfy-20260912T181540Z`; SQLite integrity and foreign keys passed before restart. The installed `AppriseSink` delivered a test that the mobile account read through the public route, and the message was absent from the monitoring topic. The final recreate activated the homelab-managed Compose file after its runtime model matched the source file. FBN resumed healthy with zero restarts, 59 stored posts, 40 delivered outbox rows, no pending delivery, no consecutive failures, and no recent error lines.

## Verify and recover

Check the most recent scan result and the delivery outcome, not only the container state. Test one harmless Apprise notification through FBN's installed image, then read the same message as `mobile-subscriber`. Require anonymous read/write to fail, FBN publish to succeed, FBN read to fail, mobile read to succeed, and mobile publish to fail. `restart: no` is deliberate: an account-action error stops the monitor so it does not loop against a broken session.

Back up the external data volume consistently with the source version and private configuration. A restore test should load the browser profile, open the saved SQLite state, retain pending deliveries, and complete a scan without resetting the baseline.

[Compose](../../docker-compose/fbn/docker-compose.yml) · [Apprise ntfy syntax](https://appriseit.com/services/ntfy/) · [ntfy access control](https://docs.ntfy.sh/config/#access-control) · [Operations](../operations.md) · [Application index](README.md)
