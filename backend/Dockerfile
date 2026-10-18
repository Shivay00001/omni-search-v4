# Omni Search V4 — Backend (FastAPI)
FROM python:3.11-slim

WORKDIR /app

# System deps for building wheels (if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps first (layer cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Render injects $PORT; default to 8000 for local runs
ENV PORT=8000

# Bind to 0.0.0.0 so Render's router can reach the app
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT}
