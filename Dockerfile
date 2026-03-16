FROM python:3.12-slim

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code and data
COPY hmas/ hmas/
COPY scripts/ scripts/
COPY data/ data/
COPY frontend/dist/ frontend/dist/
COPY .env .env

# Expose port
EXPOSE 8000

# Start the server
CMD ["python", "-m", "uvicorn", "hmas.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
