# sovereign_ai — Bun + Astro + WASM Documentation Site
# Serves static Astro output with COOP/COEP headers via Bun

FROM oven/bun:1-alpine

WORKDIR /app

# Install curl for health checks
RUN apk add --no-cache curl

# Copy Astro built output + bun server
# NOTE: In production, build first then copy dist/
COPY . .

# If dist exists, use it; otherwise bun-server.ts handles fallback
ENV PORT=8106 \
    NODE_ENV=production \
    DIST_DIR=/app/dist

EXPOSE 8106

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8106/health || exit 1

CMD ["bun", "run", "bun-server.ts"]
