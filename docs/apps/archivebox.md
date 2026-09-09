# ArchiveBox

ArchiveBox saves local copies of web pages. The accompanying pywb service replays captures stored in WARC format.

## My setup

The project lives at `/opt/archivebox` on `rpimon`. ArchiveBox uses the `archivebox/archivebox` image, with `dev` as the Compose default tag, and publishes host port 8002 to container port 8000.

The public index, snapshots, and add view are disabled. SSL checking is enabled. Capture settings use a 120-second timeout and a media-size limit of `1500m`.

## Archive and replay

`/opt/archivebox/data` is mounted at `/data` in ArchiveBox. [pywb](pywb.md) mounts that same directory at `/archivebox` and its `wayback/` subdirectory at `/webarchive`.

pywb publishes a separate interface on port 8082. Its startup command indexes WARC files from the ArchiveBox capture tree into the `default` collection before starting the replay server.

[Back to homelab](../../README.md)
