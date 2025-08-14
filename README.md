# YouTube Transcript Extractor

A Streamlit web application that extracts transcripts from YouTube videos with available captions/subtitles.

## 🐳 Production Setup with Docker + SSL (Recommended for Servers)

### Prerequisites for SSL Setup
- Linux server with public IP
- Domain name pointing to your server (`api.videotoinfographics.com`)
- Docker and Docker Compose
- Port 80 and 443 open in firewall

### SSL Setup Steps

1. **Clone/Create project directory:**
```bash
mkdir youtube-transcript-extractor
cd youtube-transcript-extractor
```

2. **Create all project files** (app.py, Dockerfile, etc.)

3. **Make setup script executable:**
```bash
chmod +x setup-ssl.sh
chmod +x nginx-commands.sh
```

4. **Run SSL setup:**
```bash
./setup-ssl.sh
```

This script will:
- Install Docker and Certbot automatically
- Create SSL certificates using Let's Encrypt
- Set up Nginx as a reverse proxy (running in Docker)
- Configure automatic certificate renewal
- Start the entire application stack

5. **Access your application:**
- Visit: `https://api.videotoinfographics.com`
- HTTP requests automatically redirect to HTTPS

### SSL Management Commands

Use the management script for easy operations:
```bash
./nginx-commands.sh
```

Available options:
- Start/Stop/Restart application
- View logs and status
- Renew SSL certificates
- Test SSL configuration
- Check DNS settings
- Rebuild containers
- Clean up resources

### Manual SSL Commands

```bash
# Start with SSL (all containers)
docker-compose -f docker-compose.prod.yml up -d

# Or using docker compose plugin
docker compose -f docker-compose.prod.yml up -d

# View logs
docker compose -f docker-compose.prod.yml logs -f

# Restart
docker compose -f docker-compose.prod.yml restart

# Stop
docker compose -f docker-compose.prod.yml down

# Renew SSL certificate
./renew-ssl.sh
```

### Key Features of Docker Setup

- **Fully Containerized**: Both application and Nginx run in Docker
- **Automatic SSL**: Let's Encrypt certificates with auto-renewal
- **Security Headers**: HSTS, XSS protection, content security
- **Health Checks**: Container health monitoring
- **Easy Management**: Simple scripts for all operations
- **Scalable**: Easy to move to cloud or scale horizontally

## Quick Start with Docker (Recommended)

### Prerequisites
- Docker installed on your system
- Docker Compose (optional but recommended)

### Option 1: Using the Setup Script (Easiest)

1. **Make the setup script executable:**
```bash
chmod +x docker-setup.sh
```

2. **Run the setup script:**
```bash
./docker-setup.sh
```

3. **Follow the interactive menu** to build and run the application

### Option 2: Using Docker Compose

1. **Build and run:**
```bash
docker-compose up -d
```

2. **Access the application:**
Open your browser and go to `http://localhost:8501`

3. **Stop the application:**
```bash
docker-compose down
```

### Option 3: Using Docker Only

1. **Build the image:**
```bash
docker build -t youtube-transcript-extractor .
```

2. **Run the container:**
```bash
docker run -d -p 8501:8501 --name youtube-transcript-app youtube-transcript-extractor
```

3. **Stop the container:**
```bash
docker stop youtube-transcript-app
docker rm youtube-transcript-app
```

## Docker Commands Reference

```bash
# Build image
docker build -t youtube-transcript-extractor .

# Run container
docker run -d -p 8501:8501 --name youtube-transcript-app youtube-transcript-extractor

# View logs
docker logs youtube-transcript-app

# Stop container
docker stop youtube-transcript-app

# Remove container
docker rm youtube-transcript-app

# View running containers
docker ps
```

## Features

- 📺 Extract transcripts from any YouTube video
- ⏱️ Display transcripts with timestamps
- 📄 View plain text version without timestamps
- 🖼️ Video thumbnail preview
- 💾 Download transcripts in multiple formats
- 📊 Display transcript statistics (word count, duration)

## Manual Setup (Without Docker)

### Prerequisites

- Python 3.8 or higher

### Installation

1. Clone this repository:
```bash
git clone <your-repo-url>
cd youtube-transcript-extractor
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
streamlit run app.py
```

## Usage

1. Open the application in your browser (usually `http://localhost:8501`)
2. Paste a YouTube video URL in the input field
3. Click "Extract Transcript" to get the transcript
4. View the transcript with timestamps or as plain text
5. Download the transcript in your preferred format

## How it Works

1. **URL Processing**: Supports multiple YouTube URL formats
2. **Transcript Extraction**: Uses `youtube-transcript-api` to extract captions/subtitles
3. **Formatting**: Displays transcripts with timestamps and provides plain text version
4. **Download**: Allows downloading in multiple formats

## Requirements

- The YouTube video must have captions/subtitles available (auto-generated or manual)

## Limitations

- Only works with videos that have available transcripts
- Requires internet connection for transcript extraction
- Cannot extract transcripts from private or restricted videos

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is open source and available under the [MIT License](LICENSE).