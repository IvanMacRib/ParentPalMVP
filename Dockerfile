FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Print contents of the directory (for debugging)
RUN ls -la

# Expose the port the app runs on
EXPOSE 8080

# Use the PORT environment variable provided by Cloud Run
# Add a default value as a fallback
CMD exec uvicorn app.api:app --host 0.0.0.0 --port ${PORT:-8080}