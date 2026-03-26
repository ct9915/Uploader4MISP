# ── Stage 1: Builder ────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libldap2-dev \
    libsasl2-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies into a prefix dir
COPY requirements.txt .
RUN pip install --prefix=/install --no-cache-dir -r requirements.txt


# ── Stage 2: Runtime ────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

LABEL maintainer="ct9915" \
      description="Uploader4MISP - Malicious File Detection Platform" \
      version="1.0"

# Runtime system deps (ldap3 needs libldap at runtime)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libldap-2.5-0 \
    libsasl2-2 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Create non-root user
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser

WORKDIR /app

# Copy application source
COPY --chown=appuser:appuser . .

# Create runtime directories that must be writable
RUN mkdir -p instance/uploads instance/temp && \
    chown -R appuser:appuser instance

USER appuser

# Expose the application port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/auth/login')" || exit 1

# Default: production with gunicorn
ENV FLASK_ENV=production \
    PORT=5000 \
    WEB_CONCURRENCY=4

CMD ["sh", "-c", "gunicorn -w ${WEB_CONCURRENCY} -b 0.0.0.0:${PORT} wsgi:app"]
