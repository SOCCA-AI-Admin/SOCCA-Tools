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

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY README.md ./README.md
COPY HOTEL_BILDER.md ./HOTEL_BILDER.md

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "app.hotel_app:app", "--host", "0.0.0.0", "--port", "8000"]
