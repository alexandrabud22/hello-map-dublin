# HeritageConnect - Django + GeoDjango application image
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# GIS system libraries needed by GeoDjango (GDAL, GEOS, PROJ)
RUN apt-get update \
    && apt-get install --yes --no-install-recommends \
        binutils \
        gdal-bin \
        libgdal-dev \
        libgeos-dev \
        libproj-dev \
        gdal-data \
        python3-gdal \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first (better Docker layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the project
COPY . .

# Run as a non-root user (security best practice).
# /app/staticfiles is created here so the shared static volume
# is owned by this user when Docker first creates it.
RUN useradd --create-home --uid 1000 appuser \
    && mkdir -p /app/staticfiles \
    && chown -R appuser:appuser /app/staticfiles
USER appuser

# Gunicorn listens on 8000 inside the Docker network only
EXPOSE 8000

ENTRYPOINT ["sh", "/app/docker/entrypoint.sh"]
