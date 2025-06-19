# ======================================================
# HIGHERSELF NETWORK SERVER - MULTI-STAGE DOCKERFILE
# Optimized for GitHub Container Registry integration
# ======================================================

# Build arguments
ARG VERSION=latest
ARG BUILD_DATE
ARG VCS_REF
ARG BUILDKIT_INLINE_CACHE=1

# Base image for all stages
FROM python:3.11-slim as base

# Metadata labels
LABEL org.opencontainers.image.title="HigherSelf Network Server"
LABEL org.opencontainers.image.description="Enterprise automation platform for multi-business entity management"
LABEL org.opencontainers.image.vendor="HigherSelf Network"
LABEL org.opencontainers.image.version="${VERSION}"
LABEL org.opencontainers.image.created="${BUILD_DATE}"
LABEL org.opencontainers.image.revision="${VCS_REF}"
LABEL org.opencontainers.image.source="https://github.com/Utak-West/The-HigherSelf-Network-Server"
LABEL org.opencontainers.image.documentation="https://github.com/Utak-West/The-HigherSelf-Network-Server/blob/main/docs/README.md"
LABEL org.opencontainers.image.licenses="MIT"
LABEL com.higherself.version="${VERSION}"
LABEL com.higherself.build-date="${BUILD_DATE}"
LABEL com.higherself.vcs-ref="${VCS_REF}"
LABEL com.higherself.business-entities="the_7_space,am_consulting,higherself_core"

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV RUNNING_IN_CONTAINER=true
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# ======================================================
# DEPENDENCIES STAGE - Install system dependencies
# ======================================================
FROM base as dependencies

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    g++ \
    python3-dev \
    tesseract-ocr \
    tesseract-ocr-eng \
    libtesseract-dev \
    libleptonica-dev \
    git \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# ======================================================
# BUILDER STAGE - Install Python dependencies
# ======================================================
FROM dependencies as builder

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# ======================================================
# DEVELOPMENT STAGE - For development with hot reload
# ======================================================
FROM dependencies as development

WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /root/.local /root/.local

# Add local bin to PATH
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/logs /app/data /app/uploads

# Expose port
EXPOSE 8000

# Development command with hot reload
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--log-level", "debug"]

# ======================================================
# PRODUCTION STAGE - Optimized production image
# ======================================================
FROM base as production

WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /root/.local /root/.local

# Add local bin to PATH
ENV PATH=/root/.local/bin:$PATH

# Create necessary directories
RUN mkdir -p /app/logs /app/data /app/uploads

# Copy application code
COPY . .

# Create non-root user
RUN adduser -u 5678 --disabled-password --gecos "" appuser \
    && chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=5 \
    CMD curl -f http://localhost:8000/health || exit 1

# Production command
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "120", "--worker-class", "uvicorn.workers.UvicornWorker", "main:app"]

# ======================================================
# DEFAULT STAGE - Production by default
# ======================================================
FROM production
