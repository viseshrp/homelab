# Gotenberg

Gotenberg converts documents for the Paperless-ngx processing pipeline.

## My setup

Gotenberg 7.8 is part of `/opt/paperless` on `rpimon`. Paperless connects through its Gotenberg integration on the Compose network.

The container uses an `unless-stopped` restart policy and has no published host port.

## Converted files

Gotenberg handles conversion requests without a persistent volume in this stack. Paperless stores the documents and resulting application data in its own data and media volumes.

[Back to homelab](../../README.md)
