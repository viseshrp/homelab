# Planka

Planka provides Kanban boards with lists, cards, and attachments.

## My setup

The project lives at `/opt/planka` on `rpiblog`. It pairs digest-pinned Planka 2.2.1 with PostgreSQL 14 Alpine.

Planka listens on container port 1337, published as host port 3001. Nginx Proxy Manager sends the `boards` hostname to that port. The app's base URL and proxy-trust setting support this HTTPS route.

## Data

| Volume | Container path | Contents |
| --- | --- | --- |
| `data` | `/app/data` | Application files |
| `db-data` | `/var/lib/postgresql/data` | PostgreSQL database |

The database connection URL and application secret are private settings. PostgreSQL stays on the Compose network without a published host port. Both containers use `unless-stopped`.

## Verify and recover

Check `rpiblog:3001` and the `boards` route, then open known boards, cards, and attachments. That confirms the application volume and PostgreSQL data agree.

Back up PostgreSQL consistently and preserve the `data` attachment volume, `SECRET_KEY`, base URL, and installed image digest. Planka major-version migrations are stateful; do not treat an image rollback as a database rollback.

[Compose](../../docker-compose/planka/docker-compose.yml) · [Operations](../operations.md) · [Application index](README.md)
