#!/bin/bash
apt update
apt full-upgrade -y
apt autoremove -y

cd /opt/
docker-compose pull
docker-compose up -d
docker image prune -af
docker volume prune -f
