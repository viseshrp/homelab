# FTP server

The FTP project provides access to a media-download directory through an FTP account.

## My setup

The Compose project lives at `/opt/ftp` on `rpinfs` and uses `garethflowers/ftp-server`.

The host directory `/mnt/media/Media/downloads` is mounted as the FTP user's home directory. The account name and password are private environment settings.

## Ports

| TCP ports | Purpose |
| --- | --- |
| 20–21 | FTP control and data connections |
| 40000–40009 | Passive data connections |

The container has an automatic restart policy. The FTP project and its account configuration are stored separately from the files on the media mount.

## Verify and recover

Start with a login and directory listing, then verify a controlled transfer when writes are intended. A listening control port does not prove passive data connections work through the firewall.

Back up the media directory independently from the Compose file and private account settings. After a restore, confirm ownership, the user's home mapping, and the entire passive port range.

[Compose](../../docker-compose/ftp/docker-compose.yml) · [Operations](../operations.md) · [Application index](README.md)
