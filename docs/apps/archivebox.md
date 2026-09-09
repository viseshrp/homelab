# ArchiveBox

ArchiveBox saves local copies of web pages. The accompanying pywb service replays captures stored in WARC format.

## My setup

The project lives at `/opt/archivebox` on `rpimon`. ArchiveBox uses the `archivebox/archivebox` image, with `dev` as the Compose default tag, and publishes host port 8002 to container port 8000.

The public index, snapshots, and add view are disabled. SSL checking is enabled. Capture settings use a 120-second timeout and a media-size limit of `1500m`.

## Archive and replay

`/opt/archivebox/data` is mounted at `/data` in ArchiveBox. [pywb](pywb.md) mounts that same directory at `/archivebox` and its `wayback/` subdirectory at `/webarchive`.

pywb publishes a separate interface on port 8082. Its startup command indexes WARC files from the ArchiveBox capture tree into the `default` collection before starting the replay server.

## Verify and recover

Verify two outcomes separately: ArchiveBox can create a new capture, and pywb can replay an existing WARC. A working ArchiveBox page does not prove that browser capture dependencies or replay indexes work.

The shared `data/` tree is the recovery unit. Preserve snapshots, WARC files, ArchiveBox state, and the pywb collection/index data together. After a restore, compare capture counts and open representative archived assets rather than checking only the index page.

[Compose](../../docker-compose/archivebox/docker-compose.yml) · [Operations](../operations.md) · [Application index](README.md)
