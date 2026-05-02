FROM python:3.11-slim

# System deps for Playwright + Chromium
RUN apt-get update && apt-get install -y \
    wget curl gnupg ca-certificates \
    libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 \
    libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 \
    libgbm1 libasound2 libpango-1.0-0 libcairo2 \
    fonts-liberation fonts-noto-color-emoji \
    --no-install-recommends && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps
COPY requirements_server.txt .
RUN pip install --no-cache-dir -r requirements_server.txt
RUN pip install --no-cache-dir firebase-admin

# Install Playwright + Chromium
RUN playwright install chromium
RUN playwright install-deps chromium

# Copy app code
COPY app_server.py .
COPY 2_Graphics_Generation/ ./2_Graphics_Generation/
COPY 1_Data_Input/ ./1_Data_Input/
COPY templates/ ./templates/
COPY buhovision_app.html .

# Logo cache dir (populated at runtime from Firebase Storage)
RUN mkdir -p /app/logo_cache

ENV CLOUD_MODE=1
ENV FIREBASE_BUCKET=buhovision-5bee4.appspot.com
ENV LOGOS_STORAGE_PREFIX=logos
ENV PORT=8080

EXPOSE 8080

CMD ["python", "app_server.py"]
