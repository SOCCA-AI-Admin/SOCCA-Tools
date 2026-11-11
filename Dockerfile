FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# OpenCV headless + HEIC/HEIF runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libheif1 \
    && rm -rf /var/lib/apt/lists/*

# LightCraft (Open-Source-Nachbau von Lightroom) für Preset SOCCA.xmp und Gerade ausrichten.
# Feste Version mit Prüfsumme: Ein Update ist eine bewusste Änderung an diesen zwei Zeilen
# (Prüfsumme: sha256sum lightcraft-<version>-linux-x86_64.tar.gz). Nur lightcraft-cli wird installiert.
ARG LIGHTCRAFT_VERSION=0.13.0
ARG LIGHTCRAFT_SHA256=873c795e641ea8c345e02e4895f6c2659015e531420f68352ca3421aa9b8edcd
RUN python -c "import hashlib,sys,tarfile,urllib.request; \
v='${LIGHTCRAFT_VERSION}'; \
url=f'https://github.com/storytold/lightcraft/releases/download/v{v}/lightcraft-{v}-linux-x86_64.tar.gz'; \
p='/tmp/lightcraft.tar.gz'; urllib.request.urlretrieve(url, p); \
h=hashlib.sha256(open(p,'rb').read()).hexdigest(); \
sys.exit('LightCraft: Prüfsumme stimmt nicht: '+h) if h!='${LIGHTCRAFT_SHA256}' else None; \
t=tarfile.open(p); m=t.getmember(f'lightcraft-{v}-linux-x86_64/bin/lightcraft-cli'); \
m.name='lightcraft-cli'; t.extract(m,'/usr/local/bin',filter='data'); t.close()" \
    && rm -f /tmp/lightcraft.tar.gz \
    && chmod 755 /usr/local/bin/lightcraft-cli \
    && lightcraft-cli commands > /dev/null

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY README.md ./README.md
COPY HOTEL_BILDER.md ./HOTEL_BILDER.md

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "app.hotel_app:app", "--host", "0.0.0.0", "--port", "8000"]
