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

[Compose](../../docker-compose/ftp/docker-compose.yml) · [Setup](../configuration.md) · [Back to homelab](../../README.md)
