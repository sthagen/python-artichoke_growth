
FROM python:3.9.2-slim-buster
LABEL org.opencontainers.image.created="2021-03-10T00:00:00Z" \
    org.opencontainers.image.authors="Stefan Hagen <mailto:stefan@hagen.link>" \
    org.opencontainers.image.url="https://hub.docker.com/repository/docker/shagen/artichoke-growth/" \
    org.opencontainers.image.documentation="https://sthagen.github.io/python-artichoke_growth/" \
    org.opencontainers.image.source="https://github.com/sthagen/python-artichoke_growth/" \
    org.opencontainers.image.version="2021.03.10" \
    org.opencontainers.image.revision="cafefadecafefadecafefadecafefadecafefade" \
    org.opencontainers.image.vendor="Stefan Hagen <mailto:stefan@hagen.link>" \
    org.opencontainers.image.licenses="MIT License" \
    org.opencontainers.image.ref.name="shagen/artichoke-growth" \
    org.opencontainers.image.title="Binary repository management system hash storage indexer." \
    org.opencontainers.image.description="Later some description for the growing artichoke)."

RUN export DEBIAN_FRONTEND=noninteractive && \
apt-get update && \
apt-get -y upgrade && \
apt-get install -y --no-install-recommends tini && \
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
