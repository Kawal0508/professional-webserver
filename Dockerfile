FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY webserver.py .
COPY config.json .

# Create non-root user
RUN useradd -m -u 1000 webserver && \
    chown -R webserver:webserver /app

# Switch to non-root user
USER webserver

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Default command
CMD ["python", "webserver.py", "-r", "/app/www", "-p", "8080", "-c", "config.json"]
