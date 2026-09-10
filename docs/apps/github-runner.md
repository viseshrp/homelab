# GitHub Actions runner

The self-hosted GitHub Actions runner builds and publishes the Hugo blog on the application host.

## My setup

The runner's Compose project is `/opt/gh-runner` on `rpiblog`. It uses `myoung34/github-runner` and restarts automatically.

| Mount | Purpose |
| --- | --- |
| Docker socket | Container operations from jobs |
| `/tmp/runner` | Runner workspace |
| `/opt/blog` | Blog deployment directory |
| `/opt/gh-runner/runner-config` | Persisted GitHub runner identity and credentials |

Repository registration and runner labels are supplied through private environment settings. GitHub registration tokens expire after one hour, so the token is used only for initial registration or explicit replacement. The image stores the configured runner files in `/opt/gh-runner/runner-config`; normal container restarts reuse that identity with `CONFIGURED_ACTIONS_RUNNER_FILES_DIR` and do not need a token.

`DISABLE_AUTOMATIC_DEREGISTRATION=true` is required when reusing the stored identity. `UNSET_CONFIG_VARS=true` removes setup variables before the runner listener starts. After successful registration, recreate the container with a blank `RUNNER_TOKEN` so the short-lived token is not retained in the container configuration.

The image can instead keep a personal access token in `ACCESS_TOKEN`, or GitHub App credentials, and mint a new registration token at startup. This installation does not do that: jobs can reach the host Docker socket, and the image warns that workflow environment values can be exfiltrated. Persisting the configured identity provides restart durability without leaving a broader GitHub credential in the runner container.

## Blog workflow

The blog's publish workflow targets `self-hosted` and starts through manual dispatch. It builds the static site with Hugo and copies the result into `/opt/blog`.

The runner and web server share the deployment directory, so publication does not require copying the site to another machine.

## Verify and recover

Confirm the runner is registered and idle, then run the manual blog workflow and verify the generated site through Nginx. A runner shown as online does not prove its labels, submodules, Hugo toolchain, Docker access, or `/opt/blog` permissions are correct.

The registration token is replaceable; the persisted identity is the recovery unit for ordinary restarts. If the identity is lost or GitHub removes it, mint a new one-hour token, register once, verify the runner is online, and then blank the token again. The source repository and workflow remain authoritative. Treat the persisted credentials, Docker-socket access, and writable blog mount as host-level deployment privileges.

[Compose](../../docker-compose/gh-runner/docker-compose.yml) · [Operations](../operations.md) · [Application index](README.md)
