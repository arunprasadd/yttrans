#!/bin/bash

# YouTube Transcript Extractor - Docker Setup Script
# This script helps you build and run the application using Docker

set -e

echo "🐳 YouTube Transcript Extractor - Docker Setup"
echo "=============================================="

# Function to check if Docker is installed
check_docker() {
    if ! command -v docker > /dev/null 2>&1; then
        echo "❌ Docker is not installed. Please install Docker first."
        echo "Visit: https://docs.docker.com/get-docker/"
        exit 1
    fi
    echo "✅ Docker is installed"
}

# Function to check if Docker Compose is installed
check_docker_compose() {
    if ! command -v docker-compose > /dev/null 2>&1; then
        echo "⚠️  Docker Compose is not installed. Using docker compose instead."
        DOCKER_COMPOSE_CMD="docker compose"
    else
        echo "✅ Docker Compose is installed"
        DOCKER_COMPOSE_CMD="docker-compose"
    fi
}

# Function to build the Docker image
build_image() {
    echo "🔨 Building Docker image..."
    docker build -t youtube-transcript-extractor .
    echo "✅ Docker image built successfully"
}

# Function to run with Docker Compose
run_with_compose() {
    echo "🚀 Starting application with Docker Compose..."
    $DOCKER_COMPOSE_CMD up -d
    echo "✅ Application started successfully"
    echo "🌐 Access the application at: http://localhost:8501"
}

# Function to run with Docker only
run_with_docker() {
    echo "🚀 Starting application with Docker..."
    docker run -d \
        --name youtube-transcript-app \
        -p 8501:8501 \
        --restart unless-stopped \
        youtube-transcript-extractor
    echo "✅ Application started successfully"
    echo "🌐 Access the application at: http://localhost:8501"
}

# Function to stop the application
stop_app() {
    echo "🛑 Stopping application..."
    if command -v docker-compose > /dev/null 2>&1 || command -v docker > /dev/null 2>&1; then
        $DOCKER_COMPOSE_CMD down 2>/dev/null || docker stop youtube-transcript-app 2>/dev/null || true
        docker rm youtube-transcript-app 2>/dev/null || true
    fi
    echo "✅ Application stopped"
}

# Function to show logs
show_logs() {
    echo "📋 Showing application logs..."
    if docker ps | grep -q youtube-transcript-app; then
        docker logs -f youtube-transcript-app
    else
        echo "❌ Application is not running"
    fi
}

# Function to show status
show_status() {
    echo "📊 Application Status:"
    if docker ps | grep -q youtube-transcript-app; then
        echo "✅ Application is running"
        echo "🌐 Access at: http://localhost:8501"
        docker ps | grep youtube-transcript-app
    else
        echo "❌ Application is not running"
    fi
}

# Main menu
show_menu() {
    echo ""
    echo "Choose an option:"
    echo "1) Build and run (Docker Compose - Recommended)"
    echo "2) Build and run (Docker only)"
    echo "3) Stop application"
    echo "4) Show logs"
    echo "5) Show status"
    echo "6) Rebuild and restart"
    echo "7) Exit"
    echo ""
}

# Main script
main() {
    check_docker
    check_docker_compose
    
    while true; do
        show_menu
        read -p "Enter your choice (1-7): " choice
        
        case $choice in
            1)
                stop_app
                build_image
                run_with_compose
                ;;
            2)
                stop_app
                build_image
                run_with_docker
                ;;
            3)
                stop_app
                ;;
            4)
                show_logs
                ;;
            5)
                show_status
                ;;
            6)
                stop_app
                build_image
                run_with_compose
                ;;
            7)
                echo "👋 Goodbye!"
                exit 0
                ;;
            *)
                echo "❌ Invalid option. Please choose 1-7."
                ;;
        esac
        
        echo ""
        read -p "Press Enter to continue..."
    done
}

# Run main function
main