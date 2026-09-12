ARG SCRUTINY_COLLECTOR_BASE
FROM ${SCRUTINY_COLLECTOR_BASE}

COPY --chmod=0555 collector-run.sh /opt/scrutiny/bin/collector-run.sh
COPY --chmod=0644 scrutiny.cron /etc/cron.d/scrutiny
