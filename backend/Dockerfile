# Bijmantra Backend - Multi-stage Dockerfile
# Supports both development and production builds

# ============================================
# Base stage - common dependencies
# ============================================
FROM python:3.11-slim AS base

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# ============================================
# Development stage - with hot reload
# ============================================
FROM base AS development

# Install development dependencies
RUN pip install --no-cache-dir \
    watchfiles \
    debugpy \
    pytest \
    pytest-asyncio \
    pytest-cov \
    httpx

# Copy application code (will be overridden by volume mount)
COPY . .

# Expose ports (8000 for app, 5678 for debugger)
EXPOSE 8000 5678

# Development command with hot reload
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ============================================
# Production stage - optimized for deployment
# ============================================
FROM base AS production

# Create non-root user for security
RUN groupadd -r bijmantra && useradd -r -g bijmantra bijmantra

# Copy application code
COPY --chown=bijmantra:bijmantra . .

# Remove unnecessary files
RUN rm -rf tests/ *.md .git* __pycache__/ .pytest_cache/ .coverage

# Switch to non-root user
USER bijmantra

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Production command with gunicorn
CMD ["gunicorn", "app.main:app", \
    "--workers", "4", \
    "--worker-class", "uvicorn.workers.UvicornWorker", \
    "--bind", "0.0.0.0:8000", \
    "--access-logfile", "-", \
    "--error-logfile", "-"]
