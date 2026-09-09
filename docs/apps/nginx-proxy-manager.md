# Nginx Proxy Manager

Nginx Proxy Manager gives the web apps HTTPS addresses and forwards each hostname to its service on the LAN.

## My setup

NPM lives on `rpiproxy` in `/opt/nginx`. The container uses `jc21/nginx-proxy-manager`, with ports 80 for HTTP, 443 for HTTPS, and 81 for administration. Certificates come from Let's Encrypt.

The `data/` directory holds NPM configuration and logs. `letsencrypt/` holds certificate state. Both sit beside the Compose file.

## Routes

| Name | HTTP backend | App |
| --- | --- | --- |
| `anki` | `rpiblog:8080` | Anki sync |
| `boards` | `rpiblog:3001` | Planka |
| `firezone` | `vpn-edge:13000` | Firezone |
| `home` | `rpiblog:7575` | Homarr |
| `links` | `rpiblog:9090` | Linkding |
| `pass` | `rpiblog:8089` | Vaultwarden |
| `plex` | `optiplex:32400` | Plex |
| `status` | `rpimon:3001` | Uptime Kuma |
| Root domain and `www` | `rpiblog:80` | Blog |

## Log filtering

[Fail2ban](fail2ban.md) reads NPM's logs from `/opt/nginx/data/logs`. Its jail uses Cloudflare and UFW actions to ban matching clients.

[Back to homelab](../../README.md)
