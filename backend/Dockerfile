FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    HEADLESS=true

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    # installs Chromium plus the apt libs it needs
    && playwright install --with-deps chromium \
    && rm -rf /var/lib/apt/lists/*

COPY . .

# Render sets $PORT. One worker on purpose: the Playwright browser and the
# in-memory execution results live in-process and are not shareable across workers.
CMD ["sh", "-c", "exec gunicorn -k uvicorn.workers.UvicornWorker -w 1 -b 0.0.0.0:${PORT:-8000} --timeout 300 --graceful-timeout 30 --keep-alive 65 main:app"]
