# Stashfleet

Local backup library and CLI included in this repository. It pulls configured folders over SSH, combines successful pulls into one ZIP, and can upload it to an rclone destination.

[Homelab index](../../README.md) · [Complete installation and API guide](../../stashfleet/README.md)

## Deployment status

The repository contains an initial implementation, tests, a local demo, and scheduling examples. No installation, scheduled backup, real SSH transfer, or cloud upload was verified in the lab. It is therefore outside the diagram’s operational service path.

## Configure a backup client

1. Install the local package with Python 3.11 or newer. Real transfers also need OpenSSH and rclone installed separately.
2. Copy `stashfleet/examples/backup.toml` to a private configuration. Select exact hosts and folders, a local destination, SSH identity/known-host policy, and any authorized cloud destination.
3. Use the offline dry run and doctor before a real run. Neither command proves connectivity, permissions, disk space, or credentials.
4. Coordinate consistent database exports with each app. Stashfleet copies regular files and folders; it does not make live databases consistent or export Docker volumes automatically.

```sh
stashfleet run --config backup.toml --dry-run
stashfleet doctor --config backup.toml
```

## Storage and recovery

Each run performs full pulls and needs room for the data plus the ZIP. Any failed pull prevents archive publication and upload; a failed upload leaves a ZIP that can be retried. Retention defaults to keeping everything; positive counts enable deletion. Source folders, named volumes, and external media mounts require explicit coverage.

Restore by obtaining the ZIP, validating it, and extracting into an isolated recovery location. Confirm database consistency and ownership before using the restored files. The package does not promise Linux ownership, ACL, extended-attribute, or special-file preservation.

Use an rclone crypt destination if cloud contents need encryption. The produced ZIP itself is not encrypted. Keep SSH keys, cloud authorization, and crypt recovery keys outside the repository.

## Limits relevant to this lab

An `/opt`-only source selection would miss Docker-managed volumes and media stored elsewhere. Planka, Paperless, Firezone, and FBN require application-specific recovery planning. The documentation audit did not authorize running Stashfleet against any host, and no backup was triggered.
