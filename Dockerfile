# ==================================
# STAGE 1: Builder
# ==================================
FROM python:3.11-slim as builder

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de trabajo
WORKDIR /app

# Copiar requirements
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ==================================
# STAGE 2: Runtime
# ==================================
FROM python:3.11-slim

# Variables de entorno
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Instalar dependencias del sistema (runtime)
RUN apt-get update && apt-get install -y \
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Crear usuario no-root
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app /app/staticfiles /app/media /app/ml_models && \
    chown -R appuser:appuser /app

# Directorio de trabajo
WORKDIR /app

# Copiar dependencias del builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copiar código de la aplicación
COPY --chown=appuser:appuser . .

# Cambiar a usuario no-root
USER appuser

# Exponer puerto
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/docs/')" || exit 1

# Script de inicio
CMD ["sh", "-c", "python manage.py migrate && python manage.py collectstatic --noinput && gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4 --timeout 120"]
