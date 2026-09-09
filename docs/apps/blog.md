# Hugo blog and Nginx

Serves the static personal site; Hugo produces the files and Nginx serves the `public/` directory.

[Homelab index](../../README.md) · [Architecture](../architecture.md) · [Inspection record](../inventory.md)

## Observed setup

Direct HTTP on port 80 returned 200. The root-domain and `www` proxy names point here. Compose, Dockerfile, and the publish workflow were inspected under `/opt/blog`.

Host: `rpiblog`. Definition: `/opt/blog/docker-compose.yml`.

| Service | Image/build recorded | Network / host ports | Restart |
| --- | --- | --- | --- |
| `webserver` | `Local build` | Compose network; `80:80` | `always` |

| Service | Declared storage mapping |
| --- | --- |
| `webserver` | `./public:/usr/share/nginx/html` |

Relative bind sources resolve beside the Compose file. Named volumes are Docker-managed. Paths outside `/opt` are declarations read from Compose; their contents and mount status were not inspected.

## Recreate the setup

1. Keep the site checkout, Hugo theme/submodules, Dockerfile, and Nginx configuration in the blog project.
2. Build the static site with `hugo --minify --enableGitInfo`. The inspected workflow sets up extended Hugo and checks out submodules.
3. The manually triggered GitHub Actions workflow runs on a self-hosted runner and uses `rsync -rav . /opt/blog` to deploy the checkout.
4. Build the Nginx image and mount `./public` at `/usr/share/nginx/html`; route the root domain and `www` to host port 80.

These are owner-run setup instructions; no deployment command was executed during documentation. Pin compatible versions and supply private values before starting a new instance.

## Data and recovery

Preserve the site source, theme revision, Nginx configuration, and workflow. Generated `public/` can be rebuilt when the source and toolchain are available.

## Verification and troubleshooting

If the site serves old pages, distinguish the workflow build from the files mounted by Nginx. The inspected rsync command does not use `--delete`, so a deployment can leave files that disappeared from the source.

## Deployment notes

The Dockerfile starts from `nginx:latest` and copies `default.conf`. Only the Dockerfile and workflow were inspected, not the contents of that Nginx config.

Related: [GitHub Actions runner](github-runner.md), [Nginx Proxy Manager](nginx-proxy-manager.md).
