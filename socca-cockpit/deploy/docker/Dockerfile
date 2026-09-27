# Image für den Rechen-Container: nur Python und die zwei Excel-Bibliotheken.
# Der Code selbst wird zur Laufzeit aus dem Projektordner eingebunden.
ARG BASE=python:3.12-slim
FROM ${BASE}

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_BREAK_SYSTEM_PACKAGES=1 \
    PIP_NO_CACHE_DIR=1 \
    TZ=Europe/Berlin \
    HOME=/tmp

# Zeitzonen-Daten, damit Log und Zeitstempel deutsche Zeit zeigen
RUN if [ ! -e /usr/share/zoneinfo/Europe/Berlin ]; then \
      apt-get update && apt-get install -y --no-install-recommends tzdata && rm -rf /var/lib/apt/lists/*; \
    fi

COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

WORKDIR /app
CMD ["bash", "/app/deploy/docker/worker.sh"]
