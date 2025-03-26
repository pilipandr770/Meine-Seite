FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create directory for audio files
RUN mkdir -p temp_audio && chmod 777 temp_audio

# Environment variables
ENV FLASK_APP=app.app
ENV FLASK_ENV=production

# Run the application
CMD ["python", "-m", "flask", "run", "--host=0.0.0.0"]
