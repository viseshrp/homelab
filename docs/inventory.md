# Inspection record

[Homelab index](../README.md) · [Architecture](architecture.md)

Snapshot: **2026-09-09, America/New_York**. Checks were made from the owner’s workstation. Private addresses and personal DNS names are replaced with host aliases. This file records a bounded inspection, not a continuous monitor.

## Sources and scope

| Source | Read | Limit |
| --- | --- | --- |
| Workstation `/etc/hosts` | Eleven non-loopback homelab aliases | Historical entries can remain after a host moves |
| Workstation SSH configuration | Wildcard identity configuration | No additional hostname/IP mapping was present; key contents were not read |
| Current repository | Compose/configuration files, scripts, existing Stashfleet guide | Source for components whose host deployment was not accessible |
| SSH as the requested account | Directory listings and selected setup files under `/opt` | No sudo, writes, runtime Docker queries, logs, databases, private environment files, or filesystem reads outside `/opt` |
| Existing in-app browser tabs | NPM proxy table and Homarr board/sidebars | No configuration changes, new routes, downloads, or app logins |

SSH used noninteractive authentication, strict known-host verification, bounded connection timeouts, and disabled forwarding. Selected remote file reads checked that resolved paths stayed under `/opt`. Directory discovery did not follow symlinks. Permission denials were retained without escalation on the hosts.

The first workstation-sandbox network attempts were blocked locally. The results below came from the subsequently permitted network checks, so local sandbox errors are not classified as host failures.

## Hosts discovered in the local aliases

| Host | SSH result | `/opt` evidence / other response |
| --- | --- | --- |
| `rpiblog` | Connected | Blog, runner, Anki, Vaultwarden, Planka, Linkding, Homarr, FBN definitions |
| `rpihass` | Connection refused | HTTP 8123 returned 200; no remote directories read |
| `rpihole` | Connected | Pi-hole definition; DNS TCP 53 accepted a connection |
| `rpimon` | Connected | Kuma, Paperless, ArchiveBox/pywb, Dozzle definitions |
| `rpinfs` | Connected | FTP definition; FTP port 21 refused |
| `rpipass` | Connection refused | No remote directories read; current Vaultwarden route uses `rpiblog` |
| `rpiproxy` | Connected | NPM and Fail2ban definitions; proxy admin browser UI available |
| `rpivpn` | Timed out | No remote directories read; distinct from the additional VPN target below |
| `rpizwcal` | Timed out | Role not established from the name |
| `rpiz2w` | Timed out | Role not established from the name |
| `optiplex` | Connected | Plex, qBittorrent/Gluetun, File Browser definitions; Reelname installed |

## Additional browser destinations

| Documentation label | Discovery source | Result |
| --- | --- | --- |
| `vpn-edge` | NPM Firezone backend | SSH connected; `/opt/firezone` and `/opt/wg-easy` found; management 13000/51821 and web 80/443 refused |
| `archive-legacy` | Homarr ArchiveBox/Paperless shortcuts | SSH and checked app ports 8000/8002 timed out |

There were **13 distinct host addresses** across the local aliases and these browser destinations. Seven authenticated SSH sessions succeeded. Refusal means the attempted service rejected a connection; a timeout can result from an offline host, filtering, a changed address, or a routing problem. Neither establishes a permanent host state.

The scan covered host aliases and destinations in the two live browser pages. It did not expand to personal devices mentioned in configuration files.

## Targeted application checks

HTTP checks requested `/` without following redirects or logging in. Status alone does not verify application identity or function; app labels below are based on the corresponding Compose definition or browser route. TCP-only checks are identified explicitly.

| Host | Port / application association | Result |
| --- | --- | --- |
| `rpiblog` | 80 · static site | HTTP 200 |
| `rpiblog` | 8080 · Anki | HTTP 404 |
| `rpiblog` | 3001 · Planka | HTTP 200 |
| `rpiblog` | 7575 · Homarr | HTTP 307; existing board rendered |
| `rpiblog` | 9090 · Linkding | HTTP 302 |
| `rpiblog` | 8089 · Vaultwarden | HTTP 200 |
| `rpihass` | 8123 · Home Assistant | HTTP 200 |
| `rpihass` | 8581 · Homebridge shortcut | Refused |
| `rpihole` | 53 · DNS | TCP connection accepted; no DNS query |
| `rpihole` | 80 · web root | HTTP 403; `/admin` not separately tested |
| `rpimon` | 3001 · Kuma | HTTP 302 |
| `rpimon` | 8080 · Dozzle | HTTP 307 |
| `rpimon` | 8000 · Paperless | Refused |
| `rpimon` | 8002 · ArchiveBox | HTTP 302 |
| `rpimon` | 8082 · pywb | HTTP 200 |
| `rpinfs` | 21 · FTP | Refused |
| `rpiproxy` | 80 · default HTTP host | HTTP 404 |
| `rpiproxy` | 443 · HTTPS | TCP connection accepted; no separate certificate test |
| `rpiproxy` | 81 · NPM admin | HTTP 200; existing proxy table rendered |
| `optiplex` | 32400 · Plex | HTTP 401 |
| `optiplex` | 8080 · File Browser instance 2 | HTTP 200 |
| `optiplex` | 8081 · File Browser instance 3 | HTTP 200 |
| `optiplex` | 8085 · qBittorrent | HTTP 200 |
| `vpn-edge` | 13000 · Firezone management | Refused |
| `vpn-edge` | 51821 · WG-Easy management | Refused |
| `vpn-edge` | 80 / 443 | Refused |
| `archive-legacy` | 8000 / 8002 | Timed out |

HTTP 200 means a response arrived, not that authenticated workflows succeeded. Redirects can lead to login or another path. HTTP 401/403 can be expected access control; a 404 at `/` can be expected for an API or host-routed server.

No UDP scan, DNS resolution test, VPN handshake, torrent transfer, Plex playback, document import, database query, FTP login, or notification delivery test was performed.

## Unread and unverified

Permission denied on selected Linkding and Kuma data directories and a container-runtime directory; no permissions were changed. Application data, secrets, cookies, certificate files, and logs were not opened. `/opt` files that mention `/mnt`, `/var`, `/home`, or `/etc` supplied configuration declarations only; those remote destinations were not read.

A named volume can hold the actual data outside `/opt`, and an installed Python environment does not prove a running service. No runtime image digests, service uptime, scheduler configuration, mount source, storage capacity, hardware model, router rules, or successful backup/restore was inferred.

## Repeat the bounded host check

Use a host alias from your private inventory and your own account. This example lists immediate directories without reading application state or following symlinks:

```sh
ssh -o BatchMode=yes -o StrictHostKeyChecking=yes \
  -o ClearAllForwardings=yes -o ConnectTimeout=5 operator@host-alias \
  'cd /opt && find -P /opt -mindepth 1 -maxdepth 1 -type d -print'
```

Verify host keys through a trusted channel before use. Do not suppress verification to make an inventory succeed. Select specific setup files for any further reads; do not recursively dump `/opt`, where credentials and application data also live.
