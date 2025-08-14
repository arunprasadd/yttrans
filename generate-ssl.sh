#!/bin/bash

# SSL Certificate Generation Script
# This script generates SSL certificates when nginx is already running

set -e

DOMAIN="api.videotoinfographics.com"
EMAIL="darunprasad@hotmail.com"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_status() { echo -e "${GREEN}✅ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }

echo "🔐 Generating SSL Certificate for $DOMAIN"
echo "=========================================="

# Step 1: Stop all containers to free up port 80
print_status "Stopping all containers..."
docker compose -f docker-compose.prod.yml down || true

# Step 2: Create directories
print_status "Creating certificate directories..."
mkdir -p certbot/conf certbot/www

# Step 3: Generate certificate using standalone mode (no nginx running)
print_status "Generating SSL certificate..."
docker run --rm \
    -v $(pwd)/certbot/conf:/etc/letsencrypt \
    -v $(pwd)/certbot/www:/var/www/certbot \
    -p 80:80 \
    certbot/certbot:latest \
    certonly --standalone \
    --email $EMAIL \
    --agree-tos \
    --no-eff-email \
    -d $DOMAIN

if [ $? -eq 0 ]; then
    print_status "SSL certificate generated successfully!"
else
    print_error "Failed to generate SSL certificate"
    exit 1
fi

# Step 4: Update nginx config to use HTTPS
print_status "Updating nginx configuration for HTTPS..."
cat > nginx/nginx.conf << 'EOF'
# HTTP server - redirect to HTTPS
server {
    listen 80;
    server_name api.videotoinfographics.com;
    
    # Let's Encrypt challenge location
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    
    # Redirect all HTTP to HTTPS
    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS server
server {
    listen 443 ssl;
    http2 on;
    server_name api.videotoinfographics.com;
    
    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/api.videotoinfographics.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.videotoinfographics.com/privkey.pem;
    
    # SSL Security Settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES128-SHA256:ECDHE-RSA-AES256-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self' wss: https:;" always;
    
    # Let's Encrypt challenge location
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    
    # Proxy to Streamlit app
    location / {
        proxy_pass http://youtube-transcript-app:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Port $server_port;
        
        # Streamlit specific headers
        proxy_buffering off;
        proxy_read_timeout 86400;
        proxy_redirect off;
        proxy_cache_bypass $http_upgrade;
    }

    # WebSocket support for Streamlit
    location /_stcore/stream {
        proxy_pass http://youtube-transcript-app:8501/_stcore/stream;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # Health check endpoint
    location /_stcore/health {
        proxy_pass http://youtube-transcript-app:8501/_stcore/health;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Static files caching
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        proxy_pass http://youtube-transcript-app:8501;
        proxy_set_header Host $host;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF

# Step 5: Start the application with HTTPS
print_status "Starting application with HTTPS..."
docker compose -f docker-compose.prod.yml up -d

# Step 6: Wait and test
print_status "Waiting for services to start..."
sleep 10

# Test HTTPS
HTTPS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://$DOMAIN 2>/dev/null || echo "000")
if [ "$HTTPS_STATUS" = "200" ]; then
    print_status "HTTPS is working!"
    print_status "🌐 Application URL: https://$DOMAIN"
else
    print_warning "HTTPS status: $HTTPS_STATUS"
    print_warning "Check logs: docker compose -f docker-compose.prod.yml logs"
fi

echo ""
print_status "SSL setup completed!"
print_status "Your application should be available at: https://$DOMAIN"