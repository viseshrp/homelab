# DIUN Agent Home Assistant OS app

This package runs a file-provider-only DIUN watcher for the Homebridge and PairDrop public image channels. It sends update-only notifications to the homelab ntfy topic, exposes no network port, and cannot update containers.

The app does not request Home Assistant Supervisor's Docker API. Keep the app repository private to the operator workflow, use a unique write-only ntfy token, and never place private endpoint, topic, or token values in Git.

Supervisor owns the app's Automatic updates and Watchdog switches. Preserve the operator's choices when installing or repairing the package. Automatic updates can replace this app package; it does not make DIUN update monitored images.

See [DOCS.md](DOCS.md) for installation, verification, backup, and recovery.
