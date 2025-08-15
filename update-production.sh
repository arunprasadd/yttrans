#!/bin/bash

# Update Production with OpenAI API Key
echo "🔄 Updating Production YouTube Transcript Extractor"
echo "================================================="

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

echo "🛑 Stopping production containers..."
$DOCKER_COMPOSE_CMD -f docker-compose.prod.yml down

echo "🔨 Rebuilding and starting with OpenAI API key..."
$DOCKER_COMPOSE_CMD -f docker-compose.prod.yml up -d --build

echo "⏳ Waiting for services to start..."
sleep 15

# Test the application
echo "🧪 Testing the application..."
HTTPS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://api.videotoinfographics.com 2>/dev/null || echo "000")

if [ "$HTTPS_STATUS" = "200" ]; then
    echo "✅ Application updated successfully!"
    echo "🌐 Access at: https://api.videotoinfographics.com"
    echo ""
    echo "📊 Status:"
    if [ ! -z "$OPENAI_API_KEY" ] && [ "$OPENAI_API_KEY" != "sk-your-actual-openai-key-here" ]; then
        echo "  ✅ OpenAI API configured - AI summaries enabled"
    else
        echo "  ⚠️  OpenAI API not configured - transcription only"
    fi
    echo "  ✅ SSL certificate active"
    echo "  ✅ Proxy configured"
    echo ""
    echo "📋 Useful commands:"
    echo "  View logs: $DOCKER_COMPOSE_CMD -f docker-compose.prod.yml logs -f"
    echo "  Restart:   $DOCKER_COMPOSE_CMD -f docker-compose.prod.yml restart"
    echo "  Status:    bash nginx-commands.sh"
else
    echo "❌ Application may not be working properly (Status: $HTTPS_STATUS)"
    echo "📋 Check logs: $DOCKER_COMPOSE_CMD -f docker-compose.prod.yml logs"
fi