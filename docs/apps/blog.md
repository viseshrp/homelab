# Hugo blog

Hugo builds the personal site into static files. Nginx serves those files behind the root-domain and `www` routes in Nginx Proxy Manager.

## My setup

The site lives at `/opt/blog` on `rpiblog`. Its Compose service builds an image from `nginx:latest`, copies in `default.conf`, and publishes port 80.

The `public/` directory is mounted at `/usr/share/nginx/html`. It contains the generated site that Nginx serves.

## Publishing

A manually triggered GitHub Actions workflow runs on the [self-hosted runner](github-runner.md). It checks out the site with its theme submodules, sets up extended Hugo, and builds with:

```sh
hugo --minify --enableGitInfo
```

The workflow deploys the checkout to `/opt/blog` using `rsync -rav`. Nginx serves the updated `public/` directory through its bind mount.

## Verify and recover

After publication, check the runner job, the generated files under `public/`, the direct `rpiblog:80` response, and both apex and `www` HTTPS routes. This distinguishes a build/deploy failure from an Nginx or proxy failure.

The Hugo source repository is authoritative. Treat `public/` as rebuildable output; retain the local Dockerfile, Nginx configuration, and deployment workflow needed to serve a clean rebuild.

[Compose](../../docker-compose/blog/docker-compose.yml) · [Operations](../operations.md) · [Application index](README.md)
