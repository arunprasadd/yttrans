#!/bin/bash

# Docker Nginx Management Commands for YouTube Transcript Extractor

COMPOSE_FILE="docker-compose.prod.yml"
DOMAIN="api.videotoinfographics.com"

# Detect docker compose command
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker compose"
elif command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker-compose"
else
    echo "❌ Docker Compose not found!"
    exit 1
fi

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_status() { echo -e "${GREEN}✅ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }

show_menu() {
    echo ""
    echo "🐳 Docker Nginx SSL Management for YouTube Transcript Extractor"
    echo "======================================================="
    echo ""
    echo "1) 🚀 Start application"
    echo "2) 🛑 Stop application"
    echo "3) 🔄 Restart application"
    echo "4) 📋 View logs"
    echo "5) 📊 Check status"
    echo "6) 🔐 Renew SSL certificate"
    echo "7) 🧪 Test SSL configuration"
    echo "8) 🔍 Check domain DNS"
    echo "9) 📈 View nginx access logs"
    echo "10) 🛠️ Rebuild and restart"
    echo "11) 🧹 Clean up containers"
    echo "12) ❌ Exit"
    echo ""
}

start_app() {
    print_status "Starting application..."
    $DOCKER_COMPOSE_CMD -f $COMPOSE_FILE up -d
    sleep 5
    check_status
}

stop_app() {
    print_status "Stopping application..."
    $DOCKER_COMPOSE_CMD -f $COMPOSE_FILE down
}

restart_app() {
    print_status "Restarting application..."
    $DOCKER_COMPOSE_CMD -f $COMPOSE_FILE restart
    sleep 5
    check_status
}

view_logs() {
    echo "📋 Application logs (Press Ctrl+C to exit):"
    $DOCKER_COMPOSE_CMD -f $COMPOSE_FILE logs -f
}

check_status() {
    echo "📊 Application Status:"
    echo "====================="
    
    # Check containers
    if $DOCKER_COMPOSE_CMD -f $COMPOSE_FILE ps | grep -q "Up"; then
        print_status "Containers are running"
        $DOCKER_COMPOSE_CMD -f $COMPOSE_FILE ps
    else
        print_error "Containers are not running"
        return 1
    fi
    
    echo ""
    
    # Check HTTP redirect
    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://$DOMAIN 2>/dev/null || echo "000")
    if [ "$HTTP_STATUS" = "301" ] || [ "$HTTP_STATUS" = "302" ]; then
        print_status "HTTP to HTTPS redirect: Working"
    else
        print_warning "HTTP redirect status: $HTTP_STATUS"
    fi
    
    # Check HTTPS
    HTTPS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://$DOMAIN 2>/dev/null || echo "000")
    if [ "$HTTPS_STATUS" = "200" ]; then
        print_status "HTTPS status: Working"
        echo "🌐 Application URL: https://$DOMAIN"
    else
        print_warning "HTTPS status: $HTTPS_STATUS"
    fi
    
    # Check SSL certificate
    SSL_EXPIRY=$(echo | openssl s_client -servername $DOMAIN -connect $DOMAIN:443 2>/dev/null | openssl x509 -noout -dates 2>/dev/null | grep notAfter | cut -d= -f2)
    if [ ! -z "$SSL_EXPIRY" ]; then
        print_status "SSL certificate expires: $SSL_EXPIRY"
    fi
}

renew_ssl() {
    print_status "Renewing SSL certificate..."
    
    # Use the renewal script if it exists
    if [ -f "renew-ssl.sh" ]; then
        ./renew-ssl.sh
    else
        # Fallback to manual renewal
        sudo certbot renew --quiet --webroot --webroot-path=./nginx/html
        sudo cp -r /etc/letsencrypt/* ssl/ 2>/dev/null || true
        sudo cp -r /var/lib/letsencrypt/* ssl-lib/ 2>/dev/null || true
        sudo chown -R $USER:$USER ssl ssl-lib
        restart_app
    fi
    
    if [ $? -eq 0 ]; then
        print_status "Certificate renewed successfully"
    else
        print_error "Certificate renewal failed"
    fi
}

test_ssl() {
    echo "🧪 Testing SSL configuration..."
    echo "==============================="
    
    # Test SSL Labs (if available)
    echo "🔍 Basic SSL test:"
    echo | openssl s_client -servername $DOMAIN -connect $DOMAIN:443 2>/dev/null | openssl x509 -noout -text | grep -E "(Subject:|Issuer:|Not Before|Not After)"
    
    echo ""
    echo "🌐 Online SSL test:"
    echo "Visit: https://www.ssllabs.com/ssltest/analyze.html?d=$DOMAIN"
}

check_dns() {
    echo "🔍 Checking DNS configuration..."
    echo "==============================="
    
    SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || curl -s ipinfo.io/ip 2>/dev/null || echo "unknown")
    DOMAIN_IP=$(dig +short $DOMAIN 2>/dev/null | tail -n1)
    
    echo "Server IP: $SERVER_IP"
    echo "Domain IP: $DOMAIN_IP"
    
    if [ "$SERVER_IP" = "$DOMAIN_IP" ]; then
        print_status "DNS configuration is correct"
    else
        print_warning "DNS configuration may be incorrect"
    fi
}

view_nginx_logs() {
    echo "📈 Nginx access logs (Press Ctrl+C to exit):"
    docker logs -f nginx-proxy 2>/dev/null || print_error "Nginx container not running"
}

rebuild_app() {
    print_status "Rebuilding and restarting application..."
    $DOCKER_COMPOSE_CMD -f $COMPOSE_FILE down
    $DOCKER_COMPOSE_CMD -f $COMPOSE_FILE up -d --build
    sleep 5
    check_status
}

cleanup() {
    print_warning "This will remove all containers and images. Are you sure? (y/N)"
    read -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Cleaning up..."
        $DOCKER_COMPOSE_CMD -f $COMPOSE_FILE down --rmi all --volumes --remove-orphans
        docker system prune -f
        print_status "Cleanup completed"
    fi
}

# Main loop
main() {
    while true; do
        show_menu
        read -p "Enter your choice (1-12): " choice
        
        case $choice in
            1) start_app ;;
            2) stop_app ;;
            3) restart_app ;;
            4) view_logs ;;
            5) check_status ;;
            6) renew_ssl ;;
            7) test_ssl ;;
            8) check_dns ;;
            9) view_nginx_logs ;;
            10) rebuild_app ;;
            11) cleanup ;;
            12) 
                echo "👋 Goodbye!"
                exit 0
                ;;
            *)
                print_error "Invalid option. Please choose 1-12."
                ;;
        esac
        
        echo ""
        read -p "Press Enter to continue..."
    done
}

# Check if docker-compose file exists
if [ ! -f "$COMPOSE_FILE" ]; then
    print_error "docker-compose.prod.yml not found!"
    print_warning "Please run the SSL setup script first."
    exit 1
fi

main