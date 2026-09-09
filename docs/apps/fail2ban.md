# Fail2ban

Fail2ban watches log files for repeated request patterns and applies bans through configured actions.

## My setup

The Compose project lives at `/opt/fail2ban` on `rpiproxy` and uses `crazymax/fail2ban`. It runs with host networking and the `NET_ADMIN` and `NET_RAW` capabilities.

The `npm-docker` jail reads Nginx Proxy Manager's default-host access log and per-proxy access/error logs. `/opt/nginx/data/logs` is mounted at `/var/log/npm` inside the container.

## Rules and actions

The jail has a threshold of 30 matches in two hours and an indefinite ban duration. Private-network exclusions keep local traffic outside that rule.

The filter matches selected 3xx and 4xx log patterns. The configured actions are `cloudflare-apiv4` and `ufw-ip-ban`.

Jails, filters, and actions are stored beneath `/opt/fail2ban/data`. Cloudflare credentials belong in the private action configuration.

[Back to homelab](../../README.md)
