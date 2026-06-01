FROM python:3.11-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Create data directories
RUN mkdir -p data/raw/writings data/raw/interviews data/raw/youtube data/raw/patents data/processed

# Make startup script executable
RUN chmod +x start.sh

# HF Spaces uses port 7860
EXPOSE 7860

# Run startup script
CMD ["bash", "start.sh"]
