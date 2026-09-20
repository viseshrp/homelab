# PairDrop

PairDrop transfers files and text between browsers using WebRTC, with its server used for discovery and signaling.

## My setup

PairDrop runs on `rpihass` as a Home Assistant OS app from the third-party `https://github.com/jdeath/homeassistant-addons` repository. [`pairdrop.json`](../../configs/homeassistant/pairdrop.json) records the repository, installed app version, image identity, architecture, network policy, and storage access.

The app uses the LinuxServer PairDrop image on `aarch64`. Start on boot is enabled and automatic app updates are disabled. The Home Assistant sidebar opens the authenticated ingress view. LAN clients can also use `http://rpihass:3000`; port 3000 has no separate Home Assistant login, so keep it on the trusted LAN. There is no Nginx Proxy Manager route or dedicated Cloudflare hostname for PairDrop. Remote administrators can reach the ingress view through the existing authenticated Home Assistant route.

The package maps Home Assistant's `/share` directory read-write even though normal PairDrop transfers move directly between browsers and are not stored there. Treat the package as trusted third-party code and do not use it to expose `/share` publicly.

## State and recovery

PairDrop has no configured server-side account or transfer database in this deployment. Device pairings, display names, and interface preferences live in each browser. Reinstall the same repository and app version after restoring Home Assistant; browser-local pairing state is outside the Home Assistant backup.

## Verify

Check the app status and logs, the authenticated ingress view, and the direct LAN page. Open PairDrop in two separate browser contexts, confirm that each sees the other, send a harmless text message and file, and verify the received contents. An HTTP response or two visible peers alone does not prove that the WebRTC transfer path works.

Observed on 2026-09-12: the protected app was running version 1.11.2 on `aarch64`, the authenticated ingress panel and LAN port 3000 loaded PairDrop, two isolated browser contexts discovered each other, and both a text message and a 43-byte file completed end to end. The receiver downloaded the transferred file successfully.

[Home Assistant](home-assistant.md) · [Operations](../operations.md) · [Application index](README.md)
