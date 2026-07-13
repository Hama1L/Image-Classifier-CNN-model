# --- Base image -------------------------------------------------------------
# python:3.11-slim keeps the image small compared to the full python:3.11 image.
FROM python:3.11-slim

WORKDIR /app

# Pillow needs a JPEG decoder available at the OS level.
RUN apt-get update && apt-get install -y --no-install-recommends \
        libjpeg62-turbo \
    && rm -rf /var/lib/apt/lists/*

# --- Dependencies ------------------------------------------------------------
# Copying requirements.txt BEFORE the rest of the code means Docker only
# re-installs dependencies when requirements.txt actually changes, not on
# every code edit. This is one of the most important Docker caching habits.
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- Application code ---------------------------------------------------------
COPY backend/app ./app
COPY frontend ./frontend

# Pre-download the model weights at build time. Without this, the container's
# FIRST request would stall for several seconds while weights download —
# and would fail entirely in an environment with no internet access at runtime.
RUN python -c "from app.model import load_model; load_model()"

EXPOSE 8000

# Basic container-level health check, used by `docker ps` and orchestrators.
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
