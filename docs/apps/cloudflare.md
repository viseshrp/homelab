# Cloudflare

Cloudflare provides DNS and edge security for the homelab. Fail2ban uses its API to block clients that repeatedly probe sensitive paths.

## My setup

On `rpiproxy`, Nginx accepts `CF-Connecting-IP` only from the Cloudflare networks listed in `cloudflare-trusted.conf`. Direct clients cannot select their logged address by sending that header.

The Fail2ban helper reads a private account email and Global API Key from an INI file. It checks existing exact-IP rules before adding a block, verifies uncertain writes, and removes only blocks whose rule ID, address, and creation note match its ownership journal. Protected addresses are excluded.

## Configuration

The trusted proxy ranges are in [the Nginx configuration](../../configs/nginx/data/nginx/custom/cloudflare-trusted.conf). Keep them aligned with [Cloudflare's published ranges](https://www.cloudflare.com/ips/). Credentials, the ownership journal, and personal allowlists stay outside Git.

[Back to homelab](../../README.md)
