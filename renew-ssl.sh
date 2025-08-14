#!/bin/bash

# SSL Certificate Renewal Script for Dockerized Setup
# This script renews SSL certificates and updates the Docker containers

set -e

DOMAIN="api.videotoinfographics.com"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_status() { echo -e "${GREEN}✅ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }

# Detect docker compose command
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker compose"
elif command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker-compose"
else
    print_error "Docker Compose not found!"
    exit 1
fi

echo "🔄 SSL Certificate Renewal for $DOMAIN"
echo "======================================"

# Change to script directory
cd "$(dirname "$0")"

# Check if certificates exist
if [ ! -d "ssl/live/$DOMAIN" ]; then
    print_error "SSL certificates not found. Please run initial setup first."
    exit 1
fi

# Stop nginx container temporarily for renewal
print_status "Stopping nginx container for renewal..."
$DOCKER_COMPOSE_CMD -f docker-compose.prod.yml stop nginx

# Start temporary nginx for renewal
print_status "Starting temporary nginx for certificate renewal..."
docker run -d \
    --name nginx-renewal \
    -p 80:80 \
    -v $(pwd)/nginx/html:/var/www/html \
    -v $(pwd)/nginx/nginx-temp.conf:/etc/nginx/conf.d/default.conf \
    nginx:alpine

# Wait for nginx to start
sleep 3

# Renew certificate
print_status "Renewing SSL certificate..."
sudo certbot renew \
    --webroot \
    --webroot-path=$(pwd)/nginx/html \
    --quiet

# Stop temporary nginx
docker stop nginx-renewal
docker rm nginx-renewal

# Copy renewed certificates
print_status "Updating certificate files..."
sudo cp -r /etc/letsencrypt/* ssl/ 2>/dev/null || true
sudo cp -r /var/lib/letsencrypt/* ssl-lib/ 2>/dev/null || true

# Fix permissions
sudo chown -R $USER:$USER ssl ssl-lib

# Restart the application
print_status "Restarting application with renewed certificates..."
$DOCKER_COMPOSE_CMD -f docker-compose.prod.yml start nginx

# Wait for services to be ready
sleep 5

# Test the renewal
print_status "Testing renewed certificate..."
HTTPS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://$DOMAIN 2>/dev/null || echo "000")
if [ "$HTTPS_STATUS" = "200" ]; then
    print_status "Certificate renewal successful!"
    print_status "Application is running at: https://$DOMAIN"
else
    print_warning "Certificate may not be working properly (Status: $HTTPS_STATUS)"
fi

echo ""
print_status "SSL certificate renewal completed!"