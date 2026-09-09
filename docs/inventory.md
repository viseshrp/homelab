# Hosts

## Host roles

| Host | Application directories under `/opt` |
| --- | --- |
| `rpiblog` | `blog`, `gh-runner`, `anki`, `vw`, `planka`, `linkding`, `homarr`, `fbn`, `fbn-compose` |
| `rpiproxy` | `nginx`, `fail2ban` |
| `rpimon` | `kuma`, `dozzle`, `archivebox`, `paperless` |
| `optiplex` | `plex`, `qbit`, `filebrowser`, `reelname` |
| `rpihole` | `pihole-docker` |
| `rpinfs` | `ftp` |
| `vpn-edge` | `firezone`, `wg-easy` |

Home Assistant responds on `rpihass:8123`. Its SSH port was closed, so it has no directory listing here.

## Reachability

Checked on September 9, 2026. “Refused” means the port rejected the connection; “timeout” means it did not answer within the check window.

| Host | SSH | Web or service response |
| --- | --- | --- |
| `rpiblog` | Connected | Blog, Anki, Planka, Homarr, Linkding, and Vaultwarden ports answered |
| `rpiproxy` | Connected | HTTP, HTTPS TCP, and NPM administration ports answered |
| `rpimon` | Connected | Kuma, Dozzle, ArchiveBox, and pywb answered; Paperless 8000 refused |
| `optiplex` | Connected | Plex, both File Browser instances, and qBittorrent answered |
| `rpihole` | Connected | DNS TCP 53 and web port 80 answered |
| `rpinfs` | Connected | FTP 21 refused |
| `vpn-edge` | Connected | Firezone 13000 and WG-Easy 51821 refused |
| `rpihass` | Refused | Home Assistant 8123 answered; Homebridge 8581 refused |
| `rpipass` | Refused | — |
| `rpivpn` | Timeout | — |
| `rpizwcal` | Timeout | — |
| `rpiz2w` | Timeout | — |
| `archive-legacy` | Timeout | Paperless 8000 and ArchiveBox 8002 timed out |

`vpn-edge` is the Firezone backend host. `archive-legacy` is the destination used by the dashboard's Paperless and ArchiveBox shortcuts. Addresses stay private.

## Dashboard connections

The ArchiveBox and Paperless shortcuts point to `archive-legacy`; their projects are on `rpimon`. The torrent widget reports no supported client even though qBittorrent's web interface answers on `optiplex:8085`.

Home Assistant has a hostname shortcut on the board, but no corresponding route appears in NPM's proxy-host table. WG-Easy's client DNS setting points to a different address from `rpihole`.

[Back to homelab](../README.md)
