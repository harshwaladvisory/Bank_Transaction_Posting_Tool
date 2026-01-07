#!/bin/bash
# echo "Starting container..."
# docker run -d \
#   --name security-deposit-container \
#   -p 5000:5000 \
#   --restart unless-stopped \
#   230138717288.dkr.ecr.us-east-2.amazonaws.com/security-deposit-repo:latest

#!/bin/bash
set -e

echo "Starting application..."

# AWS Configuration
AWS_REGION="us-east-2"
ECR_REPO_URI="230138717288.dkr.ecr.us-east-2.amazonaws.com/bank_transaction_posting_tool"
IMAGE_TAG="UAT_latest"

# Login to ECR
echo "Logging in to Amazon ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REPO_URI

# Pull the latest image
echo "Pulling Docker image from ECR..."
docker pull $ECR_REPO_URI:$IMAGE_TAG

# Stop and remove existing container if running
echo "Stopping existing container..."
docker stop bank_posting_tool || true
docker rm bank_posting_tool || true

# Run the new container
echo "Starting new container..."
docker run -d --network host \
  --name bank_posting_tool \
  -p 6002:6002 \
  --restart unless-stopped \
  $ECR_REPO_URI:$IMAGE_TAG

echo "Application started successfully!"
docker ps | grep flask-app