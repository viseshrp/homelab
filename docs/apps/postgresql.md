# PostgreSQL

PostgreSQL stores application data for Planka, Firezone, and the Cal.com configuration. Each project has its own database container and volume.

## Databases

| Application | Image | Volume |
| --- | --- | --- |
| Planka on `rpiblog` | `postgres:14-alpine` | `db-data` |
| Firezone on `vpn-edge` | `postgres:15` | `postgres-data` |
| Cal.com configuration | `postgres` | `database-data` |

## Storage and connections

Each volume is mounted at `/var/lib/postgresql/data`. Application containers connect through their own Compose networks; these definitions do not publish PostgreSQL to a host port.

Connection URLs and database credentials belong to each application's private configuration.

[Back to homelab](../../README.md)
