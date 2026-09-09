# Configuration

The checked-in files are sanitized templates. They describe service shape, required inputs, and intended placement without storing credentials or claiming to be exact copies of running projects.

## Configuration layers

| Layer | Purpose | Authority |
| --- | --- | --- |
| `docker-compose/<project>/docker-compose.yml` | Reusable services, mounts, ports, and defaults | Template for that project |
| `docker-compose/<project>/.env.example` | Required and optional substitution names | Input reference only |
| `deployments.json` | Intended host or hosts, installed directory, and copied assets | Repository deployment map |
| `configs/` | Sanitized files assembled beside selected projects | Checked-in configuration |
| Installed project directory | Private `.env`, application files, and runtime-compatible settings | Preserve during an update |
| Named volumes and bind mounts | Durable application data | Preserve and back up separately |

A rendered Compose file can contain interpolated secrets. Inspect it locally, but do not commit or publish its output.

## Prepare an isolated project

`scripts/prepare.py` copies one template, its example inputs, and the assets named by `deployments.json` into a new directory. It will not overwrite an existing path.

```sh
homelab_stage=$(mktemp -d)
python3 scripts/prepare.py npm "$homelab_stage/nginx"
cp "$homelab_stage/nginx/.env.example" "$homelab_stage/nginx/.env"
```

Fill required private values, then render the staged project:

```sh
docker compose \
  --project-directory "$homelab_stage/nginx" \
  --env-file "$homelab_stage/nginx/.env" \
  config --quiet
```

Preparation does not contact a host, deploy a file, create a volume, pull an image, or start a container.

## Update an existing installation

Treat the installed project as stateful.

1. Record its Compose project name, effective image references, mounts, volumes, and private input files.
2. Back up the recovery units listed in [the operations guide](operations.md#backup-and-recovery).
3. Prepare the repository template in a new staging directory.
4. Compare and merge the intended change into the installed project. Keep private and installation-specific settings.
5. Render, preview, apply, and verify one project using [the update runbook](operations.md#update-one-project).

Compose derives default named-volume names from the project name. Changing the directory or `--project-name` can select a different, empty volume even when the Compose YAML is unchanged.

## Project inputs

### Web and automation

| Project | Required private or external inputs | State to preserve |
| --- | --- | --- |
| Anki | `SYNC_USER1`; client-facing `BASE_URL` | `data/` |
| Blog | Generated Hugo output from the separate source repository | `public/` is replaceable output; preserve local build files |
| FBN | Source checkout, auth export, group, Apprise URL, external volume name | External `FBN_DATA_VOLUME`, including browser profile and SQLite state |
| GitHub runner | Repository URL, registration token, labels, work directory | Runner registration can be recreated; protect Docker-socket and blog write access |
| Homarr | Base URL, password, integration credentials | `homarr/configs`, `homarr/icons`, `homarr/data` |
| Linkding | Application settings in the private `.env` | Configured data directory |
| Planka | `SECRET_KEY`, base URL, database URL | `data` and `db-data` volumes |
| Vaultwarden | Domain, SMTP settings, installed image | `vw-data/` |

### Monitoring, documents, and archives

| Project | Required private or external inputs | State to preserve |
| --- | --- | --- |
| ArchiveBox | DNS server and chosen image versions | Shared `data/` tree used by ArchiveBox and pywb |
| Dozzle | Remote agent endpoints and generated users file | `data/` and private authentication configuration |
| Dozzle Agent | Per-host LAN bind address and display hostname | No application data; preserve installed Compose input for repeatable restarts |
| Paperless | `docker-compose.env` with secret, URL, database/OCR/mail/consumer settings | `data`, `media`, `redisdata`, `consume`, and `export` |
| Uptime Kuma | Installed image | `uptime-kuma-data/` |

### Media, network, and home services

| Project | Required private or external inputs | State to preserve |
| --- | --- | --- |
| File Browser | Authentication decision and both media roots | Separate database directories, settings files, and media trees |
| Firezone | Complete legacy Firezone environment: database credentials, salts, admin settings, external URL | `firezone/`, `postgres-data`, private environment |
| FTP | User, password, media directory | External media tree and private account settings |
| Homebridge | Existing `HOMEBRIDGE_DATA_DIR` | The configured host directory, including pairing and plugin state |
| Nginx Proxy Manager | Installed image and frame policy | `data/`, `letsencrypt/`, installed environment |
| Pi-hole | Admin credential and installed image-compatible environment | `etc-pihole/`, `etc-dnsmasq.d/` |
| Plex | Media roots and installed image | `config/`, local TV/movie directories, both media trees |
| qBittorrent/Gluetun | AirVPN WireGuard private key, preshared key, assigned addresses | qBittorrent config, Gluetun state, both download trees |
| WG-Easy | Endpoint, admin password, client DNS | Project directory containing WireGuard keys and peer state |

## Cross-project constraints

### Host names

The sanitized configuration uses names such as `rpiblog` and `vpn-edge`. The Mac currently resolves most deployment names through `/etc/hosts`; the repository does not manage that file. `vpn-edge` was not present there when checked. Live NPM uses LAN addresses for its backends, while `configs/nginx/routes.json` uses logical names. Make sure the system applying a configuration can resolve any name it is expected to use.

### Port ownership

Firezone and WG-Easy both publish UDP 51820 on `vpn-edge`. They cannot use that host port simultaneously without changing one definition. The NPM template also publishes UDP 51820 on `rpiproxy`; there is no corresponding HTTP proxy row, so document the intended forwarding path before depending on that port.

### Image changes

Most image defaults float on `latest` or another moving tag. Set image variables to the installed tag or digest before an intentional upgrade. Rendering a Compose file does not validate application-level settings, schema migrations, architecture support, or rollback compatibility.

Planka is pinned to 2.2.1 and an inspected digest. An older Planka database needs its supported migration sequence; do not point a newer image at it casually. Firezone and WG-Easy use legacy image families and need version-specific review before an upgrade.

### Docker access

Homarr, Dozzle, the Dozzle agents, and the GitHub runner mount the Docker socket. Remote agents replace unauthenticated Docker TCP listeners and expose only Dozzle's TLS agent protocol on LAN port 7007. Keep the central UI authenticated, do not enable actions or shell access, and do not forward agent ports outside the LAN.

## Fail2ban and Nginx

The Fail2ban project assembles the `data` tree from `configs/fail2ban`. Before using it:

1. Copy `data/cloudflare-credentials.ini.example` to `data/cloudflare-credentials.ini` and fill the account email and Global API Key. Restrict the file to the account running the service.
2. Copy `data/f2b-integration.json.example` to `data/f2b-integration.json`. Add owner/admin public networks to `protected_networks` and the jail's `ignoreip`. For an existing installation, retain its `notes`, `owner_id`, `ownership_file`, and `set_prefix` values, together with the ownership journal. Set `database` to the container path of the existing Fail2ban SQLite database.
3. Preserve any additional private jails and exclusions. `NPM_LOG_DIR` selects the read-only NPM log mount.

The private integration policy could not be read from the host, so the example contains public Cloudflare ranges only. Both helpers exclude non-global IP addresses. The Cloudflare helper records creation intent and rule ownership in an append-only journal; unban requires a matching rule ID, address, and creation note. The local helper uses IPv4/IPv6 ipsets in `INPUT` and `DOCKER-USER` and restores unexpired bans from the database at startup.

The jail selects `action.d/persistent.py`, which preserves bans during shutdown and allows explicit unban operations while running. Restored tickets skip Cloudflare writes. Its lifecycle handling and database query target Fail2ban 1.1.0; check these when changing the container image. The legacy `.conf` actions remain available but are not selected by this jail.

NPM's `nginx.conf` includes `data/nginx/custom/cloudflare-trusted.conf` and accepts `CF-Connecting-IP` only from those peers. Keep the ranges aligned with Cloudflare's published list. Nginx's remaining `/etc/nginx` includes come from the NPM image.

## NPM route reference

[`configs/nginx/routes.json`](../configs/nginx/routes.json) records the nine observed routes with example domains and logical backend names. It is not an import file and changing it does not change NPM. When an operator intentionally changes a live route, update the reference separately and verify the public URL and direct backend.

## Home Assistant and kiosk

`configs/homeassistant` contains retained YAML with private addresses replaced by `!secret` references. Copy `secrets.yaml.example` to `secrets.yaml`, fill the actual values, and preserve the existing automations, scripts, scenes, and themes. The Home Assistant host runs Home Assistant OS with Supervisor. The Dozzle Agent is packaged as a custom app because normal host SSH and the Docker TCP API are unavailable. Validate retained Home Assistant configuration against its installed version before applying it.

The kiosk reads a private URL file based on [`kiosk.urls.example`](../configs/kiosk.urls.example). It needs a dedicated desktop browser session plus `xset` and `xdotool` for automatic rotation. See [the kiosk notes](apps/kiosk.md).

## Repository checks

From the repository root:

```sh
python3 scripts/check.py
python3 -m unittest discover -s tests
```

The checker uses dummy values to render all 22 Compose projects in temporary directories. It checks shell/Python syntax, JSON, YAML, and local Markdown links. It does not contact hosts, start containers, build images, or inspect private installed configuration.

[Back to homelab](../README.md)
