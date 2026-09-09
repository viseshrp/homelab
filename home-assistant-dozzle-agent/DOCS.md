# Dozzle Agent

This app connects the Home Assistant OS Docker host to the central Dozzle server.

## Installation

1. Install the app from the Visesh Homelab Apps repository.
2. Disable **Protection mode** so Supervisor can grant the app read-only Docker API access.
3. Start the app and enable **Start on boot**.
4. Confirm TCP port 7007 is reachable only from the trusted LAN.

The app does not enable Dozzle actions or shell access. The central Dozzle server remains responsible for user authentication.
