# Fail2ban

Fail2ban blocks repeated probes for sensitive files and exploit endpoints in Nginx Proxy Manager's access logs.

## My setup

`rpiproxy:/opt/fail2ban` runs `crazymax/fail2ban` with host networking and `NET_ADMIN`/`NET_RAW`. The `npm-docker` jail reads the default-host, proxy-host, and fallback HTTP access logs from `/opt/nginx/data/logs`.

Thirty matching requests within two hours trigger an indefinite ban. The filter targets paths such as `.env`, `.git/config`, and exploit endpoints returning 4xx responses. Ordinary redirects, login failures, and missing assets do not match.

## Ban actions

The jail uses `persistent.py` actions for Cloudflare and the local firewall. Cloudflare rule IDs and unique creation notes are recorded in a private ownership journal. Unban removes only exact-IP rules with matching ownership records. Credentials are read from a private INI file.

The local action calls a source-IP helper. IPv4 and IPv6 ipsets apply to HTTP(S) traffic in `INPUT` and `DOCKER-USER`. It does not inspect request headers with iptables string matching. Private addresses and configured protected networks are excluded by both helpers.

Startup restores unexpired local bans from the Fail2ban database. Restored tickets skip Cloudflare writes. Shutdown preserves external bans; explicit unban operations still remove owned rules. The action follows Fail2ban 1.1.0 lifecycle behavior.

[Configuration and private inputs](../configuration.md#fail2ban-and-nginx) · [Back to homelab](../../README.md)
