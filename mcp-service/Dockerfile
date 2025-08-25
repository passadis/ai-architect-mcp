# Use Python 3.11 slim image
FROM python:3.11-slim

# Install system dependencies for diagrams and graphviz
RUN apt-get update && apt-get install -y \
    graphviz \
    graphviz-dev \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Create directories for generated content
RUN mkdir -p /app/static/diagrams

# Expose port for HTTP wrapper
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Start the MCP HTTP wrapper
CMD ["python", "mcp_http_wrapper.py"]
