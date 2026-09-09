# Home Assistant

Home Assistant is the home-automation interface for integrations, automations, scripts, and scenes.

## My setup

The web interface is on `rpihass:8123`, with a shortcut on the Homarr board.

The local configuration includes default integrations, Google Translate text-to-speech, FFmpeg, Wake-on-LAN, sun information, and ping-based presence sensors.

## Configuration files

`configs/homeassistant/configuration.yaml` loads separate files for automations, scripts, scenes, and customization, plus a directory of themes.

It also configures forwarded-header handling and trusted proxy sources. Presence-sensor addresses and proxy networks use `!secret` references. Fill `secrets.yaml` from the example and retain the existing included files.

[Setup](../configuration.md) · [Back to homelab](../../README.md)
