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

# Create non-root user matching host user (prevents permission issues)
RUN groupadd --system --gid ${GROUP_ID} appgroup && \
    useradd --system --gid appgroup --uid ${USER_ID} --shell /bin/bash appuser && \
    chown -R appuser:appgroup /app

# Copy source BEFORE uv sync so editable/workspace install can find it
COPY --chown=appuser:appgroup backend/app ./app
COPY --chown=appuser:appgroup backend/alembic ./alembic
COPY --chown=appuser:appgroup backend/alembic.ini ./alembic.ini
COPY --chown=appuser:appgroup backend/tests ./tests

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen

# Switch to non-root user BEFORE running application
USER appuser

# Ensure write permissions for bind-mounted directories
RUN chmod -R 775 /app/alembic/versions

ENV PATH="/app/.venv/bin:$PATH"

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
