# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.11-slim

EXPOSE 8000

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Set environment variable to indicate we're running in a container
ENV RUNNING_IN_CONTAINER=true

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy and install requirements first (for better caching)
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Create necessary directories
RUN mkdir -p /app/logs /app/data

# Copy application code
COPY . /app/

# Creates a non-root user with an explicit UID and adds permission to access the /app folder
RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser:appuser /app
USER appuser

# Health check with more generous parameters
HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=5 \
    CMD curl -f http://localhost:8000/health || exit 1

# During debugging, this entry point will be overridden. For more information, please refer to https://aka.ms/vscode-docker-python-debug
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "120", "-k", "uvicorn.workers.UvicornWorker", "main:app"]
