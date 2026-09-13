# DIUN Agent

DIUN checks the public Homebridge and PairDrop image channels listed inside this app. It reports digest changes to ntfy and never inspects, pulls, recreates, or changes Home Assistant containers.

## Configuration

Set these private app options before starting:

- `ntfy_endpoint`: the private-LAN ntfy origin, such as `http://192.0.2.14:2586`;
- `ntfy_topic`: the existing private notification topic;
- `ntfy_token`: the unique write-only token created for `diun-rpihass`;
- `hostname`: the label shown in the notification title;
- `timezone`, `schedule`, and `jitter`: the local scan schedule, set by default
  for each six-hour boundary with up to 45 minutes of random delay;
- `notification_test_on_start`: enable only for a supervised one-time delivery test, then disable it and restart the app;
- `log_level`: use `info` normally.

The app uses DIUN's file provider and does not request Supervisor Docker access. It publishes no ports, requests no host networking or Linux capabilities, and uses a cold backup so its bbolt database is quiesced during backup.

Automatic updates and Watchdog are Supervisor-owned switches, not options consumed by DIUN. Record and preserve the operator's choices. Enabling Automatic updates changes only this app package; DIUN remains notification-only for every image it monitors.

## Verification

For first installation, enable `notification_test_on_start`, start the app, confirm the log reports a successful DIUN notification test, then disable the option and restart the app. Do not leave the option enabled: every later restart would send another test. Confirm the phone receives a message labeled `rpihass` and verify that the publisher token cannot read the topic.

After the normal restart, require the app log to show DIUN 4.33.0, the file provider, exactly two image entries, an initialized schedule, and no registry or notification error. The Docker provider must be absent.

Confirm the discovered image list contains only `homebridge/homebridge:latest` and `linuxserver/pairdrop:latest`. The initial scan establishes the bbolt baseline and sends no image notifications. A later digest change sends an update notification only.

## Backup and recovery

Create a Home Assistant full backup before installation or upgrade. The app's `/data/diun.db` is replaceable monitoring state; losing it causes DIUN to rebuild its baseline without first-check notifications. The ntfy token remains a private Supervisor option and must also exist in the restricted ntfy recovery set.

To recover, reinstall the recorded app version, restore the app configuration or enter the private values again, start the app, and repeat the provider, inventory, notification, and ACL checks.
