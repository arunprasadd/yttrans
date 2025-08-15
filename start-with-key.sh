#!/bin/bash

# YouTube Transcript Extractor - Start with OpenAI Key
echo "🚀 Starting YouTube Transcript Extractor with OpenAI API"
echo "=================================================="

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found!"
    echo "Creating .env file template..."
    cat > .env << EOF
# OpenAI API Key for GPT-4 summaries
OPENAI_API_KEY=sk-your-actual-openai-key-here

# Proxy settings (already configured in code)
PROXY_USERNAME=labvizce-staticresidential
PROXY_PASSWORD=x2za3x15c9ah
EOF
    echo "✅ Created .env file"
    echo "📝 Please edit .env file and add your OpenAI API key"
    echo "Then run this script again."
    exit 1
fi

# Load environment variables
source .env

# Check if OpenAI key is set
if [ "$OPENAI_API_KEY" = "sk-your-actual-openai-key-here" ] || [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  OpenAI API key not set in .env file"
    echo "📝 Please edit .env file and add your real OpenAI API key"
    echo "Example: OPENAI_API_KEY=sk-proj-abc123..."
    read -p "Continue without AI summaries? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Detect docker compose command
if docker compose version > /dev/null 2>&1; then
    DOCKER_COMPOSE_CMD="docker compose"
elif command -v docker-compose > /dev/null 2>&1; then
    DOCKER_COMPOSE_CMD="docker-compose"
else
    echo "❌ Docker Compose not found!"
    exit 1
fi

echo "🛑 Stopping existing containers..."
$DOCKER_COMPOSE_CMD down

echo "🔨 Building and starting with OpenAI API key..."
$DOCKER_COMPOSE_CMD up -d --build

echo "⏳ Waiting for application to start..."
sleep 10

# Check if container is running
if docker ps | grep -q youtube-transcript-app; then
    echo "✅ Application started successfully!"
    echo "🌐 Access at: http://localhost:8501"
    echo ""
    echo "📊 Status:"
    if [ ! -z "$OPENAI_API_KEY" ] && [ "$OPENAI_API_KEY" != "sk-your-actual-openai-key-here" ]; then
        echo "  ✅ OpenAI API configured - AI summaries enabled"
    else
        echo "  ⚠️  OpenAI API not configured - transcription only"
    fi
    echo "  ✅ Proxy configured"
    echo ""
    echo "📋 Useful commands:"
    echo "  View logs: $DOCKER_COMPOSE_CMD logs -f"
    echo "  Stop app:  $DOCKER_COMPOSE_CMD down"
    echo "  Restart:   $DOCKER_COMPOSE_CMD restart"
else
    echo "❌ Failed to start application"
    echo "📋 Check logs: $DOCKER_COMPOSE_CMD logs"
fi