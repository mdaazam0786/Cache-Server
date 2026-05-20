# Equivalent of the Java Dockerfile — uses Python 3.12 slim
FROM python:3.12-slim

# Working directory
WORKDIR /app

# Install dependencies first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY app/ ./app/

# Expose port
EXPOSE 8081

# Run the server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8081"]
