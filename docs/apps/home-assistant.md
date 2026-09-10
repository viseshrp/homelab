# Home Assistant

Home Assistant is the home-automation interface for integrations, automations, scripts, and scenes.

## My setup

The web interface is on `rpihass:8123`, with a shortcut on the Homarr board. The public `hass.<domain>` endpoint reaches the same service through the dedicated Cloudflare Tunnel connector on `rpiproxy`.

The repository also contains a Home Assistant OS Dozzle Agent app. It requires Protection mode to be disabled so Supervisor can grant read-only Docker API access, and it exposes agent port 7007 only to the trusted LAN.

The local configuration includes default integrations, Google Translate text-to-speech, FFmpeg, Wake-on-LAN, sun information, and ping-based presence sensors.

Home Assistant's recommended automatic-backup preset creates an encrypted full backup every day and retains three backups locally. The emergency kit must stay outside the Home Assistant host because it contains the key needed to restore those backups.

HACS is downloaded on Home Assistant OS through the official HACS app repository. [`hacs.json`](../../configs/homeassistant/hacs.json) pins the one-shot **Get HACS** installer app to version 1.3.1. The configured HACS integration uses GitHub device OAuth with read-only access to public account information; its account identity and token remain private. On 2026-09-10, HACS 2.0.5 loaded its repository catalog and sidebar dashboard successfully.

## Configuration files

`configs/homeassistant/configuration.yaml` loads separate files for automations, scripts, scenes, and customization, plus a directory of themes.

Home Assistant 2026.8 and later manage the HTTP server in **Settings > System > Network**, not `configuration.yaml`. [`http-server.json`](../../configs/homeassistant/http-server.json) is the sanitized reference for the UI-managed settings. Enable **Trust X-Forwarded-For** and trust only the tunnel connector's LAN address as a `/32`; the live address remains host-only. Saving these settings restarts Home Assistant and requires an administrator to confirm them within five minutes or Home Assistant restores the previous values.

[`backup-policy.json`](../../configs/homeassistant/backup-policy.json) records the UI-managed automatic-backup policy. It does not contain the encryption key or emergency kit.

Presence-sensor addresses use `!secret` references. Fill `secrets.yaml` from the example and retain the existing included files.

## Verify and recover

Validate retained YAML against the installed Home Assistant version before a restart. For HTTP-server changes, confirm the new settings after the automatic restart, then check the direct LAN UI, public login page, one WebSocket-backed UI update, one automation, one integration, and the ping-based presence sensors; a responsive port does not prove those subsystems loaded.

The checked-in files are sanitized configuration references. Preserve the host-managed Home Assistant state, secrets, included automation/script/scene files, custom integrations, and Supervisor-managed data through the platform's supported encrypted backup path. Before installing or updating a custom integration, create a fresh backup and confirm that it appears as completed in the backup inventory.

[Configuration](../configuration.md#home-assistant-and-kiosk) · [Dozzle Agent app](../../home-assistant-dozzle-agent/README.md) · [Operations](../operations.md) · [Application index](README.md)
