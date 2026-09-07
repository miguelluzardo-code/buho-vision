FROM node:22-slim

# Chromium del sistema para whatsapp-web.js (puppeteer)
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium fonts-liberation fonts-noto-color-emoji ca-certificates \
    && rm -rf /var/lib/apt/lists/*

ENV PUPPETEER_SKIP_DOWNLOAD=1 \
    PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium \
    BOT_SESSION_DIR=/data/wwebjs_auth \
    NODE_ENV=production

WORKDIR /app
COPY package*.json ./
RUN npm ci --omit=dev --no-audit --no-fund
COPY src ./src
COPY config/*.example.json ./config/

# /data debe ser un volumen persistente (sesión de WhatsApp + estado del bot)
RUN mkdir -p /data/wwebjs_auth /app/data
VOLUME ["/data"]

CMD ["node", "src/index.js"]
