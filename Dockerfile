FROM python:3.9-slim-buster
RUN export DEBIAN_FRONTEND=noninteractive && \
apt-get update && \
apt-get -y upgrade && \
apt-get install -y --no-install-recommends tini file && \
apt-get -y clean && \
    rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN useradd --create-home action
USER action
WORKDIR /app
COPY artichoke_growth .
ENV PYTHONFAULTHANDLER=1
ENTRYPOINT ["tini", "--", "python", "-m", "artichoke_growth"]
