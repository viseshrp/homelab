# Cloudflare

Cloudflare provides DNS and edge-security services. The homelab's Fail2ban configuration includes a Cloudflare ban action, and Homarr has a shortcut to the Cloudflare dashboard.

## My setup

The `npm-docker` jail on `rpiproxy` selects `cloudflare-apiv4` alongside its UFW action. That action uses private account credentials to request client bans.

[Nginx Proxy Manager](nginx-proxy-manager.md) handles the lab's HTTPS hostnames and forwards requests to the application hosts.

## Configuration

The Cloudflare action is stored under `/opt/fail2ban/data/action.d`. Account identifiers, API credentials, and the account-specific dashboard link stay private.

[Back to homelab](../../README.md)
