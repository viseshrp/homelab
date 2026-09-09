# PostgreSQL

Private SQL data service in the Planka and Firezone definitions and the Cal.com repository template.

[Homelab index](../../README.md) · [Architecture](../architecture.md) · [Inspection record](../inventory.md)

## Observed setup

Planka declares PostgreSQL 14 Alpine, Firezone PostgreSQL 15, and Cal.com an unpinned PostgreSQL image. Database contents and listeners were not inspected.


## Recreate the setup

1. Keep each app’s database in its own Compose project/network and persistent volume.
2. Supply private database credentials and a matching application connection URL. No inspected project publishes a PostgreSQL host port.
3. Use an app-compatible database major version. A PostgreSQL major-version change requires a planned data migration.
4. Confirm database readiness before checking application health; a simple `depends_on` entry is startup ordering, not a readiness guarantee.

These are owner-run setup instructions; no deployment command was executed during documentation. Pin compatible versions and supply private values before starting a new instance.

## Data and recovery

Create consistent logical dumps or coordinated physical backups. Restore the database alongside the matching app files and private secrets, then test application-level reads.

## Verification and troubleshooting

For an app that cannot connect, check network/service-name resolution, credentials, database readiness, and version compatibility. Do not delete volumes to resolve startup problems.

## Deployment notes

Volume names are `db-data` for Planka, `postgres-data` for Firezone, and `database-data` for the Cal.com template. Docker may prefix these names with the project name; actual Docker-managed storage was not inspected.
