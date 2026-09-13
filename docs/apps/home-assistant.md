# Home Assistant

Home Assistant is the home-automation interface for integrations, automations, scripts, and scenes.

## My setup

The web interface is on `rpihass:8123`, with a shortcut on the Homarr board. The public `hass.<domain>` endpoint reaches the same service through the dedicated Cloudflare Tunnel connector on `rpiproxy`.

The repository also contains a Home Assistant OS Dozzle Agent app. It requires Protection mode to be disabled so Supervisor can grant read-only Docker API access, and it exposes agent port 7007 only to the trusted LAN.

The local configuration includes default integrations, Google Translate text-to-speech, FFmpeg, Wake-on-LAN, sun information, and ping-based presence sensors.

The Advanced SSH & Web Terminal app uses the `hassio` account with public-key-only authentication on LAN TCP port 22. Start on boot and Watchdog are enabled; Protection mode remains enabled. Password authentication, SFTP, agent forwarding, remote port forwarding, and TCP forwarding remain disabled.

Home Assistant's recommended automatic-backup preset creates an encrypted full backup every day and retains three backups locally. The emergency kit must stay outside the Home Assistant host because it contains the key needed to restore those backups.

HACS is downloaded on Home Assistant OS through the official HACS app repository. [`hacs.json`](../../configs/homeassistant/hacs.json) pins the one-shot **Get HACS** installer app to version 1.3.1. The configured HACS integration uses GitHub device OAuth with read-only access to public account information; its account identity and token remain private. On 2026-09-10, HACS 2.0.5 loaded its repository catalog and sidebar dashboard successfully.

Google Calendar and Google Nest use separate Google OAuth clients of type **Web application**. Both clients use `https://my.home-assistant.io/redirect/oauth`; client IDs and secrets remain private in Google Cloud and Home Assistant application credentials. [`google-integrations.json`](../../configs/homeassistant/google-integrations.json) records the non-secret OAuth, API, and Pub/Sub contract. Do not use the legacy **TV and Limited Input** client type for new Google Calendar credentials.


## Supervisor apps and image monitoring

On September 12, 2026, Supervisor reported ten installed apps. Homebridge and PairDrop are the only HAOS app families selected for DIUN release notifications. The local DIUN app uses a two-entry file provider instead of Docker discovery, so the remaining apps and Home Assistant internal images cannot generate alerts. [`apps.json`](../../configs/homeassistant/apps.json) records the non-secret inventory and this monitoring policy.

| App | Installed state and version | DIUN notification |
| --- | --- | --- |
| Matter Server | Running, 9.2.0 | Not monitored |
| Advanced SSH & Web Terminal | Running, 24.1.4 | Not monitored |
| Glances | Running, 0.22.1 | Not monitored |
| Dozzle Agent | Running, local package 10.10.0-2 | Not monitored as an HAOS app |
| File editor | Running, 6.1.0 | Not monitored |
| JupyterLab | Running, 0.18.1 | Not monitored |
| Get HACS | Stopped, 1.3.1 | Not monitored |
| Homebridge | Running, 2026-09-02 | `homebridge/homebridge:latest` |
| DIUN Agent | Running, local package 4.33.0-5 | Its file provider checks Homebridge and PairDrop |
| PairDrop | Running, version-v1.11.2 | `lscr.io/linuxserver/pairdrop:latest` |

The HAOS DIUN app checks the stable ARM64 `latest` channels for Homebridge and PairDrop every six hours. It does not inspect the HAOS Docker host or update either app. Supervisor remains responsible for installation and upgrades.

## Configuration files

`configs/homeassistant/configuration.yaml` loads separate files for automations, scripts, scenes, and customization, plus a directory of themes.

Home Assistant 2026.8 and later manage the HTTP server in **Settings > System > Network**, not `configuration.yaml`. [`http-server.json`](../../configs/homeassistant/http-server.json) is the sanitized reference for the UI-managed settings. Enable **Trust X-Forwarded-For** and trust only the tunnel connector's LAN address as a `/32`; the live address remains host-only. Saving these settings restarts Home Assistant and requires an administrator to confirm them within five minutes or Home Assistant restores the previous values.

[`backup-policy.json`](../../configs/homeassistant/backup-policy.json) records the UI-managed automatic-backup policy. It does not contain the encryption key or emergency kit.

[`google-integrations.json`](../../configs/homeassistant/google-integrations.json) records the UI-managed Google integration contract without client IDs, secrets, account tokens, project IDs, or Pub/Sub resource names.

Presence-sensor addresses use `!secret` references. Fill `secrets.yaml` from the example and retain the existing included files.

## Verify and recover

Validate retained YAML against the installed Home Assistant version before a restart. For HTTP-server changes, confirm the new settings after the automatic restart, then check the direct LAN UI, public login page, one WebSocket-backed UI update, one automation, one integration, and the ping-based presence sensors; a responsive port does not prove those subsystems loaded.

The checked-in files are sanitized configuration references. Preserve the host-managed Home Assistant state, secrets, included automation/script/scene files, custom integrations, and Supervisor-managed data through the platform's supported encrypted backup path. Before installing or updating a custom integration, create a fresh backup and confirm that it appears as completed in the backup inventory.

[Configuration](../configuration.md#home-assistant-and-kiosk) · [Dozzle Agent app](../../home-assistant-dozzle-agent/README.md) · [Operations](../operations.md) · [Application index](README.md)
