# FTP server

File-transfer definition exposing a media-download directory through FTP.

[Homelab index](../../README.md) · [Architecture](../architecture.md) · [Inspection record](../inventory.md)

## Observed setup

SSH and `/opt/ftp` inspection succeeded. FTP control port 21 refused the connection. NFS exports and storage mounts were outside scope.

Host: `rpinfs`. Definition: `/opt/ftp/docker-compose.yml`.

| Service | Image/build recorded | Network / host ports | Restart |
| --- | --- | --- | --- |
| `ftp-server` | `garethflowers/ftp-server` | Compose network; `20-21:20-21/tcp, 40000-40009:40000-40009/tcp` | `always` |

| Service | Declared storage mapping |
| --- | --- |
| `ftp-server` | `/mnt/media/Media/downloads:/home/ftp-user` |

Relative bind sources resolve beside the Compose file. Named volumes are Docker-managed. Paths outside `/opt` are declarations read from Compose; their contents and mount status were not inspected.

## Recreate the setup

1. Use the observed `garethflowers/ftp-server` image and supply a private FTP username/password.
2. Map the intended download tree into the FTP user’s home directory. The host source is outside `/opt` and was not opened.
3. The Compose file publishes TCP 20–21 and passive ports 40000–40009. Account for both control and data paths when configuring a private deployment.
4. Confirm transport security and access policy before use. No TLS configuration or functioning FTP session was established by this inspection.

These are owner-run setup instructions; no deployment command was executed during documentation. Pin compatible versions and supply private values before starting a new instance.

## Data and recovery

Protect the account configuration and back up the source download data independently. The Compose directory contains a mount declaration, not the mounted media.

## Verification and troubleshooting

A refused control port prevents an FTP session regardless of passive-port configuration. Establish a running listener first. The host name `rpinfs` does not prove NFS is configured.

## Deployment notes

The documented container destination uses `/home/ftp-user` as a placeholder for the private account name.
