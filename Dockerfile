# Railway Dockerfile for construction tracking system
FROM python:3.10-slim

# Install system dependencies for WeasyPrint and curl for healthcheck
RUN apt-get update && apt-get install -y \
    libgobject-2.0-0 \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libcairo2 \
    libfontconfig1 \
    libfreetype6 \
    libgdk-pixbuf-2.0-0 \
    libharfbuzz0b \
    libfribidi0 \
    libpng16-16 \
    libjpeg62-turbo \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p uploads static/reports

# Expose port
EXPOSE 5000

# Set environment variables
ENV PYTHONPATH=/app
ENV FLASK_ENV=production

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Start application
CMD ["python", "main_production.py"]