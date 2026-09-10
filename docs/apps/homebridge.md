# Homebridge

Homebridge connects compatible plugins and devices to Apple HomeKit.

## My setup

Homebridge runs on `rpihass` as a Home Assistant OS app from `https://github.com/tronikos/home-assistant-addons`. That package uses the official `homebridge/homebridge` image with host networking. The UI is available only on the LAN at `rpihass:8581`, including through Homarr's Homebridge shortcut.

[`homebridge.json`](../../configs/homeassistant/homebridge.json) records the sanitized Supervisor-managed settings. Start on boot and Watchdog are enabled, while automatic app updates are disabled. The retained [Compose template](../../docker-compose/homebridge/docker-compose.yml) is a standalone fallback and is not the live deployment.

The app maps its Supervisor-managed configuration directory into the container:

```text
/addon_configs/0656e7b8_homebridge → /homebridge
```

## Bridge data

The `/homebridge` directory holds plugin configuration, UI accounts, backups, and pairing state. Supervisor keeps it outside the container so that state survives container replacement. The app excludes `node_modules` from Home Assistant backups because installed plugins can be restored from configuration.

HomeKit pairing details and plugin credentials remain private.

## Verify and recover

Check the port 8581 interface, app logs, loaded plugins, bridge status, and one representative accessory from HomeKit. A reachable administration page does not prove that pairing data or plugin connections work.

The Home Assistant backup entry for the Homebridge app is the recovery unit. Preserve its pairing state, plugin configuration, UI account, and credentials. Do not initialize a new empty app configuration over a retained bridge. For the standalone fallback, the configured `HOMEBRIDGE_DATA_DIR` remains the recovery unit.

[Compose](../../docker-compose/homebridge/docker-compose.yml) · [Operations](../operations.md) · [Application index](README.md)
