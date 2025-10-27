FROM python:3.11-slim

WORKDIR /app

# Install system build dependencies required to build some wheels (pycld3, llama-cpp-python, etc.)
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    protobuf-compiler \
    libprotobuf-dev \
    gcc \
    g++ \
    python3-dev \
    libffi-dev \
    libssl-dev \
    pkg-config \
    libgomp1 \
    git \
    curl \
&& rm -rf /var/lib/apt/lists/*

# Ensure modern pip/setuptools/wheel before installing heavy requirements
RUN python -m pip install --upgrade pip setuptools wheel

# Install basic dependencies first
RUN pip install openai numpy transformers torch

# Install Hugging Face transformers and models
RUN python -c "from transformers import AutoTokenizer, AutoModelForCausalLM; AutoTokenizer.from_pretrained('microsoft/DialoGPT-medium'); AutoModelForCausalLM.from_pretrained('microsoft/DialoGPT-medium')"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create writable directories
RUN mkdir -p /app/instance && chmod -R 777 /app/instance
ENV HF_HOME=/app/transformers_cache
RUN mkdir -p /app/transformers_cache && chmod -R 777 /app/transformers_cache

# Create ../data directory for vector store
RUN mkdir -p /app/data && chmod -R 777 /app/data
RUN mkdir -p /data && chmod -R 777 /data

# Create uploads directory
RUN mkdir -p /app/uploads && chmod -R 777 /app/uploads

# Create logs directory
RUN mkdir -p /app/logs && chmod -R 777 /app/logs
RUN mkdir -p /storage && chmod -R 777 /storage  # Ensure /storage exists before changing permissions

# Pre-download sentence-transformers model
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

EXPOSE 7860

CMD ["python", "app_hf.py"]
