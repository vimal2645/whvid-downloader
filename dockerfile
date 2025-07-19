# Use official Python slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy app files
COPY . .

# Install system dependencies
RUN apt-get update && apt-get install -y ffmpeg curl && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Expose the port used by the app
EXPOSE 5000

# Start the app with Gunicorn
CMD ["gunicorn", "app:app", "-b", "0.0.0.0:5000"]
