FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create directory for audio files and ensure permissions
RUN mkdir -p temp_audio && chmod 777 temp_audio
RUN mkdir -p instance && chmod 777 instance

# Environment variables
ENV FLASK_APP=run.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Run the application with Gunicorn in production
ENTRYPOINT ["sh", "-c"]
CMD ["gunicorn run:app --workers=3 --bind=0.0.0.0:${PORT:-5000}"]
