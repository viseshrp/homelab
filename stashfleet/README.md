# Stashfleet

A pip-installable Python library and CLI for parallel server-to-client folder backups.
Each successful run produces **one ZIP** containing every configured folder. Google Drive
(or another configured rclone remote) is an optional second destination.

**Initial implementation. Real SSH and Google Drive transfers have not been validated.**
Tests and the demo use local fixtures and fake processes only.

## Install and try without servers

Requires Python 3.11+ on Linux or macOS. From this directory:

```sh
python3 -m pip install -e .
stashfleet demo --directory /tmp/stashfleet-demo
```

Use a new demo directory each time. The demo creates two local source folders, backs them
up, builds a real ZIP, and copies it to a `fake-cloud/` directory. It never runs SSH or
rclone, reads your SSH settings, or connects to any server or cloud account.

The library has only two runtime Python dependencies: Click and Rich. Real transfers
require **rclone and OpenSSH installed separately**. The Python package does not download
executables, authenticate cloud accounts, or install timers automatically.

## Configure a real run

```sh
cp examples/backup.toml backup.toml
# Edit backup.toml before any real run.
stashfleet run --config backup.toml --dry-run
stashfleet doctor --config backup.toml
```

Both commands above are offline: dry-run prints a plan; doctor checks configuration,
executable presence, and explicit key/config file existence. Neither proves connectivity,
authentication, permissions, binary-version compatibility, or available storage.

`--dry-run` previews the pull commands, ZIP path and compression, optional cloud upload,
and retention policy. It does not require rclone to be installed and does not inspect remote
files or calculate exact changes/deletions. `<run-id>` is a placeholder, not a created run.
Add `--json-events` for a single machine-readable plan:

```sh
stashfleet run --config backup.toml --dry-run --json-events
```

After you have tested access yourself:

```sh
stashfleet run --config backup.toml
stashfleet status --config backup.toml
stashfleet retry-upload RUN_ID --config backup.toml
```

`--parallel-hosts N` overrides the TOML concurrency setting. Other settings are in TOML.
Use `--plain` for scheduled logs or `--json-events` for machine-readable progress and results.
An unsuccessful run returns exit code 1; invalid command-line usage returns 2.

Paths in TOML resolve relative to the config file; `~` expands for local paths. Remote
source folders must be absolute. Host/job names become ZIP directory names and must be
unique ignoring case. Invalid or unknown configuration fields fail before transfers.
The example documents all options. No environment-specific hosts or credentials are bundled.

## Flow and recovery

1. Acquire an OS lock on the destination and create a new run directory.
2. Pull at most `parallel_hosts` servers at once, processing each host's jobs sequentially.
   Each rclone process permits `transfers` concurrent files. Compression runs in a worker
   thread; transfer subprocesses and progress are coordinated by asyncio.
3. If **every pull succeeds**, stream all folders into one ZIP and rename the completed
   temporary ZIP atomically. A source-set manifest is included inside the ZIP.
4. If cloud is enabled, upload that ZIP. Record success only after rclone exits successfully.
5. Apply explicit retention settings and save the final result.

Local layout:

```text
backups/
  .lock
  history/<run-id>.json
  runs/<run-id>/
    data/
      manifest.json
      server_a/configuration/...
      server_b/documents/...
    stashfleet-<run-id>.zip
```

Each run uses fresh directories and therefore **performs full pulls**, not incremental
snapshots. This avoids stale files from previous runs entering the ZIP, at the cost of
network traffic and disk space. Budget for the uncompressed data plus the ZIP for each
retained run. Files which change during the same run still require source-side coordination.

An exhausted pull failure does not stop independent jobs, but prevents ZIP creation and
cloud upload. Partial local data remains for inspection. A later `run` starts a new backup.
Transient transfer errors get bounded retries with exponential backoff. Configuration and
programming errors are not retried. Process output is drained continuously; cancellation
and timeouts terminate rclone's process group, including its external SSH children.

A failed or interrupted upload leaves `cloud_pending` state and the existing ZIP.
`retry-upload` validates its SHA-256 before reusing it, without contacting source hosts.
Keep the original cloud destination in the config for retries. A repeat upload uses the
same cloud filename with rclone's immutable option; it will not overwrite a different ZIP.
After a hard kill during upload, the already-saved pending state can still be retried.
Hard kills during pulls/archiving may leave unfinished data or `.partial` files for manual
inspection. The OS releases the lock when the process exits.

## ZIP settings and scope

| Compression | Level | Notes |
| --- | --- | --- |
| `deflate` (default) | 0–9, default 6 | Broad ZIP reader compatibility |
| `store` | Omit | No compression |
| `bzip2` | 1–9, default 9 | Requires a reader supporting BZIP2 ZIP entries |
| `lzma` | Omit | Requires a reader supporting LZMA ZIP entries |

ZIP64 is enabled for large archives. ZIP creation streams files rather than loading them
into memory; progress measures uncompressed bytes processed. Deflate/BZIP2 compression
levels are passed to the ZIP writer. LZMA's ZIP API does not expose a configurable level.

This is a **regular-file/folder backup**, not a bootable system image. Rclone SFTP copies
do not guarantee preservation of Linux owners, ACLs, extended attributes, special files,
or links. Symlinks are not followed by the default transfer. The ZIP builder refuses
symlinks and special files if a replacement backend supplies them. Empty folders are included.
Prepare consistent database exports yourself; live database snapshot/export hooks are not
implemented in v1. Restore requires downloading (and decrypting, if applicable) the ZIP,
checking it, and extracting it with a compatible ZIP reader. Perform a restore trial before
relying on this for recovery.

## Google Drive and credentials

Configure an rclone remote yourself with `rclone config`; use a dedicated backup destination.
Set `cloud.enabled = true` and `cloud.destination = "gdrive:stashfleet"` in TOML. Stashfleet
uploads the ZIP unchanged and uses rclone's transfer checks. It does not do a full read-back
of cloud contents after upload. The local SHA-256 protects the retry input.

To encrypt cloud contents and filenames, configure an **rclone crypt remote** over Drive
and use that remote instead. The ZIP itself is not password-encrypted. Keep the crypt key
and Google authorization credentials outside the repository; preserve a recovery copy of
the crypt key. Follow [rclone's Drive setup](https://rclone.org/drive/) for OAuth requirements
and [crypt documentation](https://rclone.org/crypt/) for encryption setup.

SSH uses the external OpenSSH binary so normal SSH aliases/configuration are honored.
TOML user and port override SSH defaults; `ssh_config` selects a config file. An explicit
identity adds that key and enables `IdentitiesOnly` (keys listed in SSH config can still
apply). Batch mode and strict known-host checks are always enabled. Verify host keys before
scheduling. Encrypted keys must be usable noninteractively (for example via an agent).
Stashfleet never installs keys or disables host verification.

## Retention

Both retention counts default to **0 (keep everything)**. Setting a positive count explicitly
enables deletion: `keep_local` keeps the newest N completed run directories; `keep_cloud`
keeps the newest N recorded uploaded ZIPs at the current cloud destination. Unfinished runs
and pending uploads are never pruned automatically. Inspect and remove those yourself.

Cloud pruning deletes exact filenames recorded by this installation, never a wildcard,
directory, or unrelated Drive file. It does not discover backups created by another client.
History manifests remain after data pruning. Preserve history alongside the backup root
if moving clients. Retention errors return a failed exit status even when the new backup
itself is complete. A new run will retry eligible cleanup.

## Schedule with systemd

Edit the user, paths and schedule in `examples/systemd/`, then install on your **Linux client**:

```sh
sudo cp examples/systemd/stashfleet.service examples/systemd/stashfleet.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now stashfleet.timer
systemctl list-timers stashfleet.timer
journalctl -u stashfleet.service
```

The example runs around 02:00 in the system timezone with up to five minutes of jitter.
`Persistent=true` catches up a missed calendar activation. Systemd prevents overlapping
activations of the service; the application lock also covers manual invocations using the
same backup destination. Configure SSH, rclone authorization, and filesystem permissions
for the service user. Use absolute binary paths in TOML if systemd's PATH differs from your
shell. macOS users can invoke the same one-shot command through launchd. No Python scheduler
or background daemon is included.

## Library and replaceable dependencies

```python
import asyncio
from stashfleet import Runner, load_config


async def backup():
    runner = Runner(load_config("backup.toml"), emit=lambda event: print(event))
    result = await runner.run()
    return result.success


asyncio.run(backup())  # The calling application owns the event loop.
```

`Runner(config, backend=..., archiver=..., emit=...)` accepts injected implementations.
`Backend` defines `validate`, async `pull`, async `upload`, and async `delete`.
`ArchiveBuilder` defines a synchronous, cooperatively cancellable `build` method.
`Event` is independent of Rich. Callbacks execute on the event loop and should be quick
and non-throwing. The library performs no printing and does not start an event loop.
`stashfleet.demo.FakeBackend` provides a local fixture implementation; its excludes support
simple glob matching, not the full rclone filter language. No Fabric dependency is required.

## Development and packaging

```sh
uv sync --group dev
uv run pytest
uv run ruff check .
uv build
```

Tests never contact real servers or cloud accounts. They inject fake backends and a fake
rclone executable for process/progress/cancellation tests. The ZIP and filesystem operations
are real, inside temporary directories. `uv.lock` pins the local development environment;
the distribution declares compatible Click/Rich ranges for downstream installs.

This folder is self-contained: copy it to its own repository without its parent homelab
repository. Wheels and source distributions are built from `pyproject.toml`. Nothing here
has been published to PyPI.
