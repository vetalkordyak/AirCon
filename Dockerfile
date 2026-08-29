FROM python:3.14

ARG BUILD_VERSION=latest
LABEL io.hass.version="$BUILD_VERSION" io.hass.type="addon" io.hass.arch="armhf|armv7|aarch64|amd64|i386"

COPY . /app
WORKDIR /app

RUN dpkg --add-architecture i386 && apt-get update && apt-get install -y --no-install-recommends jq git
RUN pip install --no-cache-dir .

ENV PLATFORM=docker

ENV CONFIG_DIR=/opt/hisense
ENV OPTIONS_FILE=/data/options.json

COPY run.sh /
RUN chmod a+x /run.sh

# aioesphomeserver's connection handling can wedge after a burst of
# simultaneous reconnects while staying "up" from Docker's point of view -
# this actually probes the ESPHome API instead of just checking the process.
# Pair with the autoheal sidecar in docker-compose.yaml to act on it.
HEALTHCHECK --interval=60s --timeout=15s --start-period=30s --retries=3 \
  CMD python -m aircon.esphome_healthcheck

CMD [ "/run.sh" ]
