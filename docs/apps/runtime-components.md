# Other `/opt` components

[Homelab index](../../README.md) · [Inspection record](../inventory.md)

The directory inventory included supporting software beyond the app Compose projects. Directory names identify installed artifacts; they do not establish active processes or user-facing services.

| Component | Observed hosts | Evidence and limit |
| --- | --- | --- |
| `containerd` | All seven SSH-accessible hosts | Runtime directories present; no daemon or container state queried |
| `pigpio` | `rpimon`, `rpinfs` | Directory tree present; no GPIO task, hardware, or daemon verified |
| `WidevineCdm` | `rpimon` | Content-decryption component directories present; no browser, kiosk, or media use verified |
| Older FBN environment | `rpiblog` | `/opt/fbn/venv` exists beside the newer Compose project; active installation unverified |

No separate app endpoint or deployment guide can be established from these names alone. Package maintenance, device access, licensing state, and scheduler configuration were outside the inspection. Preserve the relevant host provisioning records privately if these components are needed for recovery.
