FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# GeoDjango needs these libraries to read and measure geometry.
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

# Install dependencies before copying the rest of the project.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod -R a+rX /app

RUN useradd --create-home --uid 1000 appuser \
    && mkdir -p /app/staticfiles \
    && chown -R appuser:appuser /app/staticfiles
# Run Django without root access.
USER appuser

EXPOSE 8000

ENTRYPOINT ["sh", "/app/docker/entrypoint.sh"]
