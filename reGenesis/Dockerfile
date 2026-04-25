# reGenesis — Design System & Site Example
# pnpm workspace with Next.js static export

# Stage 1: Install dependencies with pnpm
FROM node:20-alpine AS deps
WORKDIR /app
RUN corepack enable && corepack prepare pnpm@9.7.0 --activate
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY apps/site-example/package.json ./apps/site-example/
COPY packages/ ./packages/
RUN pnpm install --frozen-lockfile || pnpm install

# Stage 2: Build tokens + packages + app
FROM node:20-alpine AS builder
WORKDIR /app
RUN corepack enable && corepack prepare pnpm@9.7.0 --activate
COPY --from=deps /app/node_modules ./node_modules
COPY --from=deps /app/apps ./apps
COPY --from=deps /app/packages ./packages
COPY . .

# Build design tokens first, then packages, then site
RUN pnpm run build:tokens && \
    pnpm run build:packages && \
    pnpm --filter @cyberarchitect/site-example run build

# Stage 3: Serve static export with nginx
FROM nginx:alpine
RUN apk add --no-cache curl
COPY --from=builder /app/apps/site-example/out /usr/share/nginx/html
COPY --from=builder /app/apps/site-example/out /usr/share/nginx/html/regenesis

# nginx config for SPA fallback + health check
RUN echo 'server { \
    listen 80; \
    location / { \
        root /usr/share/nginx/html; \
        index index.html; \
        try_files $uri $uri/ /index.html; \
    } \
    location /health { \
        access_log off; \
        return 200 '\''{"status":"healthy","service":"regenesis"}'\''; \
        add_header Content-Type application/json; \
    } \
}' > /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:80/health || exit 1
