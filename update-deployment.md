# Steps to Update Deployment with Latest Changes

## Quick Update (Recommended)

1. **Navigate to your project directory:**
```bash
cd /path/to/youtube-transcript-extractor
```

2. **Use the management script:**
```bash
bash nginx-commands.sh
```
Select option **10) 🛠️ Rebuild and restart**

This will:
- Stop all containers
- Rebuild with latest code changes
- Restart with new configuration
- Show status

## Manual Steps (Alternative)

### Step 1: Stop Current Services
```bash
# Using docker compose
docker compose -f docker-compose.prod.yml down

# Or using docker-compose
docker-compose -f docker-compose.prod.yml down
```

### Step 2: Rebuild and Start
```bash
# Rebuild and start all services
docker compose -f docker-compose.prod.yml up -d --build

# Or using docker-compose
docker-compose -f docker-compose.prod.yml up -d --build
```

### Step 3: Check Status
```bash
# Check if containers are running
docker compose -f docker-compose.prod.yml ps

# Check logs
docker compose -f docker-compose.prod.yml logs -f
```

### Step 4: Test the Application
```bash
# Test HTTP redirect
curl -I http://api.videotoinfographics.com

# Test HTTPS
curl -I https://api.videotoinfographics.com
```

## Troubleshooting

### If SSL certificates are missing:
```bash
# Run SSL setup again
bash setup-ssl.sh
```

### If containers fail to start:
```bash
# Check logs for errors
docker compose -f docker-compose.prod.yml logs

# Check individual container logs
docker logs nginx-proxy
docker logs youtube-transcript-app
```

### If port conflicts occur:
```bash
# Stop any conflicting services
sudo systemctl stop nginx
sudo systemctl stop apache2

# Check what's using ports 80/443
sudo netstat -tlnp | grep :80
sudo netstat -tlnp | grep :443
```

## Verification Steps

1. **Check containers are running:**
```bash
docker ps
```

2. **Test HTTP to HTTPS redirect:**
```bash
curl -I http://api.videotoinfographics.com
# Should return 301 redirect
```

3. **Test HTTPS is working:**
```bash
curl -I https://api.videotoinfographics.com
# Should return 200 OK
```

4. **Check SSL certificate:**
```bash
openssl s_client -servername api.videotoinfographics.com -connect api.videotoinfographics.com:443 -brief
```

5. **Access application:**
Open browser: https://api.videotoinfographics.com

## Expected Results

- ✅ HTTP requests redirect to HTTPS
- ✅ HTTPS loads with valid SSL certificate
- ✅ Application accessible at https://api.videotoinfographics.com
- ✅ All security headers present
- ✅ WebSocket connections work for Streamlit