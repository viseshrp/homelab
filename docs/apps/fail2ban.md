# Fail2ban

Fail2ban blocks repeated probes for sensitive files and exploit endpoints in Nginx Proxy Manager's access logs.

## My setup

`rpiproxy:/opt/fail2ban` runs `crazymax/fail2ban` with host networking and `NET_ADMIN`/`NET_RAW`. The `npm-docker` jail reads the default-host, proxy-host, and fallback HTTP access logs from `/opt/nginx/data/logs`.

Thirty matching requests within two hours trigger an indefinite ban. The filter targets paths such as `.env`, `.git/config`, and exploit endpoints returning 4xx responses. Ordinary redirects, login failures, and missing assets do not match.

## Ban actions

`cloudflare-apiv4` calls a Python helper that manages exact-IP Cloudflare block rules. Unban removes only rules carrying this integration's ownership note. Credentials are read from a private INI file.

The legacy `ufw-ip-ban` action name now calls a source-IP helper. IPv4 and IPv6 ipsets apply to HTTP(S) traffic in `INPUT` and `DOCKER-USER`. It does not inspect request headers with iptables string matching. Private addresses and configured protected networks are excluded by both helpers.

[Configuration and private inputs](../configuration.md#fail2ban-and-nginx) · [Back to homelab](../../README.md)
