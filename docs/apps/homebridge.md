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

[Back to homelab](../../README.md)
