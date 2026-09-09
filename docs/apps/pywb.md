# pywb

pywb replays archived web pages from WARC files. It provides the replay interface for the ArchiveBox stack.

## My setup

The `webrecorder/pywb` container is part of `/opt/archivebox` on `rpimon`. Host port 8082 maps to container port 8080.

| Host path | Container path |
| --- | --- |
| `/opt/archivebox/data` | `/archivebox` |
| `/opt/archivebox/data/wayback` | `/webarchive` |

## Startup

The entrypoint creates a `default` collection, adds captures matching `/archivebox/archive/*/warc/*.warc.gz`, and starts `wayback`.

ArchiveBox supplies the captures. The replay collection and its indexes persist in the shared data directory.

[Compose](../../docker-compose/archivebox/docker-compose.yml) · [Setup](../configuration.md) · [Back to homelab](../../README.md)
