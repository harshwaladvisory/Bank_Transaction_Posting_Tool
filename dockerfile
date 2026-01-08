# Use official Python image
FROM public.ecr.aws/docker/library/python:3.11-slim
RUN apt-get update && apt-get install -y \
    poppler-utils \
    tesseract-ocr \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory inside container
WORKDIR /app

# Copy all files from current folder to /app in container
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port (optional – only if your app uses it)
EXPOSE 6002

# Run the application
CMD ["python", "app.py"]
