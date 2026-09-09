# Nginx Proxy Manager

Nginx Proxy Manager is the shared HTTPS entry point for the public web applications. It terminates TLS on `rpiproxy` and forwards requests over HTTP to four backend hosts.

## Deployment

| Item | Value |
| --- | --- |
| Host | `rpiproxy` |
| Project directory | `/opt/nginx` |
| Compose project | [`docker-compose/npm`](../../docker-compose/npm/docker-compose.yml) |
| HTTP / HTTPS | 80 / 443 |
| Administration | 81 |
| Persistent configuration and logs | `/opt/nginx/data` |
| Certificate state | `/opt/nginx/letsencrypt` |
| Container health check | `/bin/check-health` every 10 seconds |

The Compose template also publishes UDP 51820. That port is not an HTTP proxy-host entry; document and verify its forwarding purpose separately.

## Observed proxy map

The NPM UI displayed version 2.15.1 and these nine enabled rows during a read-only check on September 9, 2026. All used Let's Encrypt, the Public access-list setting, and an Online row status.

| Public name | Backend | Service |
| --- | --- | --- |
| `anki.<domain>` | `rpiblog:8080` | Anki sync |
| `boards.<domain>` | `rpiblog:3001` | Planka |
| `firezone.<domain>` | `vpn-edge:13000` | Firezone management |
| `home.<domain>` | `rpiblog:7575` | Homarr |
| `links.<domain>` | `rpiblog:9090` | Linkding |
| `pass.<domain>` | `rpiblog:8089` | Vaultwarden |
| `plex.<domain>` | `optiplex:32400` | Plex |
| `status.<domain>` | `rpimon:3001` | Uptime Kuma |
| `<domain>` and `www.<domain>` | `rpiblog:80` | Hugo site |

The table uses sanitized domains and logical host names. Live NPM stores LAN addresses for the observed backends. The Mac's `/etc/hosts` maps most logical names to those addresses, but it does not currently define `vpn-edge`. See [host name resolution](../inventory.md#host-name-resolution).

An Online row and the container health check cover NPM state only. Verify the public URL, direct backend, application logs, dependencies, and persisted data before declaring a service healthy.

## Client addresses and bans

The mounted [`nginx.conf`](../../configs/nginx/nginx.conf) includes [`cloudflare-trusted.conf`](../../configs/nginx/data/nginx/custom/cloudflare-trusted.conf). Nginx accepts `CF-Connecting-IP` only from the listed Cloudflare networks, preventing direct clients from choosing the address written to access logs.

[Fail2ban](fail2ban.md) mounts `/opt/nginx/data/logs` read-only. Its NPM jail matches repeated probes for sensitive files and exploit paths, then applies source-IP firewall bans and owned Cloudflare rules. Private integration policy and credentials remain outside Git.

## Route-change checklist

1. Confirm the backend works directly from `rpiproxy`.
2. Create or edit the NPM row with the intended domain, HTTP destination, certificate, and access policy.
3. Test the public URL through normal DNS and TLS.
4. Confirm the backend receives the expected client/proxy headers and that WebSocket-dependent features work.
5. Update [`configs/nginx/routes.json`](../../configs/nginx/routes.json) as the sanitized reference.

Changing `routes.json` does not update NPM. Never paste a rendered production configuration or certificate material into the repository.

## Backup and recovery

Back up `data/`, `letsencrypt/`, the installed Compose file, and its private environment as one recovery set. This template uses NPM's SQLite database under `data/`; quiesce writes or copy it consistently. After a restore, verify:

1. The administration login and all nine proxy rows.
2. Certificate presence and renewal state.
3. A direct backend and its corresponding public URL.
4. Real client-address logging through Cloudflare and from the LAN.
5. Fail2ban log access without giving it write access to the NPM tree.

[Troubleshooting runbook](../operations.md#diagnose-a-public-url) · [Configuration](../configuration.md#fail2ban-and-nginx) · [Back to application index](README.md)
