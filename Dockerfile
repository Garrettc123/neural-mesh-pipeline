FROM python:3.11-slim

LABEL maintainer="neural-mesh-pipeline"
LABEL description="Production-ready self-healing neural mesh pipeline"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements-termux.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements-termux.txt

# Copy application files
COPY pipeline_enhanced.py .
COPY README.md .
COPY IMPLEMENTATION_GUIDE.md .
COPY QUICK_REFERENCE.md .
COPY TROUBLESHOOTING.md .

# Create necessary directories
RUN mkdir -p /app/src/tests /app/logs /app/storage

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV BASE_DIR=/app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import os; exit(0 if os.path.exists('/app/storage/pipeline_state.json') else 1)"

# Default command
CMD ["python", "pipeline_enhanced.py", "--mode", "continuous"]
