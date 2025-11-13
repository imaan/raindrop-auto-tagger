# Use Python 3.9 slim image for smaller size
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY raindrop_auto_tagger.py .
COPY app.py .

# Create non-root user for security
RUN useradd -m -u 1000 tagger && chown -R tagger:tagger /app
USER tagger

# Expose port for web service
EXPOSE 8080

# Default command - can be overridden
# For web service: CMD ["python", "app.py"]
# For direct execution: CMD ["python", "raindrop_auto_tagger.py"]
CMD ["python", "app.py"]