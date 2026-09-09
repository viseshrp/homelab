# Paperless-ngx

Paperless stores and indexes documents, with background processing for text extraction and conversion.

## My setup

The project is `/opt/paperless` on `rpimon`. Four services share its Compose network:

| Service | Role |
| --- | --- |
| Paperless-ngx | Web interface and document processing on port 8000 |
| Redis 7 | Task broker |
| Apache Tika | Document-content extraction |
| Gotenberg 7.8 | Document conversion |

Paperless connects to `redis://broker:6379` and has its Tika and Gotenberg integration enabled. Private application settings come from `docker-compose.env`.

## Document storage

Named volumes hold application data, document media, and Redis state. Two directories beside the Compose file handle file exchange:

| Directory | Container path | Purpose |
| --- | --- | --- |
| `consume` | `/usr/src/paperless/consume` | Incoming documents |
| `export` | `/usr/src/paperless/export` | Exported documents and data |

The web service publishes port 8000. Redis and the conversion services stay on the internal network.

[Compose](../../docker-compose/paperless/docker-compose.yml) · [Setup](../configuration.md) · [Back to homelab](../../README.md)
