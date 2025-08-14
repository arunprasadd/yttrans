#!/bin/bash

# SSL Setup Script for YouTube Transcript Extractor
# This script sets up Nginx and Certbot in Docker with SSL certificate

set -e

DOMAIN="api.videotoinfographics.com"
EMAIL="darunprasad@hotmail.com"  # Change this to your email

echo "🔐 Full Docker SSL Setup for YouTube Transcript Extractor"
echo "=============================================="
echo "Domain: $DOMAIN"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        print_error "This script should not be run as root for security reasons."
        print_warning "Please run as a regular user with sudo privileges."
        exit 1
    fi
}

# Check if domain points to this server
check_domain() {
    echo "🔍 Checking if domain points to this server..."
    
    SERVER_IP=$(curl -s ifconfig.me || curl -s ipinfo.io/ip || echo "unknown")
    DOMAIN_IP=$(dig +short $DOMAIN | tail -n1)
    
    echo "Server IP: $SERVER_IP"
    echo "Domain IP: $DOMAIN_IP"
    
    if [ "$SERVER_IP" != "$DOMAIN_IP" ]; then
        print_warning "Domain $DOMAIN does not point to this server ($SERVER_IP)"
        print_warning "Please update your DNS records before continuing."
        read -p "Do you want to continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        print_status "Domain correctly points to this server"
    fi
}

# Install required packages
install_packages() {
    echo "📦 Installing required packages..."
    
    # Update package list
    sudo apt update
    
    # Install Docker if not present
    if ! command -v docker &> /dev/null; then
        print_status "Installing Docker..."
        sudo apt install -y docker.io docker-compose-plugin
        sudo systemctl start docker
        sudo systemctl enable docker
        sudo usermod -aG docker $USER
        print_warning "You may need to log out and back in for Docker group changes to take effect"
    else
        print_status "Docker is already installed"
    fi
    
    # Check if docker compose plugin is available, fallback to docker-compose
    if docker compose version &> /dev/null; then
        DOCKER_COMPOSE_CMD="docker compose"
    elif command -v docker-compose &> /dev/null; then
        DOCKER_COMPOSE_CMD="docker-compose"
    else
        print_status "Installing docker-compose..."
        sudo apt install -y docker-compose
        DOCKER_COMPOSE_CMD="docker-compose"
    fi
    
    # Install other utilities
    sudo apt install -y curl dnsutils
}

# Create necessary directories
create_directories() {
    echo "📁 Creating necessary directories..."
    mkdir -p certbot/conf certbot/www nginx/html
    sudo chown -R $USER:$USER certbot nginx
}

# Stop any existing containers and system nginx
stop_services() {
    echo "🛑 Stopping existing services..."
    
    # Stop Docker containers if running
    $DOCKER_COMPOSE_CMD -f docker-compose.prod.yml down 2>/dev/null || true
    
    # Stop system nginx if running
    sudo systemctl stop nginx 2>/dev/null || true
    sudo systemctl disable nginx 2>/dev/null || true
}

# Create initial nginx config for certificate generation
create_initial_nginx() {
    echo "📝 Creating initial nginx configuration for certificate..."
    
    mkdir -p nginx/html
    
    # Create initial nginx config that works without SSL first
    cat > nginx/nginx-initial.conf << EOF
server {
    listen 80;
    server_name $DOMAIN;
    
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    
    location / {
        root /var/www/html;
        index index.html;
    }
}
EOF

    # Create a simple index.html
    cat > nginx/html/index.html << EOF
<!DOCTYPE html>
<html>
<head>
    <title>Setting up SSL...</title>
</head>
<body>
    <h1>Setting up SSL certificate...</h1>
    <p>Please wait while we configure your YouTube Transcript Extractor.</p>
</body>
</html>
EOF
}

# Get SSL certificate
get_certificate() {
    echo "🔐 Obtaining SSL certificate using Docker Certbot..."
    
    # Start nginx with initial config for certificate generation
    docker run -d --name nginx-initial \
        -p 80:80 \
        -v $(pwd)/nginx/nginx-initial.conf:/etc/nginx/conf.d/default.conf \
        -v $(pwd)/nginx/html:/var/www/html \
        -v $(pwd)/certbot/www:/var/www/certbot \
        nginx:alpine
    
    # Wait for nginx to be ready
    sleep 5
    
    # Get certificate using Docker Certbot
    docker run --rm \
        -v $(pwd)/certbot/conf:/etc/letsencrypt \
        -v $(pwd)/certbot/www:/var/www/certbot \
        certbot/certbot:latest \
        certonly --webroot \
        --webroot-path=/var/www/certbot \
        --email $EMAIL \
        --agree-tos \
        --no-eff-email \
        -d $DOMAIN
    
    # Stop initial nginx
    docker stop nginx-initial || true
    docker rm nginx-initial || true
    
    print_status "SSL certificate obtained successfully"
}

# Setup auto-renewal
setup_renewal() {
    echo "🔄 Setting up certificate auto-renewal..."
    
    # The certbot container in docker-compose.prod.yml handles auto-renewal
    # It checks every 12 hours and renews if needed
    
    print_status "Auto-renewal configured"
}

# Start the application
start_application() {
    echo "🚀 Starting application with SSL..."
    
    # Build and start
    $DOCKER_COMPOSE_CMD -f docker-compose.prod.yml up -d --build
    
    print_status "Application started successfully"
}

# Test the setup
test_setup() {
    echo "🧪 Testing the setup..."
    
    sleep 10
    
    # Test HTTP redirect
    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://$DOMAIN || echo "000")
    if [ "$HTTP_STATUS" = "301" ] || [ "$HTTP_STATUS" = "302" ]; then
        print_status "HTTP to HTTPS redirect working"
    else
        print_warning "HTTP redirect may not be working (Status: $HTTP_STATUS)"
    fi
    
    # Test HTTPS
    HTTPS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://$DOMAIN || echo "000")
    if [ "$HTTPS_STATUS" = "200" ]; then
        print_status "HTTPS is working"
    else
        print_warning "HTTPS may not be working (Status: $HTTPS_STATUS)"
    fi
    
    echo ""
    echo "🎉 Setup completed!"
    echo "Your application should be available at: https://$DOMAIN"
    echo ""
    echo "To check logs:"
    echo "  $DOCKER_COMPOSE_CMD -f docker-compose.prod.yml logs -f"
    echo ""
    echo "To restart:"
    echo "  $DOCKER_COMPOSE_CMD -f docker-compose.prod.yml restart"
}

# Main execution
main() {
    check_root
    
    echo "This script will:"
    echo "1. Install Docker (Certbot will run in Docker)"
    echo "2. Check domain DNS configuration"
    echo "3. Obtain SSL certificate using Docker Certbot"
    echo "4. Configure Nginx as reverse proxy in Docker"
    echo "5. Start the application with HTTPS"
    echo ""
    
    read -p "Do you want to continue? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Setup cancelled."
        exit 1
    fi
    
    # Change email if needed
    read -p "Enter your email for SSL certificate (default: $EMAIL): " user_email
    if [ ! -z "$user_email" ]; then
        EMAIL=$user_email
    fi
    
    install_packages
    check_domain
    create_directories
    stop_services
    create_initial_nginx
    get_certificate
    setup_renewal
    start_application
    test_setup
}

# Run main function
main "$@"