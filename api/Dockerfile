# Security API Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy API code
COPY api/ .

# Expose port
EXPOSE 8000

# Run API
CMD ["uvicorn", "security-api:app", "--host", "0.0.0.0", "--port", "8000"]
