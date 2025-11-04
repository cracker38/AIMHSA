FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (kept minimal; add libs only if required at runtime)
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    python3-dev \
    libffi-dev \
    libssl-dev \
    pkg-config \
    libgomp1 \
    curl \
 && rm -rf /var/lib/apt/lists/*

# Ensure modern pip stack
RUN python -m pip install --upgrade pip setuptools wheel

# Install Python dependencies (cloud-optimized)
COPY requirements-cloud.txt ./requirements-cloud.txt
RUN pip install --no-cache-dir -r requirements-cloud.txt

# Copy app source
COPY . .

# Create writable dirs used by the app
RUN mkdir -p /app/instance /app/data /data /app/uploads /app/logs /storage \
 && chmod -R 777 /app/instance /app/data /data /app/uploads /app/logs /storage

EXPOSE 7860

# Start the Flask app (port picked from config/env, defaults to 7860)
CMD ["python", "run_aimhsa.py"]
