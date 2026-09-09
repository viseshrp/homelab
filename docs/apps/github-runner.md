# GitHub Actions runner

Runs the blog’s self-hosted deployment workflow and can write the blog directory.

[Homelab index](../../README.md) · [Architecture](../architecture.md) · [Inspection record](../inventory.md)

## Observed setup

The runner Compose file and the blog workflow’s `self-hosted` target were verified. Runner registration, job history, and current process health were not checked.

Host: `rpiblog`. Definition: `/opt/gh-runner/docker-compose.yml`.

Source file: `docker-compose/gh-runner/docker-compose.yml`.

| Service | Image/build recorded | Network / host ports | Restart |
| --- | --- | --- | --- |
| `worker` | `myoung34/github-runner:latest` | Compose network; no host mapping declared | `always` |

| Service | Declared storage mapping |
| --- | --- |
| `worker` | `/var/run/docker.sock:/var/run/docker.sock` |
| `worker` | `/tmp/runner:/tmp/runner` |
| `worker` | `/opt/blog:/opt/blog` |

Relative bind sources resolve beside the Compose file. Named volumes are Docker-managed. Paths outside `/opt` are declarations read from Compose; their contents and mount status were not inspected.

## Recreate the setup

1. Use `myoung34/github-runner` with the intended repository, runner name, scope, labels, work directory, and a private registration credential.
2. The observed mounts expose the Docker socket, a runner work directory, and `/opt/blog` to the container.
3. Match workflow runner labels to registration. Limit which workflows can execute on a runner with host Docker and deployment-directory access.
4. Run a controlled deployment and inspect its resulting site before relying on automatic publication. The observed workflow is manually dispatched.

These are owner-run setup instructions; no deployment command was executed during documentation. Pin compatible versions and supply private values before starting a new instance.

## Data and recovery

Keep the Compose definition and workflow source. Re-register with fresh credentials during recovery; do not treat the temporary runner work directory as the source of truth.

## Verification and troubleshooting

If a job waits for a runner, verify registration and label matching. If it runs but deployment fails, check the blog mount and ownership. Access to Docker’s socket grants broad host capabilities.

## Deployment notes

The existing source contains credential configuration fields. The documentation deliberately provides variable names and mount behavior without their values.
