#!/bin/bash
set -ex
docker compose pull
docker compose up -d --remove-orphans
yes | docker image prune
