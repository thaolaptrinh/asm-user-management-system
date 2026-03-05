ARG BUN_VERSION=1.3.10

# ── Dependencies ──────────────────────────────────────────────────────
FROM oven/bun:${BUN_VERSION} AS dependencies

WORKDIR /app
COPY package.json bun.lock* ./
COPY frontend/package.json ./frontend/

RUN --mount=type=cache,target=/root/.bun/install/cache \
    bun install --no-save --frozen-lockfile

# ── Builder ───────────────────────────────────────────────────────────
FROM oven/bun:${BUN_VERSION} AS builder

ARG NEXT_PUBLIC_API_URL

ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL} \
    NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1

WORKDIR /app
COPY --from=dependencies /app/node_modules ./node_modules
COPY package.json ./
COPY frontend/ ./frontend/

WORKDIR /app/frontend
RUN bun run build

# ── Dev ───────────────────────────────────────────────────────────────
FROM oven/bun:${BUN_VERSION} AS dev

RUN apt-get update && \
    apt-get install -y --no-install-recommends gosu && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY package.json bun.lock* ./
COPY frontend/package.json ./frontend/
COPY --from=dependencies /app/node_modules ./node_modules
COPY frontend/ ./frontend/

ENV NODE_ENV=development

WORKDIR /app/frontend
EXPOSE 3000

ENTRYPOINT ["bash", "/app/frontend/scripts/dev-entrypoint.sh"]
CMD ["bun", "run", "dev"]

# ── Runner ────────────────────────────────────────────────────────────
FROM oven/bun:${BUN_VERSION} AS runner

LABEL org.opencontainers.image.title="frontend" \
      org.opencontainers.image.description="Next.js frontend"

WORKDIR /app

ENV NODE_ENV=production \
    PORT=80 \
    HOSTNAME="0.0.0.0" \
    NEXT_TELEMETRY_DISABLED=1

RUN mkdir .next && chown bun:bun .next

COPY --from=builder --chown=bun:bun /app/frontend/.next/standalone ./

WORKDIR /app/frontend
COPY --from=builder --chown=bun:bun /app/frontend/public ./public
COPY --from=builder --chown=bun:bun /app/frontend/.next/static ./.next/static
COPY --from=builder --chown=bun:bun /app/node_modules/next/dist/compiled/@opentelemetry \
    ./node_modules/next/dist/compiled/@opentelemetry

USER bun
EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD bun -e "fetch('http://localhost:80').then(r=>{if(!r.ok)throw 1}).catch(()=>process.exit(1))"

CMD ["bun", "server.js"]
