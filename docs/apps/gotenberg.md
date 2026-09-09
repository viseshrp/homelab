# Gotenberg

Document-conversion dependency used by the Paperless integration.

[Homelab index](../../README.md) · [Architecture](../architecture.md) · [Inspection record](../inventory.md)

## Observed setup

The inspected Paperless definition selects `gotenberg/gotenberg:7.8` and provides a custom command. No conversion request or generated document was inspected.

Host association: `rpimon`.


## Recreate the setup

1. Use the Gotenberg service inside the Paperless project network.
2. Configure Paperless’s Gotenberg endpoint together with its Tika integration.
3. The inspected service publishes no host port and declares no persistent volume. Preserve the project’s intended command when rebuilding.
4. Test a disposable conversion end to end through Paperless before relying on document ingestion.

These are owner-run setup instructions; no deployment command was executed during documentation. Pin compatible versions and supply private values before starting a new instance.

## Data and recovery

Preserve the selected image and invocation in the application configuration. Back up converted output through Paperless’s media/export recovery process.

## Verification and troubleshooting

Check the internal endpoint and selected conversion features if office-document ingestion fails. Keep conversion failures separate from OCR and database issues.

## Deployment notes

The image tag here records the inspected file, not a recommendation of a current Gotenberg release.

Related: [Paperless-ngx](paperless.md).
