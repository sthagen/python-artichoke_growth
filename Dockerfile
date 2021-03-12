FROM python:3.9.2-slim-buster
RUN export DEBIAN_FRONTEND=noninteractive && \
apt-get update && \
apt-get -y upgrade && \
apt-get install -y --no-install-recommends tini file && \
apt-get -y clean && \
    rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt /app
RUN pip install --upgrade --no-cache-dir pip && pip install --no-cache-dir -r requirements.txt
RUN useradd --create-home action
USER action
COPY artichoke_growth /app/artichoke_growth
ENV PYTHONFAULTHANDLER=1
ENTRYPOINT ["tini", "--", "python", "-m", "artichoke_growth"]
ARG BUILD_TS
ARG REVISION
ARG VERSION
LABEL org.opencontainers.image.created=$BUILD_TS \
    org.opencontainers.image.authors="Stefan Hagen <mailto:stefan@hagen.link>" \
    org.opencontainers.image.url="https://hub.docker.com/repository/docker/shagen/artichoke-growth/" \
    org.opencontainers.image.documentation="https://sthagen.github.io/python-artichoke_growth/" \
    org.opencontainers.image.source="https://github.com/sthagen/python-artichoke_growth/" \
    org.opencontainers.image.version=$VERSION \
    org.opencontainers.image.revision=$REVISION \
    org.opencontainers.image.vendor="Stefan Hagen <mailto:stefan@hagen.link>" \
    org.opencontainers.image.licenses="MIT License" \
    org.opencontainers.image.ref.name="shagen/artichoke-growth" \
    org.opencontainers.image.title="artichoke-growth." \
    org.opencontainers.image.description="Document some binary repository management storage."
