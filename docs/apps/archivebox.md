# ArchiveBox

ArchiveBox saves local copies of web pages. The accompanying pywb service replays captures stored in WARC format.

## My setup

The project lives at `/opt/archivebox` on `rpimon`. ArchiveBox uses the `archivebox/archivebox` image, with `dev` as the Compose default tag, and publishes host port 8002 to container port 8000.

The private `.env` supplies the canonical `BASE_URL` and chosen image versions. `SERVER_SECURITY_MODE` defaults to `auto`, new captures default to private, and the public index, snapshots, and add view are disabled. SSL checking is enabled. Capture settings use a 120-second timeout and a media-size limit of `1500m`.

The first-run setup is configured as a private server on one trusted-LAN hostname using direct HTTP. Saving the setup form stores the generated secret and selected routing/access values in ArchiveBox's database and `data/ArchiveBox.conf`; keep that runtime configuration with the shared recovery unit. When changing the canonical URL or access model, update the repository inputs first and compare the non-secret saved values after deployment.

## Archive and replay

`/opt/archivebox/data` is mounted at `/data` in ArchiveBox. [pywb](pywb.md) mounts that same directory at `/archivebox` and its `wayback/` subdirectory at `/webarchive`.

pywb publishes a separate interface on port 8082. Its startup command indexes WARC files from the ArchiveBox capture tree into the `default` collection before starting the replay server.

## Verify and recover

Verify two outcomes separately: ArchiveBox can create a new capture, and pywb can replay an existing WARC. A working ArchiveBox page does not prove that browser capture dependencies or replay indexes work.

The shared `data/` tree is the recovery unit. Preserve snapshots, WARC files, ArchiveBox state, `ArchiveBox.conf`, and the pywb collection/index data together. After a restore, compare capture counts, confirm the saved non-secret routing/access values, and open representative archived assets rather than checking only the index page.

[Compose](../../docker-compose/archivebox/docker-compose.yml) · [Operations](../operations.md) · [Application index](README.md)
