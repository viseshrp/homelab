# Fail2ban

Consumes Nginx Proxy Manager logs and defines Cloudflare and UFW ban actions.

[Homelab index](../../README.md) · [Architecture](../architecture.md) · [Inspection record](../inventory.md)

## Observed setup

Compose, the active-named jail file, and its filter were read under `/opt`. The daemon, loaded jail state, firewall rules, and Cloudflare enforcement were not inspected.

Host: `rpiproxy`. Definition: `/opt/fail2ban/docker-compose.yml`.

Source file: `docker-compose/fail2ban/docker-compose.yml`.

| Service | Image/build recorded | Network / host ports | Restart |
| --- | --- | --- | --- |
| `fail2ban` | `crazymax/fail2ban:latest` | host; no host mapping declared | `always` |

| Service | Declared storage mapping |
| --- | --- |
| `fail2ban` | `./data:/data` |
| `fail2ban` | `/opt/nginx/data/logs:/var/log/npm` |
| `fail2ban` | `/var/log/auth.log:/var/log/auth.log:ro` |

Relative bind sources resolve beside the Compose file. Named volumes are Docker-managed. Paths outside `/opt` are declarations read from Compose; their contents and mount status were not inspected.

## Recreate the setup

1. Keep the jail, filter, and action definitions under `/opt/fail2ban/data`.
2. Map NPM’s `/opt/nginx/data/logs` into `/var/log/npm` in the container. Host networking and `NET_ADMIN`/`NET_RAW` are configured.
3. Provide private Cloudflare credentials outside the published configuration. Confirm the selected UFW action is executable in the environment where Fail2ban runs.
4. Test the regex against representative redacted access/error lines before enabling bans. The filter matches 3xx/4xx patterns, so ordinary redirects and missing resources can count.

These are owner-run setup instructions; no deployment command was executed during documentation. Pin compatible versions and supply private values before starting a new instance.

## Data and recovery

Back up jail/filter/action definitions and private action credentials separately. Ban-database recovery is distinct from restoring the intended policy.

## Verification and troubleshooting

Check that log paths, log format, and action commands agree. Forwarded-client-IP handling must be correct before client bans can be trusted. A configuration file does not prove the action succeeds.

## Deployment notes

The host file uses 30 retries within 2 hours and an indefinite ban. Private-network exclusions are configured. The Compose file mentions an authentication log outside `/opt`; its contents were not read.
