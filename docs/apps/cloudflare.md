# Cloudflare

Cloudflare provides DNS, edge security, and the public Home Assistant tunnel. Fail2ban also uses its API to block clients that repeatedly probe sensitive paths.

## My setup

On `rpiproxy`, Nginx accepts `CF-Connecting-IP` only from the Cloudflare networks listed in `cloudflare-trusted.conf`. Direct clients cannot select their logged address by sending that header.

The `cloudflared` project runs from `/opt/cloudflared` on `rpiproxy`. Its remotely managed route sends `hass.<domain>` to `rpihass:8123` across the LAN. The connector creates outbound connections to Cloudflare and does not require a new inbound firewall rule. Cloudflare Access protects the entire public hostname with an email one-time-PIN policy restricted to one host-only owner address and a 30-day (`720h`) application session. There are no path exceptions or bypass policies. Cloudflare One Client authentication is not enabled because the account does not have a One Client session duration configured. Home Assistant still performs its own authentication after Access. The public route bypasses Nginx Proxy Manager.

The Fail2ban helper reads a private account email and Global API Key from an INI file. It checks existing exact-IP rules before adding a block, verifies uncertain writes, and removes only blocks whose rule ID, address, and creation note match its ownership journal. Protected addresses are excluded.

## Configuration

The trusted proxy ranges are in [the Nginx configuration](../../configs/nginx/data/nginx/custom/cloudflare-trusted.conf). Keep them aligned with [Cloudflare's published ranges](https://www.cloudflare.com/ips/). Credentials, the ownership journal, and personal allowlists stay outside Git.

[`tunnels.json`](../../configs/cloudflare/tunnels.json) records the sanitized remote tunnel rule. [`access.json`](../../configs/cloudflare/access.json) records the Access application and policy without account IDs, object IDs, or the allowed email. Cloudflare ownership IDs remain in the mode-`0600` host-only manifest. The installed `.env` supplies `TUNNEL_TOKEN` and the private `RPIHASS_IP`; it must remain mode `0600` and outside Git. `CLOUDFLARED_IMAGE` selects the pinned multi-architecture connector image.

## Verify and recover

Verify the container healthcheck, recent connector logs, Cloudflare tunnel health and connection count, direct origin response from `rpiproxy`, and Home Assistant's UI-managed trusted-proxy settings. Unauthenticated public requests to the root, `/api/`, and Companion webhook paths must redirect to Cloudflare Access, and the allowed owner must complete the one-time-PIN flow in a browser. Home Assistant must still require either its own valid session or a separate login. After Home Assistant authentication, verify a WebSocket-backed browser update from outside the LAN. The native Companion apps cannot complete their remote connection through this hostname-wide Access gate without Cloudflare One Client; they continue to use the direct internal URL on the LAN. A DNS record or Access redirect alone does not prove that the tunnel can reach its origin.

Before changing the route or Access policy, record the existing DNS target, tunnel configuration, Access application, reusable policy, and application policy in a mode-`0600` host-only snapshot. Roll back the main gate by deleting the Home Assistant application and then its now-unused reusable policy. Restore tunnel fields separately only if they changed; no Home Assistant data is stored in the connector project.

[Back to homelab](../../README.md)
