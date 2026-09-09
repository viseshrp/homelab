# Reelname

Reelname is a Python command-line tool for fixing media filenames.

## My setup

Reelname 2.0.4 is installed in a Python 3.10 environment at `/opt/reelname` on `optiplex`, alongside Plex and qBittorrent.

The package uses Cinemagoer for media information, RapidFuzz for matching, and Watchdog for filesystem events.

## Command line

The installed entry point is:

```sh
/opt/reelname/bin/reelname --help
```

Reelname works on media files directly; it has no web port or Nginx Proxy Manager route.

[Back to homelab](../../README.md)
