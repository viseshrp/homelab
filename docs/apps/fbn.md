# FBN

Custom Facebook-group notification tool with browser-based acquisition, persistent session state, and a delivery queue.

[Homelab index](../../README.md) · [Architecture](../architecture.md) · [Inspection record](../inventory.md)

## Observed setup

Compose, Dockerfile, and setup README were read under `/opt/fbn-compose`. An older `/opt/fbn/venv` also exists. No browser session, group content, live scan, or notification was accessed.

Host: `rpiblog`. Definition: `/opt/fbn-compose/compose.yaml`.

| Service | Image/build recorded | Network / host ports | Restart |
| --- | --- | --- | --- |
| `fbn` | `fbn:local` | Compose network; no host mapping declared | `no` |
| `bootstrap` | `fbn:local` | Compose network; no host mapping declared | `no` |

| Service | Persistent application-data mapping |
| --- | --- |
| `fbn` | `fbn-data:/home/fbn/.local/share/fbn` |
| `bootstrap` | `fbn-data:/home/fbn/.local/share/fbn` |

Relative bind sources resolve beside the Compose file. Named volumes are Docker-managed. Paths outside `/opt` are declarations read from Compose; their contents and mount status were not inspected.

## Recreate the setup

1. Build the local image from the FBN checkout. Its Dockerfile uses Ubuntu 24.04, Playwright 1.61.0 with Chromium, and a non-root runtime user.
2. Provide the private group configuration, notification URL, authentication-file reference, and dedicated persistent data volume. Keep authentication exports outside source control.
3. The one-shot `bootstrap` service must exit successfully before the `fbn` monitor starts. Both share persistent application data; the setup README describes a private authentication mount for bootstrap.
4. Keep the same browser/profile combination for later checks. The monitor has a 1 GiB shared-memory allocation and an explicit `restart: no` policy so account-action failures need owner recovery.

These are owner-run setup instructions; no deployment command was executed during documentation. Pin compatible versions and supply private values before starting a new instance.

## Data and recovery

Preserve the SQLite state and dedicated browser profile securely with the application stopped. The profile is authentication material. Preserve pending-delivery state to avoid silently losing work during recovery.

## Verification and troubleshooting

A running container or successful import does not prove that Facebook acquisition works. The Dockerfile’s health check imports the package only. Distinguish browser readiness, authenticated group access, scan success, and delivery success.

## Deployment notes

The inspected README describes baseline-first behavior and persistent pending notifications with at-least-once delivery. It also describes a user-systemd alternative; no timer outside `/opt` was inspected, so no schedule is claimed here.

## Private deployment inputs

| Input | Purpose |
| --- | --- |
| `FBN_GROUP` | Group identifier selected by the owner |
| `FBN_APPRISE_URL` | Private notification destination |
| `FBN_AUTH_FILE` | External authentication export used by bootstrap |
| `FBN_DATA_VOLUME` | External persistent volume selected by the setup README |
| `FBN_TIMEZONE`, `FBN_EVERY`, `FBN_TO` | Timestamp interpretation and monitoring interval bounds |
| `FBN_UID`, `FBN_GID` | Non-root container ownership |

The inspected README requires creating the external volume before Compose starts it. Bootstrap’s private authentication-file bind is intentionally omitted from the table above. The monitor uses the initialized profile; authentication material is not a public setup artifact.
