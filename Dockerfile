# Use a slim, recent Python
FROM python:3.11-slim

# Avoid writing pyc and set unbuffered
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Create app directory and a non-root user
WORKDIR /usr/src/app
RUN groupadd -r appgroup && useradd -r -s /bin/false -g appgroup appuser

# Install system deps required for typical Python wheels & curl for healthcheck
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential curl && \
    rm -rf /var/lib/apt/lists/*

# Copy only requirements first (better cache)
COPY requirements.txt .

# Install Python deps
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY ./app ./app
COPY ./README.md ./README.md

# Change ownership and switch user
RUN chown -R appuser:appgroup /usr/src/app
USER appuser

# Expose FastAPI port
EXPOSE 8000

# Use Uvicorn for serving; keep a single worker for simple evaluation.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--loop", "asyncio", "--ws", "websockets", "--lifespan", "off"]
