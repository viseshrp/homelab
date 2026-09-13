FROM crazymax/diun:4.33.0@sha256:e324b793eb32dfb7f74d3a39421ebf090141caaadee69b8f78da63112408ee25

ARG BUILD_ARCH
ARG BUILD_VERSION

LABEL io.hass.version="${BUILD_VERSION}" \
      io.hass.type="app" \
      io.hass.arch="${BUILD_ARCH}"

RUN apk add --no-cache jq

COPY run.sh /run.sh
COPY custom-images.yml /etc/diun/custom-images.yml
RUN chmod 0755 /run.sh

ENTRYPOINT ["/run.sh"]
CMD []
