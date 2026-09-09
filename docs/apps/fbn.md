# FBN

FBN watches recent posts in a Facebook group and sends notifications through Apprise. It uses Chromium with a dedicated browser profile and stores scan and delivery state in SQLite.

## My setup

The Compose project lives at `/opt/fbn-compose` on `rpiblog`. Its local image uses Ubuntu 24.04 and Playwright 1.61.0 with Chromium. The application runs as a non-root user with 1 GiB of shared memory for the browser.

Two services share the application-data volume:

| Service | Job |
| --- | --- |
| `bootstrap` | Initializes the browser profile from a private authentication export |
| `fbn` | Starts monitoring after bootstrap completes successfully |

The monitor uses `restart: no`, allowing account-action failures to stop it until the session is recovered.

## Configuration and state

Private settings select the group, Apprise destination, authentication file, timezone, and interval bounds. `FBN_DATA_VOLUME` selects the external data volume, mounted at `/home/fbn/.local/share/fbn`.

The first successful scan establishes a baseline by default. New posts enter a persistent delivery queue. Pending notifications survive a restart; a retry can produce a duplicate if a send succeeded before its completion was recorded.

[Back to homelab](../../README.md)
