# GitHub Actions runner

The self-hosted GitHub Actions runner builds and publishes the Hugo blog on the application host.

## My setup

The runner's Compose project is `/opt/gh-runner` on `rpiblog`. It uses `myoung34/github-runner` and restarts automatically.

| Mount | Purpose |
| --- | --- |
| Docker socket | Container operations from jobs |
| `/tmp/runner` | Runner workspace |
| `/opt/blog` | Blog deployment directory |

Repository registration, runner labels, and the registration token are supplied through private environment settings.

## Blog workflow

The blog's publish workflow targets `self-hosted` and starts through manual dispatch. It builds the static site with Hugo and copies the result into `/opt/blog`.

The runner and web server share the deployment directory, so publication does not require copying the site to another machine.

## Verify and recover

Confirm the runner is registered and idle, then run the manual blog workflow and verify the generated site through Nginx. A runner shown as online does not prove its labels, submodules, Hugo toolchain, Docker access, or `/opt/blog` permissions are correct.

The registration token is replaceable; the source repository and workflow are authoritative. Treat Docker-socket access and the writable blog mount as host-level deployment privileges.

[Compose](../../docker-compose/gh-runner/docker-compose.yml) · [Operations](../operations.md) · [Application index](README.md)
