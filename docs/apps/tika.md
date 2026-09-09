# Apache Tika

Document-content extraction dependency in the Paperless stack.

[Homelab index](../../README.md) · [Architecture](../architecture.md) · [Inspection record](../inventory.md)

## Observed setup

Paperless Compose defines `ghcr.io/paperless-ngx/tika:latest` and enables its Tika integration. No conversion or extraction request was sent.

Host association: `rpimon`.


## Recreate the setup

1. Keep the Tika service on the Paperless Compose network.
2. Configure Paperless’s Tika endpoint to use the internal service, as in the inspected definition.
3. The Tika service has no declared persistent volume or published host port in this stack.
4. Validate extraction with a disposable supported document after Paperless itself is responding.

These are owner-run setup instructions; no deployment command was executed during documentation. Pin compatible versions and supply private values before starting a new instance.

## Data and recovery

Preserve the Compose definition and selected image version. Persisted documents and application metadata belong to Paperless, not this conversion container.

## Verification and troubleshooting

If a document cannot be extracted, distinguish file-format support from service reachability and endpoint configuration. A container restart is not evidence that extraction works.

## Deployment notes

The parent Paperless listener refused connections during this audit. Tika runtime health was not independently established.

Related: [Paperless-ngx](paperless.md).
