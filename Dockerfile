FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    bash \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Make scripts executable
RUN chmod +x prestart.sh

# Create directory for audio files and ensure permissions
RUN mkdir -p temp_audio && chmod 777 temp_audio
RUN mkdir -p instance && chmod 777 instance

# Environment variables
ENV FLASK_APP=run.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Run the application with Gunicorn in production
ENTRYPOINT ["bash", "-c"]
CMD ["./prestart.sh && gunicorn run:app --workers=3 --bind=0.0.0.0:${PORT:-5000} --log-level debug"]
