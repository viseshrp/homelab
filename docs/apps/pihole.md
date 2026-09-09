# Pi-hole

Pi-hole filters DNS requests to block unwanted domains across devices that use it as their DNS server.

## My setup

The Compose project is `/opt/pihole-docker` on `rpihole`. It uses `pihole/pihole` with host networking, the `NET_ADMIN` capability, and an automatic restart policy.

Homarr links to its `/admin` interface and includes a widget for DNS query and blocking counters.

## Persistent configuration

| Host directory | Container directory |
| --- | --- |
| `/opt/pihole-docker/etc-pihole` | `/etc/pihole` |
| `/opt/pihole-docker/etc-dnsmasq.d` | `/etc/dnsmasq.d` |

These directories retain Pi-hole and DNS configuration across container replacement. The administration credential is supplied privately.

[Back to homelab](../../README.md)
