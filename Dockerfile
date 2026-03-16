FROM python:3.12-slim

WORKDIR /app

# Install Node.js for frontend build
RUN apt-get update && apt-get install -y curl && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Install CPU-only PyTorch first (avoids 3GB+ CUDA downloads)
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Install remaining Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code and data
COPY hmas/ hmas/
COPY scripts/ scripts/
COPY data/ data/

# Build frontend
COPY frontend/ frontend/
RUN cd frontend && npm install && npm run build

# Expose port
EXPOSE 8000

# Start the server
CMD ["python", "-m", "uvicorn", "hmas.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
