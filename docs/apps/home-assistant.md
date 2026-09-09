# Home Assistant

Home automation endpoint, with repository configuration for integrations and reverse-proxy awareness.

[Homelab index](../../README.md) · [Architecture](../architecture.md) · [Inspection record](../inventory.md)

## Observed setup

Port 8123 returned HTTP 200, while SSH port 22 refused the connection. No remote filesystem on this host was inspected.

Host association: `rpihass`.


## Recreate the setup

1. Use an installation method appropriate to the target host. The current host installation method was not verified.
2. The saved configuration enables default integrations, Google Translate TTS, FFmpeg, Wake-on-LAN, sun data, and includes for automations, scripts, scenes, themes, and customization.
3. If placing it behind a proxy, configure forwarded-header handling and trust only the intended proxy sources. The repository has trusted-proxy configuration, but it was not verified against the live instance.
4. Recreate device-presence sensors with your own private device inventory. Provide the referenced automation, script, scene, theme, and customization files.

These are owner-run setup instructions; no deployment command was executed during documentation. Pin compatible versions and supply private values before starting a new instance.

## Data and recovery

Use an owner-run Home Assistant backup that includes its actual configuration and state. The small checked-in YAML files are not a complete recovery archive.

## Verification and troubleshooting

HTTP reachability and SSH access are independent. The dashboard has a Home Assistant hostname shortcut, but that hostname is absent from the nine inspected NPM proxy rows. Its routing path remains unverified.

## Deployment notes

The saved configuration includes private device-presence details, which are omitted here. Home Assistant OS/Supervised installation mode, add-ons, and automations were not confirmed.

Related: [Homebridge](homebridge.md).
