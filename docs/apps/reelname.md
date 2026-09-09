# Reelname

Python command-line tool for fixing media filenames, installed alongside the media stack.

[Homelab index](../../README.md) · [Architecture](../architecture.md) · [Inspection record](../inventory.md)

## Observed setup

`/opt/reelname` is a Python environment. Its package metadata identifies Reelname 2.0.4, a tool to fix media filenames. No command was executed and no media was inspected.

Host association: `optiplex`.


## Recreate the setup

1. Use a dedicated Python environment and retain the intended Reelname version. The inspected environment uses Python 3.10; package metadata declares Python 3.9 or newer.
2. The package’s documented entry point is `reelname`; use its own help to establish the supported commands before operating on files.
3. Choose an explicit media directory and verify rename behavior on copies of disposable files.
4. Coordinate any real rename step with Plex and the download client so neither loses its expected paths. No automation connecting these apps was verified.

These are owner-run setup instructions; no deployment command was executed during documentation. Pin compatible versions and supply private values before starting a new instance.

## Data and recovery

Keep the package version and owner-maintained invocation/configuration. Back up media or maintain a reversible rename record before processing originals.

## Verification and troubleshooting

Package presence does not prove a scheduled watcher exists. Inspect the selected version’s behavior before assuming options from another release.

## Deployment notes

The package metadata lists Click, Cinemagoer, RapidFuzz, Watchdog, and aiofiles dependencies. Process lists, timers, and service files outside `/opt` were not inspected.
