# Agentic Content Factory - Docker Build
# Multi-stage build for production deployment

FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

# -------------------
# Builder stage
# -------------------
FROM base as builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# -------------------
# Production stage
# -------------------
FROM base as production

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY src/ ./src/
COPY config/ ./config/
COPY pyproject.toml .

# Create output directory
RUN mkdir -p /app/output

# Set default environment variables
ENV ENVIRONMENT=production \
    LOG_LEVEL=INFO

# Expose API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys, urllib.request; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/health').getcode() == 200 else 1)" || exit 1

# Default command - run API server
CMD ["python", "-m", "src.main", "--mode", "api", "--host", "0.0.0.0", "--port", "8000"]

# -------------------
# Development stage
# -------------------
FROM base as development

# Install development dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Install additional dev tools
RUN pip install pytest pytest-asyncio pytest-cov black ruff

# Copy all code
COPY . .

# Create output directory
RUN mkdir -p /app/output

# Expose API port
EXPOSE 8000

# Default command for development
CMD ["python", "-m", "src.main", "--mode", "api", "--host", "0.0.0.0", "--port", "8000"]
