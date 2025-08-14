#!/bin/bash

# SSL Certificate Renewal Script for Full Docker Setup
# This script manually triggers certificate renewal using Docker Certbot

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
if docker compose version > /dev/null 2>&1; then
    DOCKER_COMPOSE_CMD="docker compose"
elif command -v docker-compose > /dev/null 2>&1; then
    DOCKER_COMPOSE_CMD="docker-compose"
else
    print_error "Docker Compose not found!"
    exit 1
fi

echo "🔄 SSL Certificate Renewal for $DOMAIN"
echo "======================================"

# Change to script directory
cd "$(dirname "$0")"

# Check if certificate directory exists
if [ ! -d "certbot/conf/live/$DOMAIN" ]; then
    print_error "SSL certificates not found. Please run initial setup first."
    exit 1
fi

# Renew certificate using Docker Certbot
print_status "Renewing SSL certificate..."
docker run --rm \
    -v $(pwd)/certbot/conf:/etc/letsencrypt \
    -v $(pwd)/certbot/www:/var/www/certbot \
    certbot/certbot:latest \
    renew --quiet

# Reload nginx to use renewed certificates
print_status "Reloading nginx with renewed certificates..."
docker exec nginx-proxy nginx -s reload

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