# CyberArchitect — Ultimate Website Replicator
# Node.js CLI service with health endpoint wrapper

FROM node:20-slim

WORKDIR /app

# Install system dependencies for Puppeteer/Chromium
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    fonts-liberation \
    libappindicator3-1 \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libc6 \
    libcairo2 \
    libcups2 \
    libdbus-1-3 \
    libexpat1 \
    libfontconfig1 \
    libgbm1 \
    libgcc1 \
    libglib2.0-0 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libstdc++6 \
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxi6 \
    libxrandr2 \
    libxrender1 \
    libxss1 \
    libxtst6 \
    lsb-release \
    wget \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy package files and install if present
COPY package.json package-lock.json* ./
RUN if [ -f package.json ]; then npm ci || npm install; fi

# Copy application code
COPY . .

# Create a minimal health-endpoint wrapper
RUN echo 'const http = require("http");\n\
const port = process.env.PORT || 8105;\n\
const server = http.createServer((req, res) => {\n\
  if (req.url === "/health") {\n\
    res.writeHead(200, { "Content-Type": "application/json" });\n\
    res.end(JSON.stringify({ status: "healthy", service: "cyberarchitect" }));\n\
  } else {\n\
    res.writeHead(404);\n\
    res.end("Not Found");\n\
  }\n\
});\n\
server.listen(port, () => {\n\
  console.log(`CyberArchitect health probe on port ${port}`);\n\
});\n' > health-server.js

ENV NODE_ENV=production \
    PORT=8105

EXPOSE 8105

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8105/health || exit 1

CMD ["node", "health-server.js"]
