# Apache Tika

Tika extracts text and metadata from document formats for Paperless-ngx.

## My setup

The `tika` service belongs to `/opt/paperless` on `rpimon`. It uses `ghcr.io/paperless-ngx/tika` with an `unless-stopped` restart policy.

Paperless has the Tika integration enabled and connects to it over the internal Compose network.

## Document flow

Paperless sends documents to Tika for extraction and keeps the resulting application data in its own storage. Tika has no persistent volume or published host port in this stack.

[Compose](../../docker-compose/paperless/docker-compose.yml) · [Setup](../configuration.md) · [Back to homelab](../../README.md)
