FROM amir20/dozzle:v10.10.0

ARG BUILD_ARCH
ARG BUILD_VERSION

LABEL io.hass.version="${BUILD_VERSION}" \
      io.hass.type="app" \
      io.hass.arch="${BUILD_ARCH}"

ENV DOCKER_HOST="unix:///run/docker.sock"

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
  CMD ["/dozzle", "healthcheck"]

CMD ["agent"]
