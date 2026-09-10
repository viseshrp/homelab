# Cloudflare

Cloudflare provides DNS, edge security, and the public Home Assistant tunnel. Fail2ban also uses its API to block clients that repeatedly probe sensitive paths.

## My setup

On `rpiproxy`, Nginx accepts `CF-Connecting-IP` only from the Cloudflare networks listed in `cloudflare-trusted.conf`. Direct clients cannot select their logged address by sending that header.

The `cloudflared` project runs from `/opt/cloudflared` on `rpiproxy`. Its remotely managed route sends `hass.<domain>` to `rpihass:8123` across the LAN. The connector creates outbound connections to Cloudflare and does not require a new inbound firewall rule. The public Home Assistant route bypasses Nginx Proxy Manager.

The Fail2ban helper reads a private account email and Global API Key from an INI file. It checks existing exact-IP rules before adding a block, verifies uncertain writes, and removes only blocks whose rule ID, address, and creation note match its ownership journal. Protected addresses are excluded.

## Configuration

The trusted proxy ranges are in [the Nginx configuration](../../configs/nginx/data/nginx/custom/cloudflare-trusted.conf). Keep them aligned with [Cloudflare's published ranges](https://www.cloudflare.com/ips/). Credentials, the ownership journal, and personal allowlists stay outside Git.

[`tunnels.json`](../../configs/cloudflare/tunnels.json) records the sanitized remote tunnel rule. The installed `.env` supplies `TUNNEL_TOKEN` and the private `RPIHASS_IP`; it must remain mode `0600` and outside Git. `CLOUDFLARED_IMAGE` selects the pinned multi-architecture connector image.

## Verify and recover

Verify the container healthcheck, recent connector logs, Cloudflare tunnel health and connection count, direct origin response from `rpiproxy`, Home Assistant's UI-managed trusted-proxy settings, the public login page, and a WebSocket-backed UI update. A DNS record alone does not prove that the tunnel has a connector or can reach its origin.

Before changing the route, record the existing DNS target and tunnel configuration. To roll back, restore those Cloudflare fields and stop only `/opt/cloudflared`; no Home Assistant data is stored in the connector project.

[Back to homelab](../../README.md)
