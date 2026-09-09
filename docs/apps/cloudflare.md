# Cloudflare integration

External integration referenced by the homepage and Fail2ban’s configured ban action.

[Homelab index](../../README.md) · [Architecture](../architecture.md) · [Inspection record](../inventory.md)

## Observed setup

The dashboard contains a Cloudflare link, and the inspected Fail2ban jail selects `cloudflare-apiv4`. The Cloudflare account, DNS records, edge proxy mode, and API action results were not accessed.


## Recreate the setup

1. Use your own zone and deliberately choose how application names resolve to the lab’s ingress.
2. If enabling the Fail2ban action, provide a narrowly scoped private credential and the identifiers required by that action.
3. Configure origin TLS, forwarded-client-IP handling, and router exposure to match your chosen DNS/proxy mode.
4. Validate the public path from an external network. Browser access from this workstation does not establish the router or edge configuration.

These are owner-run setup instructions; no deployment command was executed during documentation. Pin compatible versions and supply private values before starting a new instance.

## Data and recovery

Keep DNS/routing configuration and recovery access privately. Never publish the account-specific dashboard URL or action credentials.

## Verification and troubleshooting

Distinguish DNS resolution, edge handling, origin TLS, NPM routing, and app availability. A Cloudflare bookmark alone is evidence of none of those settings.

## Deployment notes

The architecture diagram therefore marks the uninspected upstream edge as an unknown boundary rather than asserting Cloudflare is in every request path.
