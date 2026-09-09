# Cal.com

Cal.com provides booking pages for scheduling meetings against connected calendars.

## Compose setup

The local configuration pairs Cal.com with PostgreSQL on a network named `stack`. The application publishes port 3000.

A private `.env` supplies the web URL, database connection, authentication secret, and encryption key. The build configuration also accepts license-consent and telemetry settings.

## Database

The `database-data` volume is mounted at `/var/lib/postgresql/data`. PostgreSQL stays on the Compose network without a published host port.

The application and database both use automatic restart policies.

[Back to homelab](../../README.md)
