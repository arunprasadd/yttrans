#!/bin/bash

# SSL Setup Script for YouTube Transcript Extractor
# This script sets up Nginx with SSL certificate using Certbot

set -e

DOMAIN="api.videotoinfographics.com"
EMAIL="admin@videotoinfographics.com"  # Change this to your email

echo "🔐 SSL Setup for YouTube Transcript Extractor"
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
        sudo apt install -y docker.io docker-compose
        sudo systemctl start docker
        sudo systemctl enable docker
        sudo usermod -aG docker $USER
        print_warning "You may need to log out and back in for Docker group changes to take effect"
    else
        print_status "Docker is already installed"
    fi
    
    # Install Certbot
    if ! command -v certbot &> /dev/null; then
        print_status "Installing Certbot..."
        sudo apt install -y certbot python3-certbot-nginx
    else
        print_status "Certbot is already installed"
    fi
    
    # Install other utilities
    sudo apt install -y curl dig nginx
}

# Stop any existing nginx service
stop_nginx() {
    echo "🛑 Stopping system nginx if running..."
    sudo systemctl stop nginx 2>/dev/null || true
    sudo systemctl disable nginx 2>/dev/null || true
}

# Create initial nginx config for certificate generation
create_initial_nginx() {
    echo "📝 Creating initial nginx configuration..."
    
    mkdir -p nginx
    
    cat > nginx/nginx-initial.conf << EOF
server {
    listen 80;
    server_name $DOMAIN;
    
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    
    location / {
        return 301 https://\$server_name\$request_uri;
    }
}
EOF
}

# Get SSL certificate
get_certificate() {
    echo "🔐 Obtaining SSL certificate..."
    
    # Create directory for certbot challenges
    sudo mkdir -p /var/www/certbot
    
    # Run nginx temporarily for certificate generation
    docker run --rm -d \
        --name nginx-temp \
        -p 80:80 \
        -v $(pwd)/nginx/nginx-initial.conf:/etc/nginx/conf.d/default.conf \
        -v /var/www/certbot:/var/www/certbot \
        nginx:alpine
    
    # Wait for nginx to start
    sleep 5
    
    # Get certificate
    sudo certbot certonly \
        --webroot \
        --webroot-path=/var/www/certbot \
        --email $EMAIL \
        --agree-tos \
        --no-eff-email \
        -d $DOMAIN
    
    # Stop temporary nginx
    docker stop nginx-temp || true
    
    print_status "SSL certificate obtained successfully"
}

# Setup auto-renewal
setup_renewal() {
    echo "🔄 Setting up certificate auto-renewal..."
    
    # Create renewal script
    sudo tee /etc/cron.d/certbot-renew > /dev/null << EOF
0 12 * * * root certbot renew --quiet --deploy-hook "docker-compose -f $(pwd)/docker-compose.prod.yml restart nginx"
EOF
    
    print_status "Auto-renewal configured"
}

# Start the application
start_application() {
    echo "🚀 Starting application with SSL..."
    
    # Stop any existing containers
    docker-compose -f docker-compose.prod.yml down 2>/dev/null || true
    
    # Build and start
    docker-compose -f docker-compose.prod.yml up -d --build
    
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
    echo "  docker-compose -f docker-compose.prod.yml logs -f"
    echo ""
    echo "To restart:"
    echo "  docker-compose -f docker-compose.prod.yml restart"
}

# Main execution
main() {
    check_root
    
    echo "This script will:"
    echo "1. Install Docker and Certbot"
    echo "2. Check domain DNS configuration"
    echo "3. Obtain SSL certificate from Let's Encrypt"
    echo "4. Configure Nginx as reverse proxy"
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
    stop_nginx
    create_initial_nginx
    get_certificate
    setup_renewal
    start_application
    test_setup
}

# Run main function
main "$@"