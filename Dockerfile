# Use Python 3.9 slim image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Set build-time arguments
ARG FLASK_ENV=production
ARG FLASK_APP=app.py
ARG STORAGE_URL=file:///app/static/uploads

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=${FLASK_APP} \
    FLASK_ENV=${FLASK_ENV} \
    STORAGE_URL=${STORAGE_URL}

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    imagemagick \
    libmagickwand-dev \
    libwebp-dev \
    webp \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Configure ImageMagick policy to allow WebP conversion with higher limits
RUN if [ -f /etc/ImageMagick-6/policy.xml ]; then \
    sed -i 's/<policy domain="resource" name="memory" value="256MiB"\/>/<policy domain="resource" name="memory" value="1GiB"\/>/g' /etc/ImageMagick-6/policy.xml && \
    sed -i 's/<policy domain="resource" name="disk" value="1GiB"\/>/<policy domain="resource" name="disk" value="4GiB"\/>/g' /etc/ImageMagick-6/policy.xml && \
    sed -i 's/<policy domain="coder" rights="none" pattern="WEBP" \/>/<policy domain="coder" rights="read|write" pattern="WEBP" \/>/g' /etc/ImageMagick-6/policy.xml; \
    fi

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Create uploads directory
RUN mkdir -p static/uploads

# Make entrypoint script executable
RUN chmod +x entrypoint.sh

# Create volume for uploads
VOLUME /app/static/uploads

# Expose port
EXPOSE 5000

# Use the entrypoint script
ENTRYPOINT ["./entrypoint.sh"]
