ARG PYTHON_VERSION=3.10
ARG UV_VERSION=0.9.26

FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv

# ── Base ──────────────────────────────────────────────────────────────
FROM python:${PYTHON_VERSION}-slim-bookworm AS base

COPY --from=uv /uv /uvx /bin/

ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# ── Dependencies ──────────────────────────────────────────────────────
FROM base AS dependencies

COPY backend/pyproject.toml backend/alembic.ini uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-workspace --package app

RUN uv pip install pymysql cryptography

# ── Builder ───────────────────────────────────────────────────────────
FROM base AS builder

COPY --from=dependencies /app/.venv /app/.venv
COPY backend/scripts /app/backend/scripts
COPY backend/pyproject.toml backend/alembic.ini /app/backend/
COPY backend/app /app/backend/app
COPY backend/migrations /app/backend/migrations
COPY backend/tests /app/backend/tests

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=backend/pyproject.toml,target=pyproject.toml \
    uv sync --frozen --package app

# ── Runner ────────────────────────────────────────────────────────────
FROM python:${PYTHON_VERSION}-slim-bookworm AS runner

LABEL org.opencontainers.image.title="backend" \
      org.opencontainers.image.description="FastAPI backend"

ENV PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

COPY --from=dependencies --chown=appuser:appuser /app/.venv /app/.venv
COPY --from=builder --chown=appuser:appuser /app/backend /app/backend

WORKDIR /app/backend
USER appuser
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/utils/health-check/')"

CMD ["fastapi", "run", "--workers", "4", "app/main.py"]
