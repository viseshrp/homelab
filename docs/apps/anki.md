# Anki sync server

The Anki server synchronizes flashcard collections and media between clients using a private sync endpoint.

## My setup

The service lives at `/opt/anki` on `rpiblog`. It uses `ghcr.io/luckyturtledev/anki`, with container name `anki-sync-server` and port 8080.

Nginx Proxy Manager forwards the `anki` hostname to `rpiblog:8080` over HTTP and provides HTTPS for clients.

## Configuration and data

`SYNC_USER1` supplies the private sync account. `SYNC_HOST`, `SYNC_PORT`, and the base URL configure the endpoint.

The host's `/opt/anki/data` directory is mounted at `/data`. It holds the server's persistent sync data. The container runs as `0:0` with an `unless-stopped` restart policy.

## Verify and recover

Check both `rpiblog:8080` and the public sync endpoint, then complete a sync from a real Anki client. An HTTP response alone does not prove that authentication, collection sync, and media sync work.

Back up `data/` with a consistent view of the files and retain the installed account/base-URL settings. After a restore, use a disposable client profile first so an incorrect server copy cannot overwrite a good client collection.

[Compose](../../docker-compose/anki/docker-compose.yml) · [Operations](../operations.md) · [Application index](README.md)
