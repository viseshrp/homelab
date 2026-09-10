ARG HOMARR_BASE_IMAGE=ghcr.io/ajnart/homarr@sha256:e103abadfb527186af5b4bd43df4eff7c67afa5cd4df8e65fa97910c8840b2a9
FROM ${HOMARR_BASE_IMAGE}

COPY patch-qbittorrent-cookie.mjs /usr/local/share/homarr/patch-qbittorrent-cookie.mjs
RUN node /usr/local/share/homarr/patch-qbittorrent-cookie.mjs
