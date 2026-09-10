# Repository instructions

## Scope

These instructions apply to the entire repository unless a nested `AGENTS.md` adds narrower rules. The user's current request and system instructions take precedence.

This repository is the canonical, sanitized source for homelab configuration. Installed hosts contain private values and persistent runtime state, but they must not become an independent source of long-lived configuration.

## Non-negotiable configuration contract

Every managed configuration change is a repository-and-host change.

1. Edit the repository first. Do not make a persistent host-only configuration change.
2. Validate the repository change before deploying it.
3. Synchronize the exact in-scope change to every target declared in `deployments.json`.
4. Apply or restart only the affected project when the change requires it.
5. Verify repository/host parity and the application outcome.
6. Update the relevant documentation when the topology, inputs, routes, state, or operating procedure changed.

A configuration task is incomplete until the repository and all in-scope hosts agree. If a host cannot be reached, a target path is unknown, or safe deployment cannot be verified, report the repository change as **not deployed** and the task as incomplete. Never imply host parity from a local test.

The latest explicit user boundary overrides the standing sync rule. If the user says `read-only`, `repo-only`, `do not deploy`, or equivalent, do not write to hosts. State clearly that runtime configuration remains unsynchronized.

### What counts as managed configuration

The contract covers:

- `docker-compose/**`, including Compose files, Dockerfiles, patches, settings, and `.env.example` files;
- `configs/**`;
- `deployments.json`;
- `home-assistant-dozzle-agent/**` and `repository.yaml`;
- scripts that assemble, validate, update, or operate deployments;
- Nginx Proxy Manager routes represented by `configs/nginx/routes.json`;
- documentation that defines runtime configuration or host placement.

Documentation-only wording changes do not require host deployment. Code under `stashfleet/` follows its own package/test workflow unless the task also changes a live backup configuration.

## Authorization boundary

Unless a later user instruction narrows the scope, a request to change, fix, update, or configure a managed service includes:

- the repository edit;
- synchronization to only the host or hosts mapped for that project;
- a minimal restart or recreate of only that project when required;
- post-change runtime and parity checks.

That standing instruction does not authorize:

- deleting volumes, databases, certificates, media, backups, or application records;
- `docker compose down -v`, Docker prune operations, or recursive deletion;
- OS upgrades, reboots, host-wide package changes, or host-wide container restarts;
- unrelated firewall, router, DNS-provider, Cloudflare, account, or permission changes;
- a database migration or application downgrade without a verified backup and version-specific plan;
- committing or pushing Git changes unless the user asks for it.

Stop before a materially destructive, irreversible, broadly disruptive, or externally scoped action.

## Repository map

| Path | Role |
| --- | --- |
| `deployments.json` | Canonical project-to-host(s), installed-directory, Compose filename, and asset map |
| `docker-compose/<project>/` | Sanitized project template and input schema |
| `configs/` | Checked-in configuration copied into selected projects |
| `scripts/prepare.py` | Builds a new isolated project directory without overwriting an existing path |
| `scripts/check.py` | Offline assembly, Compose rendering, syntax, and Markdown-link validation |
| `docker-compose/update.sh` | One-project update preview; `--apply` performs the printed commands |
| `docker-compose/update-all.sh` | Explicit multi-project wrapper; never discovers projects automatically |
| `home-assistant-dozzle-agent/` | Home Assistant OS app packaging for the Dozzle agent |
| `docs/` | Architecture, inventory, configuration, runbooks, and per-service recovery notes |
| `stashfleet/` | Standalone server-to-client backup package |

`deployments.json` may declare either one `host` or a list of `hosts`. Treat the two forms literally. A replicated project such as `dozzle-agent` must be synchronized and verified on every listed host. A `null` directory, currently used for the retained Homebridge template, is not permission to guess a path.

## Required workflow for configuration changes

### 1. Establish the repository baseline

Run:

```sh
git status --short --branch
```

Preserve all pre-existing modifications. Do not overwrite, reformat, stage, or revert unrelated work. If an in-scope file is already modified, inspect the diff and merge carefully.

Read:

- the project entry in `deployments.json`;
- its full `docker-compose/<project>/` directory;
- every source and destination in the project's `assets` map;
- the relevant application page under `docs/apps/`;
- `docs/configuration.md` and the applicable part of `docs/operations.md`.

### 2. Resolve every target

Use `deployments.json` rather than memory. Confirm:

- exact host alias;
- exact installed directory;
- whether the project has one target or multiple targets;
- whether the local alias resolves on the current Mac;
- whether an alias represents the same machine as another alias.

The local `/etc/hosts` file is host-specific runtime configuration and is not currently generated by this repository. Do not change it as a side effect. If a task explicitly changes it, first add or update a sanitized repository representation of the alias-to-role mapping, then verify semantic parity after the live edit. It currently carries aliases used by the deployment map, including both `rpivpn` and `vpn-edge` for the VPN host, but re-read it before relying on that mapping. Treat raw private addresses as host-only inputs and keep them out of committed public documentation unless the user explicitly changes that policy.

### 3. Inspect the host read-only

Before editing or deploying, collect enough current evidence to avoid overwriting live state:

- installed Compose and override filenames;
- Compose project name;
- private input filenames, without printing their values;
- current image references and image IDs;
- named volumes, bind mounts, owners, and modes;
- host architecture, available disk, and relevant resource limits;
- currently bound ports and dependent services;
- container status, health, and recent errors;
- application/database version and migration state;
- existing backup and rollback material.

Use noninteractive SSH with strict host-key checking, bounded connection timeouts, and forwarding disabled. Keep inspection within the mapped project directory and the minimum host-level commands needed to validate mounts, ports, resources, Docker, or service state.

Do not emit secrets from `.env`, rendered Compose output, Docker inspect output, application databases, logs, browser profiles, cookies, or credential files.

### 4. Define backup and rollback before mutation

For stateful services, identify the recovery unit from `docs/operations.md` and the application page. A filesystem copy of a live PostgreSQL or SQLite database is not automatically consistent.

Record:

- the current image tag and immutable image ID or digest;
- the exact files that will be replaced;
- the Compose project name and volume names;
- the database/application backup method;
- the rollback command sequence;
- the condition that triggers rollback.

Use an application export, database-native dump, quiesced copy, or documented snapshot appropriate to the service. Verify that the backup exists and is readable before deploying.

### 5. Edit the repository

Use `apply_patch` for hand edits. Keep changes limited to the requested project and its required metadata/docs.

For Compose changes:

- preserve project identity, volume names, bind paths, restart behavior, health checks, and private overlays unless the task changes them deliberately;
- keep host-specific values configurable through environment inputs;
- add every new input to `.env.example` with a safe placeholder or non-secret default;
- use `${VAR:?message}` for required values when failure at render time is safer than a silent default;
- verify the image supports every target architecture before changing a tag or digest;
- treat moving tags such as `latest` as upgrades, not stable identities;
- review database migrations and downgrade support before changing stateful images.

For supporting assets:

- add them to the relevant `assets` map when `prepare.py` must copy them;
- update `prepare.py` and tests if their file type is not included by its copy rules;
- keep generated files out of Git unless they are intentional deployment inputs.
- keep `.gitignore` runtime-directory rules project-specific; never hide every future project's `data/`, `config/`, or `public/` directory with a wildcard.

### 6. Run repository validation

The minimum repository gate is:

```sh
python3 scripts/check.py
python3 -m unittest discover -s tests
git diff --check
```

`scripts/check.py` renders every declared Compose project with validation-only values. It does not contact hosts, start containers, build images, validate private values, or prove runtime compatibility.

Add the narrow checks required by the change:

- build a changed local image when architecture and build behavior matter;
- run targeted unit tests for scripts or integrations;
- validate JSON/YAML/application syntax with the owning tool;
- check local Markdown links and route/index coverage when docs change;
- run the `stashfleet` test, lint, and build workflow when changing that package.

### 7. Build the exact deployment payload

Use a new temporary directory:

```sh
homelab_stage=$(mktemp -d)
python3 scripts/prepare.py PROJECT "$homelab_stage/PROJECT"
```

Never point `prepare.py` at an installed project. It is deliberately overwrite-resistant.

Compare the staged non-secret files with the installed project. Preserve host-only private files and documented overlays. Do not copy an entire project tree blindly, use `rsync --delete`, or synchronize the whole `/opt` tree.

### 8. Synchronize safely

For each mapped host:

1. Reconfirm the destination and current file checksum.
2. Copy only the intended files to a temporary path on that host.
3. Preserve or set the required owner and mode.
4. Validate the staged files on the host.
5. Replace the destination atomically when practical.
6. Retain a rollback copy until runtime verification passes.

Do not overwrite `.env`, secrets, databases, certificate directories, named-volume contents, or application data with repository examples.

Use [`docker-compose/update.sh`](docker-compose/update.sh) in preview mode when its pull/build/up sequence fits the task:

```sh
bash docker-compose/update.sh /opt/example-project
```

Review the output before using `--apply`. The helper updates the installed project; it does not copy repository files to the host, create backups, handle migrations, or verify the application.

### 9. Apply the smallest runtime change

Run `docker compose config --quiet` from the installed project with its real private inputs. Do not print the rendered configuration.

Restart or recreate only the affected services. Avoid `docker compose down` when `up -d` can apply the change without tearing down the whole project. Never add `-v`.

For a local build, verify the built image and the running container both use the intended architecture and code. For image-only changes, record the post-update image ID.

### 10. Verify runtime behavior

Use every layer that applies:

1. `docker compose ps` shows expected containers without restart loops.
2. Recent logs show no migration, permission, authentication, dependency, or storage errors.
3. The direct LAN endpoint returns the expected application or authentication behavior.
4. The public endpoint works through DNS, Cloudflare when enabled, TLS, and NPM.
5. The application can read existing state and complete one harmless representative operation.
6. Monitoring, delivery, indexing, sync, VPN, or backup jobs produce a real outcome when relevant.

A healthy container, open TCP port, HTTP login page, Homarr tile, or NPM “Online” badge is only one layer of evidence.

### 11. Prove parity

Use the appropriate parity model:

| Configuration type | Required parity proof |
| --- | --- |
| Checked-in files copied to a host | SHA-256 or byte comparison of the repository/staged file and installed file |
| `.env.example` versus private `.env` | Required key/schema compatibility without exposing or comparing private values |
| Host-specific generated/override file | Normalized semantic diff plus documented reason for host-only values |
| NPM or another UI-managed configuration | Field-by-field semantic comparison with the checked-in sanitized reference |
| Replicated project | Per-host checksum/config/runtime evidence for every host in the manifest |
| Home Assistant OS app | Repository package version, installed app version, configuration, health, and runtime behavior |

Hash only non-secret files. Do not place private values into a comparison artifact or final report.

If live drift is found:

- stop before overwriting unknown or broader changes;
- classify it as private input, expected host overlay, stale host copy, or untracked configuration;
- backport the sanitized intended state into the repository first;
- validate, deploy, and re-check parity.

An emergency host fix must be represented in the repository during the same task. If that is impossible, report the host as drifted and the task as incomplete.

## Project-specific rules

### Nginx Proxy Manager and routes

- `configs/nginx/routes.json` is the sanitized route reference, not an import file.
- A route change must update the repository reference, the live NPM entry, and the relevant inventory/application documentation.
- Compare domains, scheme, destination, port, certificate choice, access list, WebSocket behavior, and advanced configuration.
- Validate the backend directly from `rpiproxy` and through the public URL.
- NPM “Online” does not establish backend health.
- Preserve `/opt/nginx/data` and `/opt/nginx/letsencrypt` as one recovery set.

### Nginx, Fail2ban, and Cloudflare

- Sync checked-in Nginx and Fail2ban assets only to `rpiproxy`.
- Validate Nginx syntax before reload and confirm its custom include paths still exist.
- Run repository tests for Fail2ban Python actions and filters before host deployment.
- Preserve private credentials, protected networks, the Fail2ban database, and the Cloudflare ownership journal.
- Do not flush existing bans or modify unrelated firewall/Cloudflare rules as a side effect of configuration deployment.
- A Cloudflare write is external state; limit it to the exact rule behavior requested and verify ownership before removal.

### Dozzle

- `rpimon` runs the central server with its local Docker socket.
- `dozzle-agent` is a replicated project; use the current `hosts` list in `deployments.json` rather than a remembered list.
- `rpihass` uses `home-assistant-dozzle-agent` instead of the normal Compose agent.
- Keep agent port 7007 on the trusted LAN and retain TLS. Do not restore unauthenticated Docker TCP port 2375.
- Preserve per-host `DOZZLE_AGENT_BIND_IP` and `DOZZLE_HOSTNAME` values.
- Verify every host appears, per-host container totals reconcile with Docker, and at least one log stream opens from each non-empty host.

### Homarr

- Treat the Compose file, Dockerfile, override, compatibility patch, and sanitized board configuration as one change set when they depend on each other.
- Keep every copied asset listed in `deployments.json`.
- Preserve the live private environment and Homarr data directories.
- Build and inspect the local image before replacing a working container.
- Verify the board, public and LAN links, widgets, qBittorrent authentication, and container health separately.

### Home Assistant OS app

- When runtime or package metadata changes under `home-assistant-dozzle-agent/`, bump the version in `config.yaml`.
- Validate `config.yaml`, the Dockerfile, supported architectures, watchdog, Docker API requirement, and user-facing `DOCS.md` together.
- Host installation may depend on a committed and pushed repository version. If publication is required and the user did not request commit/push, stop and report that host parity cannot yet be completed.
- Do not change Protection mode, install/update the app, or restart Home Assistant outside the exact requested scope.

### Stateful database applications

Planka and Firezone use PostgreSQL. Paperless, NPM, Vaultwarden, Uptime Kuma, File Browser, FBN, and other applications may keep SQLite or application-managed state.

- Use database/application-consistent backups.
- Preserve application files and database state from the same logical point.
- Record the current schema/application version.
- Do not test rollback by starting an older image against a migrated production volume.
- Verify existing records and representative attachments/documents after deployment.

### Media services

Before changing Plex, qBittorrent/Gluetun, File Browser, or Reelname, verify that `/mnt/media2` and `/mnt/media3` are the intended mounted filesystems. An empty mount point can look like deleted data.

Keep qBittorrent inside Gluetun's network namespace. Verify the VPN path before starting transfer traffic. Back up application configuration separately from bulk media.

### VPN services

Firezone and WG-Easy both default to UDP 51820 on the VPN host. Confirm the current port owner before starting either project. A working management page does not prove a client handshake, forwarding, DNS, or private-resource access.

### Homebridge

`deployments.json` currently has no asserted installed directory for Homebridge. Do not deploy or invent a path until the exact live location and update method are verified.

## Secrets and sanitization

- Never commit passwords, tokens, cookies, session exports, private keys, SMTP credentials, API credentials, personal allowlists, live databases, or rendered production configuration.
- Use `example.com`, TEST-NET addresses, and explicit placeholders in public examples.
- Keep private `.env` and application secret files on the appropriate host or approved secret store.
- When adding a private input, update the example/schema and documentation in Git, then set the real value only on the target host.
- Avoid commands or logs that echo secrets. Capture only the minimal status needed for evidence.
- Run a focused privacy scan before commit or publication.

## Documentation synchronization

Update documentation in the same task when behavior changes:

| Change | Documentation |
| --- | --- |
| Host/project placement | `README.md`, `docs/architecture.md`, `docs/inventory.md`, `deployments.json` |
| Ports or public routes | `docs/inventory.md`, service page, `configs/nginx/routes.json`, live NPM |
| Private inputs or persistent state | `docs/configuration.md` and service page |
| Update, backup, recovery, or verification procedure | `docs/operations.md` and service page |
| New or removed service | `docs/apps/README.md` and all relevant top-level diagrams/tables |
| Observed live status | Include the observation date and distinguish configuration state from application health |

Do not publish raw LAN addresses, secret values, or stale live-status claims. Link every new Markdown page from an index and validate local links.

## Git rules

- Work in the current checkout unless the user asks for a branch or worktree.
- Preserve unrelated user changes in a dirty worktree.
- Do not use `git reset --hard`, `git checkout --`, force push, or destructive cleanup.
- Do not commit or push unless explicitly requested.
- When asked to commit, stage only the intended repository files.
- When asked to publish, verify the remote branch points to the new commit and report what remains uncommitted.

## Completion report

For every configuration task, report:

- repository files changed;
- target host or hosts and installed paths;
- backup or snapshot created;
- host files synchronized;
- parity method and result;
- repository validation commands and results;
- runtime/application verification;
- restart, recreate, migration, or downtime performed;
- any target not synchronized or check not completed.

Do not call the task complete when host synchronization or runtime verification is pending.

## Stop conditions

Stop and request direction when:

- the target host/path is absent, `null`, ambiguous, or conflicts with live state;
- the host contains unknown in-scope drift that could be overwritten;
- a required secret or private overlay is missing;
- a stateful change lacks a usable backup or rollback plan;
- an image, migration path, or target architecture is uncertain;
- synchronization would require deletion, broad recursion, host-wide restart, firewall expansion, account/permission changes, or unrelated external writes;
- one of several replicated targets cannot be brought to parity;
- verification fails and the documented rollback is unsafe or unavailable.

When in doubt, preserve state, leave the service running, and report the exact unmet condition.
