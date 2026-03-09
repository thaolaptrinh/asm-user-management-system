ARG UV_VERSION=0.5.20

FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv

FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# ── Builder: install runtime deps only (no source, layer-cached) ───────
FROM base AS builder

COPY --from=uv /uv /usr/local/bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/app/.venv

COPY backend/pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-workspace

# ── Development: add dev deps, source baked in + synced via compose watch
FROM builder AS development

# Build-time arguments for user mapping (auto-detected by Makefile)
ARG USER_ID=1000
ARG GROUP_ID=1000

# Create non-root user before COPY to use --chown (matches production pattern)
RUN groupadd --system --gid ${GROUP_ID} appgroup && \
    useradd --system --gid appgroup --uid ${USER_ID} --shell /bin/bash appuser && \
    mkdir -p /home/appuser/.cache/uv /home/appuser/.cache/ruff && \
    chown -R appuser:appgroup /home/appuser

# Copy source AFTER user exists (ensures correct UID/GID mapping)
COPY --chown=appuser:appgroup backend/app ./app
COPY --chown=appuser:appgroup backend/alembic ./alembic
COPY --chown=appuser:appgroup backend/alembic.ini ./alembic.ini
COPY --chown=appuser:appgroup backend/tests ./tests

# Install dependencies (creates .venv)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen

# --- CHANGED: Fix .venv ownership separately
RUN chown -R appuser:appgroup /app/.venv && \
    chmod -R 775 /app/alembic/versions

# Switch to non-root user
USER appuser

ENV PATH="/app/.venv/bin:$PATH"
ENV RUFF_CACHE_DIR=/home/appuser/.cache/ruff
ENV PYTHONPATH=/app

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["uvicorn", "app.main:app", \
    "--host", "0.0.0.0", "--port", "8000", \
    "--reload", "--reload-dir", "/app/app", \
    "--log-level", "debug"]

# ── Production: minimal image, non-root user ──────────────────────────
FROM base AS production

# Create non-root user before COPY to use --chown (avoids extra layer)
RUN groupadd --system --gid 1001 appgroup && \
    useradd --system --gid appgroup --uid 1001 --shell /bin/false appuser

COPY --from=builder --chown=appuser:appgroup /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

COPY --chown=appuser:appgroup backend/app ./app
COPY --chown=appuser:appgroup backend/alembic ./alembic
COPY --chown=appuser:appgroup backend/alembic.ini ./alembic.ini

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# exec replaces the shell so SIGTERM reaches uvicorn directly (graceful shutdown)
# Shell form used here to expand ${WEB_CONCURRENCY:-2} at runtime
CMD exec uvicorn app.main:app \
    --host 0.0.0.0 --port 8000 \
    --workers ${WEB_CONCURRENCY:-2} --log-level info
