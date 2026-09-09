# Homebridge

Homebridge connects compatible plugins and devices to Apple HomeKit.

## My setup

Homarr's Homebridge shortcut targets `rpihass:8581`. The local Compose configuration uses `oznu/homebridge` with host networking and automatic restart.

Its persistent directory comes from the Home Assistant supervisor tree:

```text
/mnt/data/supervisor/homeassistant/homebridge → /homebridge
```

## Bridge data

The `/homebridge` directory holds plugin configuration and pairing state. Keeping it outside the container lets that state survive container replacement.

HomeKit pairing details and plugin credentials remain private.

## Verify and recover

Check the port 8581 interface, loaded plugins, bridge status, and one representative accessory from HomeKit. A reachable administration page does not prove that pairing data or plugin connections work.

The configured `HOMEBRIDGE_DATA_DIR` is the recovery unit. Preserve its ownership, pairing state, plugin configuration, and credentials; do not initialize a new empty directory over a retained bridge.

[Compose](../../docker-compose/homebridge/docker-compose.yml) · [Operations](../operations.md) · [Application index](README.md)
