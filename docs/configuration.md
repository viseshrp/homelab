# Configuration

Each directory under `docker-compose/` contains a Compose template and `.env.example`. [deployments.json](../deployments.json) maps those templates to the host and `/opt` directory. Local hostnames and `example.com` stand in for private addresses and domains.

## Prepare a project

1. Run `python3 scripts/prepare.py npm local/nginx` from the repository root. This assembles NPM's Compose file, Nginx configuration, and trusted-proxy ranges in a new directory. It refuses to overwrite an existing directory.
2. Copy `local/nginx/.env.example` to `local/nginx/.env` and edit the values. Each project's additional inputs are listed below.
3. Run `docker compose --project-directory local/nginx config --quiet` to check the assembled configuration.

Preparation only copies local files. Deployment is a separate operator action. Preserve the existing project directory/name, volumes, bind mounts, and private settings when updating an installation. Compose derives named-volume names from the project name; changing `/opt/planka` to `/opt/boards`, for example, can select different storage.

Image defaults follow the inspected Compose files, including their floating tags. Set the image variables to the installed tag or digest before an intentional upgrade. Rendering a Compose file does not verify an image's application settings or perform a database migration.

## Project inputs

| Project | Private settings and supporting files |
| --- | --- |
| Anki | `SYNC_USER1` holds the sync credentials; `BASE_URL` is the client-facing endpoint. State stays in `./data`. |
| ArchiveBox | Set `DNS_SERVER`; `./data` is shared with pywb. ArchiveBox uses port 8002 and pywb 8082. |
| Blog | Supply the generated site in `./public`. `Dockerfile` and `default.conf` build its Nginx image. `publish.yml.example` belongs in the separate Hugo source repository; it copies only generated output to `/opt/blog/public`. |
| Dozzle | Set `DOZZLE_REMOTE_HOST` to the private Docker endpoints and create `./data/users.yml` with Dozzle's `generate` command. `users.yml.example` is an empty schema, not a working login. Retain the current users file when updating. |
| FBN | Set `FBN_SOURCE_DIR` to the separate FBN source checkout, `FBN_AUTH_FILE` to a private authentication export, and fill the group and Apprise destination. The selected external `FBN_DATA_VOLUME` must already exist. Bootstrap completes before the monitor starts. |
| File Browser | Set the two media directories. Each instance has its own settings file and database directory. The template defaults `FB_NOAUTH=false`; the inspected configuration used `noauth`. Preserve existing accounts and choose authentication deliberately. |
| Firezone | Legacy self-hosted Firezone configuration. Preserve the installed image and its complete private `.env`, including database credentials, salts, and admin settings. The example is a starting list, not a replacement for the existing environment. Its IPv6 example uses a private ULA subnet. |
| FTP | Set the username/password and media directory. Ports 20–21 and 40000–40009 are published. |
| GitHub runner | Set the source repository, runner registration token, labels, and work directory. Its Docker socket and blog mounts grant deployment access. |
| Homarr | The assembled board uses example domains and host aliases, with ArchiveBox/Paperless pointing to `rpimon`. Configure integration credentials through Homarr. Personal notes, location, and integration tokens are excluded from the sample. |
| Homebridge | Set `HOMEBRIDGE_DATA_DIR` to the existing data directory. This is the retained repository template; the host's SSH service was unavailable. |
| Linkding | `.env` is passed to the container. Preserve application settings alongside the provided port/data-directory options. |
| Nginx Proxy Manager | Keep the existing `data` and `letsencrypt` directories. [routes.json](../configs/nginx/routes.json) lists the nine proxy hosts using example domains; it is a reference, not an import file. |
| Paperless | Copy `docker-compose.env.example` to `docker-compose.env`; preserve the existing secret, database connection, OCR, mail, and consumer settings. Named `data`, `media`, and `redisdata` volumes persist the stack; `consume` and `export` are bind mounts. |
| Pi-hole | Preserve its private settings and `etc-pihole`/`etc-dnsmasq.d` directories. The template retains the inspected environment names; check their compatibility with the selected image before upgrading Pi-hole. |
| Planka | The image is pinned to 2.2.1 and the inspected digest. Preserve `SECRET_KEY`, `BASE_URL`, `/app/data`, and PostgreSQL's `db-data`. The isolated database retains the inspected `trust` authentication configuration. An older Planka database requires its own migration procedure. |
| Plex | Set media-root paths if they differ. Host networking, the existing configuration directory, and the inspected UID/GID values are retained. |
| qBittorrent/Gluetun | Supply AirVPN's WireGuard key, preshared key, and assigned addresses. Downloads use both media trees. qBittorrent shares Gluetun's network namespace; its ports are published by Gluetun. |
| Uptime Kuma | Keep `./uptime-kuma-data`, containing monitors and notification settings. |
| Vaultwarden | Preserve `./vw-data`, the public vault URL, and SMTP settings. Signups remain disabled. |
| WG-Easy | Supply the VPN endpoint, admin password, and current client DNS address. Preserve the existing WireGuard state in the project directory. This is the legacy image family used by the inspected Compose file. |

Firezone and WG-Easy both publish UDP 51820 on `vpn-edge`. Select one or explicitly change its host-port assignment before running both.

## Fail2ban and Nginx

The Fail2ban project assembles the `data` tree from `configs/fail2ban`. Before using it:

1. Copy `data/cloudflare-credentials.ini.example` to `data/cloudflare-credentials.ini` and fill the account email and Global API Key. Restrict the file to the account running the service.
2. Copy `data/f2b-integration.json.example` to `data/f2b-integration.json`. Add owner/admin public networks to `protected_networks` and the jail's `ignoreip`. For an existing installation, retain its `notes` and `set_prefix` values so the helpers recognize their rules and ipsets.
3. Preserve any additional private jails and exclusions. `NPM_LOG_DIR` selects the read-only NPM log mount.

The private integration policy could not be read from the host, so the example contains public Cloudflare ranges only. Both helpers exclude non-global IP addresses. The Cloudflare helper removes only rules with its ownership note; the local helper uses IPv4/IPv6 ipsets in `INPUT` and `DOCKER-USER`.

NPM's `nginx.conf` includes `data/nginx/custom/cloudflare-trusted.conf` and accepts `CF-Connecting-IP` only from those peers. Keep the ranges aligned with Cloudflare's published list. Nginx's remaining `/etc/nginx` includes come from the NPM image.

## Home Assistant and kiosk

`configs/homeassistant` contains the retained YAML configuration with private addresses replaced by `!secret` references. Copy `secrets.yaml.example` to `secrets.yaml` and supply the actual values. Preserve existing automations, scripts, scenes, and themes. The host was inaccessible over SSH; validate the legacy ping configuration against its installed Home Assistant version before using it.

The kiosk takes a private URL file based on [kiosk.urls.example](../configs/kiosk.urls.example). See [Kiosk](apps/kiosk.md) for desktop requirements.

## Local checks and updates

From the repository root:

```sh
python3 scripts/check.py
python3 -m unittest discover -s tests
```

The checker assembles all projects in temporary directories and runs `docker compose config --quiet` with dummy private values. It also checks shell/Python syntax, JSON, and local Markdown links. It does not contact hosts, start containers, or build images.

To preview an update on the machine holding an assembled project:

```sh
bash docker-compose/update.sh /path/to/project
bash docker-compose/update-all.sh /path/to/project-one /path/to/project-two
```

`--apply` runs the printed Compose commands: validate, pull images, build local images, and start services. The scripts do not upgrade the OS, discover other projects, remove orphan containers, or prune storage. FBN bootstrap and database migrations need project-specific review before an update.

[Back to homelab](../README.md)
