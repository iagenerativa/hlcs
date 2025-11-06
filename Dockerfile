# ============================================================================
# Stage 1: Builder
# ============================================================================
FROM python:3.12-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# ============================================================================
# Stage 2: Runtime
# ============================================================================
FROM python:3.12-slim

WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /root/.local /root/.local

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY src/ /app/src/
COPY proto/ /app/proto/
COPY scripts/ /app/scripts/
COPY .env.example /app/.env

# Create directories
RUN mkdir -p /app/logs /app/data

# Set Python path
ENV PYTHONPATH=/app/src:$PYTHONPATH

# Expose ports
EXPOSE 4000 4001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import httpx; httpx.get('http://localhost:4001/health', timeout=5.0)" || exit 1

# Default command: REST server (más estable que gRPC sin stubs)
CMD ["python", "-m", "hlcs.rest_gateway.server"]
