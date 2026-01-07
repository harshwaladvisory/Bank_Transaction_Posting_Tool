# Use official Python image
FROM python:3.11-slimFROM public.ecr.aws/docker/library/python:3.11-slim

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