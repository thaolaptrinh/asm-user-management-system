# Bun 1.3.10 - LTS stable release
# Update: Check https://github.com/oven-sh/bun/releases
ARG BUN_VERSION=1.3.10
FROM oven/bun:${BUN_VERSION}-alpine AS deps

WORKDIR /app

COPY bun.lock package.json ./
COPY frontend/package.json ./frontend/
RUN bun install

FROM deps AS development

COPY frontend/ ./frontend/

WORKDIR /app/frontend

ENV NODE_ENV=development \
    NEXT_TELEMETRY_DISABLED=1 \
    HOSTNAME=0.0.0.0

EXPOSE 3000

CMD ["bun", "run", "dev"]

FROM deps AS builder

COPY frontend/ ./frontend/

WORKDIR /app/frontend

ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL} \
    NEXT_TELEMETRY_DISABLED=1

RUN bun run build

FROM node:25-alpine AS production

WORKDIR /app

ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    HOSTNAME=0.0.0.0

COPY --from=builder /app/frontend/.next/standalone ./
COPY --from=builder /app/frontend/.next/static ./.next/static
COPY --from=builder /app/frontend/public ./public

RUN chown -R node:node /app

USER node

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000 || exit 1

CMD ["node", "server.js"]
