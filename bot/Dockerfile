# Multi-stage build for Bot Service (Production-Ready)
FROM python:3.10-slim as builder

WORKDIR /build
COPY requirements.txt .

# Install dependencies
RUN pip install --user --no-cache-dir -r requirements.txt


# Final stage
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder
COPY --from=builder --chown=1000:1000 /root/.local /root/.local

# Set environment variable for PATH
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app /root/.local
USER appuser

# Run application with restart capability
CMD ["python", "main.py"]
