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

## Verify and recover

Query a known domain through `rpihole` over both UDP and TCP, then confirm the request appears in the administration interface. A working web page does not prove clients can resolve DNS.

Back up both configuration directories and the private settings. After a restore, verify custom DNS records, blocklists, client groups, query logging, and the resolver address distributed to clients.

[Compose](../../docker-compose/pihole/docker-compose.yml) · [Operations](../operations.md) · [Application index](README.md)
