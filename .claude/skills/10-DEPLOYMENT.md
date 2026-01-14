# Skill 10: Deployment & Production

## Objective
Deploy the Voice AI Platform to production with proper security, monitoring, and scalability.

---

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           PRODUCTION DEPLOYMENT                                  │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                         Load Balancer / CDN                              │    │
│  │                    (Cloudflare / AWS ALB / Nginx)                        │    │
│  │                                                                          │    │
│  │  HTTPS ───▶ Admin UI (Next.js)                                          │    │
│  │  HTTPS ───▶ Backend API (FastAPI)                                       │    │
│  │  WSS   ───▶ LiveKit Server                                              │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                         Application Servers                              │    │
│  │                                                                          │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                   │    │
│  │  │   Backend    │  │   Admin UI   │  │   n8n        │                   │    │
│  │  │   (FastAPI)  │  │   (Next.js)  │  │   (MCP)      │                   │    │
│  │  │   Port 8000  │  │   Port 3000  │  │   Port 5678  │                   │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘                   │    │
│  │                                                                          │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                   │    │
│  │  │  LiveKit     │  │  LightRAG    │  │ Voice Agent  │                   │    │
│  │  │  Server      │  │              │  │  (Workers)   │                   │    │
│  │  │  Port 7880   │  │  Port 9621   │  │              │                   │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘                   │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                         Data Layer                                       │    │
│  │                                                                          │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                   │    │
│  │  │  PostgreSQL  │  │    Redis     │  │  Object      │                   │    │
│  │  │  (Primary)   │  │   (Cache)    │  │  Storage     │                   │    │
│  │  │              │  │              │  │  (S3/Minio)  │                   │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘                   │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                         Monitoring                                       │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                   │    │
│  │  │  Prometheus  │  │   Grafana    │  │   Sentry     │                   │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘                   │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Step 1: Complete Docker Compose (Production)

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

x-common-env: &common-env
  TZ: UTC

services:
  # ============== Database ==============
  postgres:
    image: postgres:16-alpine
    container_name: vai-postgres
    environment:
      <<: *common-env
      POSTGRES_USER: ${POSTGRES_USER:-postgres}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB:-voice_ai_platform}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./configs/postgres/init.sql:/docker-entrypoint-initdb.d/init.sql:ro
    ports:
      - "127.0.0.1:5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-postgres}"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped
    networks:
      - vai-network

  redis:
    image: redis:7-alpine
    container_name: vai-redis
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    ports:
      - "127.0.0.1:6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "-a", "${REDIS_PASSWORD}", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped
    networks:
      - vai-network

  # ============== Backend API ==============
  backend:
    build:
      context: ./src/backend
      dockerfile: Dockerfile
    container_name: vai-backend
    environment:
      <<: *common-env
      DATABASE_URL: postgresql+asyncpg://${POSTGRES_USER:-postgres}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB:-voice_ai_platform}
      REDIS_URL: redis://:${REDIS_PASSWORD}@redis:6379/0
      JWT_SECRET_KEY: ${JWT_SECRET_KEY}
      LIVEKIT_URL: ${LIVEKIT_URL}
      LIVEKIT_API_KEY: ${LIVEKIT_API_KEY}
      LIVEKIT_API_SECRET: ${LIVEKIT_API_SECRET}
      LIGHTRAG_URL: http://lightrag:9621
      LIGHTRAG_API_KEY: ${LIGHTRAG_API_KEY}
      N8N_URL: http://n8n:5678
      ENVIRONMENT: production
    ports:
      - "127.0.0.1:8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped
    networks:
      - vai-network

  # ============== Admin UI ==============
  admin-ui:
    build:
      context: ./src/admin-ui
      dockerfile: Dockerfile
      args:
        NEXT_PUBLIC_API_URL: ${API_URL:-http://localhost:8000}
        NEXT_PUBLIC_LIVEKIT_URL: ${LIVEKIT_URL}
    container_name: vai-admin-ui
    environment:
      <<: *common-env
      NEXT_PUBLIC_API_URL: ${API_URL}
      NEXT_PUBLIC_LIVEKIT_URL: ${LIVEKIT_URL}
    ports:
      - "127.0.0.1:3000:3000"
    depends_on:
      - backend
    restart: unless-stopped
    networks:
      - vai-network

  # ============== LiveKit ==============
  livekit:
    image: livekit/livekit-server:latest
    container_name: vai-livekit
    command: --config /etc/livekit.yaml
    environment:
      <<: *common-env
    volumes:
      - ./configs/livekit/livekit.yaml:/etc/livekit.yaml:ro
    ports:
      - "7880:7880"
      - "7881:7881"
      - "7882:7882/udp"
    depends_on:
      redis:
        condition: service_healthy
    restart: unless-stopped
    networks:
      - vai-network

  livekit-sip:
    image: livekit/sip:latest
    container_name: vai-livekit-sip
    network_mode: host
    environment:
      <<: *common-env
      LIVEKIT_URL: ws://localhost:7880
      LIVEKIT_API_KEY: ${LIVEKIT_API_KEY}
      LIVEKIT_API_SECRET: ${LIVEKIT_API_SECRET}
    volumes:
      - ./configs/livekit/sip-trunk.yaml:/etc/sip-trunk.yaml:ro
      - ./configs/livekit/sip-dispatch.yaml:/etc/sip-dispatch.yaml:ro
    command: --config /etc/sip-trunk.yaml --dispatch-rules /etc/sip-dispatch.yaml
    depends_on:
      - livekit
    restart: unless-stopped

  # ============== Voice Agent ==============
  voice-agent:
    build:
      context: ./src/agent
      dockerfile: Dockerfile
    container_name: vai-voice-agent
    environment:
      <<: *common-env
      LIVEKIT_URL: ws://livekit:7880
      LIVEKIT_API_KEY: ${LIVEKIT_API_KEY}
      LIVEKIT_API_SECRET: ${LIVEKIT_API_SECRET}
      DEEPGRAM_API_KEY: ${DEEPGRAM_API_KEY}
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      CARTESIA_API_KEY: ${CARTESIA_API_KEY}
      MCP_SERVER_URL: http://n8n:5678/webhook/${N8N_MCP_WEBHOOK_ID}
      BACKEND_URL: http://backend:8000
    depends_on:
      - livekit
      - n8n
      - backend
    deploy:
      replicas: ${AGENT_REPLICAS:-2}
    restart: unless-stopped
    networks:
      - vai-network

  # ============== LightRAG ==============
  lightrag:
    build:
      context: ./src/lightrag
      dockerfile: Dockerfile
    container_name: vai-lightrag
    environment:
      <<: *common-env
      LIGHTRAG_API_KEY: ${LIGHTRAG_API_KEY}
      LLM_BINDING: openai
      LLM_MODEL: ${LIGHTRAG_LLM_MODEL:-gpt-4o-mini}
      LLM_API_KEY: ${OPENAI_API_KEY}
      EMBEDDING_BINDING: ${EMBEDDING_BINDING:-openai}
      EMBEDDING_MODEL: ${EMBEDDING_MODEL:-text-embedding-3-small}
      EMBEDDING_API_KEY: ${OPENAI_API_KEY}
    volumes:
      - lightrag_data:/app/data
    ports:
      - "127.0.0.1:9621:9621"
    restart: unless-stopped
    networks:
      - vai-network

  # ============== n8n ==============
  n8n:
    image: n8nio/n8n:latest
    container_name: vai-n8n
    environment:
      <<: *common-env
      N8N_BASIC_AUTH_ACTIVE: "true"
      N8N_BASIC_AUTH_USER: ${N8N_USER:-admin}
      N8N_BASIC_AUTH_PASSWORD: ${N8N_PASSWORD}
      N8N_HOST: ${N8N_HOST:-localhost}
      N8N_PORT: 5678
      N8N_PROTOCOL: https
      WEBHOOK_URL: ${N8N_WEBHOOK_URL}
      GENERIC_TIMEZONE: ${TZ:-UTC}
      # Environment for workflows
      LIGHTRAG_URL: http://lightrag:9621
      LIGHTRAG_API_KEY: ${LIGHTRAG_API_KEY}
    volumes:
      - n8n_data:/home/node/.n8n
      - ./src/n8n-workflows:/home/node/workflows:ro
    ports:
      - "127.0.0.1:5678:5678"
    restart: unless-stopped
    networks:
      - vai-network

  # ============== Nginx Reverse Proxy ==============
  nginx:
    image: nginx:alpine
    container_name: vai-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./configs/nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./configs/nginx/ssl:/etc/nginx/ssl:ro
      - ./configs/nginx/conf.d:/etc/nginx/conf.d:ro
    depends_on:
      - backend
      - admin-ui
      - n8n
    restart: unless-stopped
    networks:
      - vai-network

  # ============== Monitoring ==============
  prometheus:
    image: prom/prometheus:latest
    container_name: vai-prometheus
    volumes:
      - ./configs/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus_data:/prometheus
    ports:
      - "127.0.0.1:9090:9090"
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
    restart: unless-stopped
    networks:
      - vai-network

  grafana:
    image: grafana/grafana:latest
    container_name: vai-grafana
    environment:
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_PASSWORD}
      GF_USERS_ALLOW_SIGN_UP: "false"
    volumes:
      - grafana_data:/var/lib/grafana
      - ./configs/grafana/dashboards:/etc/grafana/provisioning/dashboards:ro
    ports:
      - "127.0.0.1:3001:3000"
    depends_on:
      - prometheus
    restart: unless-stopped
    networks:
      - vai-network

volumes:
  postgres_data:
  redis_data:
  lightrag_data:
  n8n_data:
  prometheus_data:
  grafana_data:

networks:
  vai-network:
    driver: bridge
```

---

## Step 2: Nginx Configuration

Create `configs/nginx/nginx.conf`:

```nginx
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 4096;
    use epoll;
    multi_accept on;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;

    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml application/json application/javascript 
               application/xml application/xml+rss text/javascript;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=auth:10m rate=5r/m;

    # Upstream servers
    upstream backend {
        server backend:8000;
        keepalive 32;
    }

    upstream admin-ui {
        server admin-ui:3000;
        keepalive 32;
    }

    upstream livekit {
        server livekit:7880;
        keepalive 32;
    }

    upstream n8n {
        server n8n:5678;
        keepalive 32;
    }

    # HTTP to HTTPS redirect
    server {
        listen 80;
        server_name _;
        return 301 https://$host$request_uri;
    }

    # Main HTTPS server
    server {
        listen 443 ssl http2;
        server_name your-domain.com;

        ssl_certificate /etc/nginx/ssl/fullchain.pem;
        ssl_certificate_key /etc/nginx/ssl/privkey.pem;
        ssl_session_timeout 1d;
        ssl_session_cache shared:SSL:50m;
        ssl_session_tickets off;

        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
        ssl_prefer_server_ciphers off;

        # Security headers
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header Referrer-Policy "strict-origin-when-cross-origin" always;

        # Admin UI
        location / {
            proxy_pass http://admin-ui;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_cache_bypass $http_upgrade;
        }

        # Backend API
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            
            proxy_pass http://backend/;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # CORS headers
            add_header Access-Control-Allow-Origin $http_origin always;
            add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
            add_header Access-Control-Allow-Headers "Authorization, Content-Type" always;
            
            if ($request_method = 'OPTIONS') {
                return 204;
            }
        }

        # Auth endpoints with stricter rate limiting
        location /api/auth/ {
            limit_req zone=auth burst=5 nodelay;
            
            proxy_pass http://backend/auth/;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # LiveKit WebSocket
        location /livekit/ {
            proxy_pass http://livekit/;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_read_timeout 86400;
        }

        # n8n webhooks
        location /webhook/ {
            proxy_pass http://n8n/webhook/;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Health check
        location /health {
            access_log off;
            return 200 "OK";
            add_header Content-Type text/plain;
        }
    }
}
```

---

## Step 3: Backend Dockerfile

Create `src/backend/Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run with gunicorn
CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000"]
```

---

## Step 4: Voice Agent Dockerfile

Create `src/agent/Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libsndfile1 \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 agentuser && chown -R agentuser:agentuser /app
USER agentuser

# Run agent
CMD ["python", "main.py", "start"]
```

---

## Step 5: Production Environment File

Create `configs/env.production`:

```bash
# ===========================================
# VOICE AI PLATFORM - PRODUCTION
# ===========================================

# ----- General -----
ENVIRONMENT=production
TZ=UTC
LOG_LEVEL=INFO

# ----- Domain -----
DOMAIN=voice-ai.yourdomain.com
API_URL=https://voice-ai.yourdomain.com/api
FRONTEND_URL=https://voice-ai.yourdomain.com

# ----- Database -----
POSTGRES_USER=voice_ai
POSTGRES_PASSWORD=<GENERATE_SECURE_PASSWORD>
POSTGRES_DB=voice_ai_platform

# ----- Redis -----
REDIS_PASSWORD=<GENERATE_SECURE_PASSWORD>

# ----- JWT -----
JWT_SECRET_KEY=<GENERATE_64_CHAR_SECRET>
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# ----- Internal API -----
INTERNAL_API_KEY=<GENERATE_32_CHAR_KEY>

# ----- LiveKit -----
LIVEKIT_URL=wss://voice-ai.yourdomain.com/livekit
LIVEKIT_API_KEY=<YOUR_API_KEY>
LIVEKIT_API_SECRET=<YOUR_API_SECRET>

# ----- AI Services -----
OPENAI_API_KEY=sk-...
DEEPGRAM_API_KEY=...
CARTESIA_API_KEY=...

# ----- LightRAG -----
LIGHTRAG_API_KEY=<GENERATE_40_CHAR_KEY>
LIGHTRAG_LLM_MODEL=gpt-4o-mini

# ----- n8n -----
N8N_USER=admin
N8N_PASSWORD=<GENERATE_SECURE_PASSWORD>
N8N_HOST=voice-ai.yourdomain.com
N8N_WEBHOOK_URL=https://voice-ai.yourdomain.com/webhook/
N8N_MCP_WEBHOOK_ID=<YOUR_WEBHOOK_ID>

# ----- Telephony (Telnyx) -----
TELNYX_API_KEY=KEY...
TELNYX_SIP_USERNAME=<YOUR_SIP_USERNAME>
TELNYX_SIP_PASSWORD=<YOUR_SIP_PASSWORD>

# ----- Monitoring -----
GRAFANA_PASSWORD=<GENERATE_SECURE_PASSWORD>
SENTRY_DSN=https://...@sentry.io/...

# ----- Scaling -----
AGENT_REPLICAS=2
```

---

## Step 6: Deployment Script

Create `scripts/deploy.sh`:

```bash
#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Voice AI Platform - Production Deployment${NC}"
echo -e "${GREEN}========================================${NC}"

# Check requirements
echo -e "\n${YELLOW}Checking requirements...${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker is not installed${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}Docker Compose is not installed${NC}"
    exit 1
fi

# Check environment file
if [ ! -f ".env" ]; then
    echo -e "${RED}.env file not found. Copy from configs/env.production${NC}"
    exit 1
fi

# Load environment
source .env

# Verify critical variables
REQUIRED_VARS=(
    "POSTGRES_PASSWORD"
    "REDIS_PASSWORD"
    "JWT_SECRET_KEY"
    "LIVEKIT_API_KEY"
    "LIVEKIT_API_SECRET"
    "OPENAI_API_KEY"
    "DEEPGRAM_API_KEY"
    "CARTESIA_API_KEY"
)

for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        echo -e "${RED}Missing required variable: $var${NC}"
        exit 1
    fi
done

echo -e "${GREEN}✓ All required variables set${NC}"

# Pull latest images
echo -e "\n${YELLOW}Pulling latest images...${NC}"
docker compose -f docker-compose.prod.yml pull

# Build custom images
echo -e "\n${YELLOW}Building custom images...${NC}"
docker compose -f docker-compose.prod.yml build --no-cache

# Run database migrations
echo -e "\n${YELLOW}Running database migrations...${NC}"
docker compose -f docker-compose.prod.yml run --rm backend alembic upgrade head

# Start services
echo -e "\n${YELLOW}Starting services...${NC}"
docker compose -f docker-compose.prod.yml up -d

# Wait for services to be healthy
echo -e "\n${YELLOW}Waiting for services to be healthy...${NC}"
sleep 30

# Check service health
echo -e "\n${YELLOW}Checking service health...${NC}"
SERVICES=("vai-postgres" "vai-redis" "vai-backend" "vai-livekit" "vai-lightrag" "vai-n8n")

for service in "${SERVICES[@]}"; do
    STATUS=$(docker inspect --format='{{.State.Health.Status}}' $service 2>/dev/null || echo "unknown")
    if [ "$STATUS" == "healthy" ] || [ "$STATUS" == "unknown" ]; then
        echo -e "${GREEN}✓ $service is running${NC}"
    else
        echo -e "${RED}✗ $service is not healthy (status: $STATUS)${NC}"
    fi
done

# Print access information
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "\nAccess URLs:"
echo -e "  Admin UI:  https://${DOMAIN}"
echo -e "  API:       https://${DOMAIN}/api"
echo -e "  n8n:       https://${DOMAIN}:5678"
echo -e "  Grafana:   https://${DOMAIN}:3001"
echo -e "\nNext steps:"
echo -e "  1. Create superadmin: docker compose exec backend python scripts/create_superadmin.py"
echo -e "  2. Import n8n workflows from src/n8n-workflows/"
echo -e "  3. Configure SSL certificates if not using Cloudflare"
echo -e "  4. Set up monitoring alerts in Grafana"
```

---

## Step 7: Backup Script

Create `scripts/backup.sh`:

```bash
#!/bin/bash
set -e

BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

echo "Starting backup: $DATE"

# Create backup directory
mkdir -p $BACKUP_DIR/$DATE

# Backup PostgreSQL
echo "Backing up PostgreSQL..."
docker exec vai-postgres pg_dump -U $POSTGRES_USER $POSTGRES_DB | gzip > $BACKUP_DIR/$DATE/postgres.sql.gz

# Backup Redis
echo "Backing up Redis..."
docker exec vai-redis redis-cli -a $REDIS_PASSWORD BGSAVE
sleep 5
docker cp vai-redis:/data/dump.rdb $BACKUP_DIR/$DATE/redis.rdb

# Backup LightRAG data
echo "Backing up LightRAG..."
docker cp vai-lightrag:/app/data $BACKUP_DIR/$DATE/lightrag_data

# Backup n8n data
echo "Backing up n8n..."
docker cp vai-n8n:/home/node/.n8n $BACKUP_DIR/$DATE/n8n_data

# Compress backup
echo "Compressing backup..."
tar -czf $BACKUP_DIR/backup_$DATE.tar.gz -C $BACKUP_DIR $DATE
rm -rf $BACKUP_DIR/$DATE

# Upload to S3 (optional)
# aws s3 cp $BACKUP_DIR/backup_$DATE.tar.gz s3://your-bucket/backups/

# Cleanup old backups
echo "Cleaning up old backups..."
find $BACKUP_DIR -name "backup_*.tar.gz" -mtime +$RETENTION_DAYS -delete

echo "Backup complete: $BACKUP_DIR/backup_$DATE.tar.gz"
```

---

## Step 8: SSL Certificate Setup

### Option A: Let's Encrypt with Certbot

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d voice-ai.yourdomain.com

# Auto-renewal is set up automatically
```

### Option B: Cloudflare (Recommended)

1. Add your domain to Cloudflare
2. Enable Full (strict) SSL mode
3. Create Origin Certificate in Cloudflare dashboard
4. Copy certificates to `configs/nginx/ssl/`

---

## Step 9: Monitoring Setup

Create `configs/prometheus/prometheus.yml`:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'backend'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: /metrics

  - job_name: 'livekit'
    static_configs:
      - targets: ['livekit:7880']
    metrics_path: /metrics

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']

  - job_name: 'nginx'
    static_configs:
      - targets: ['nginx-exporter:9113']
```

---

## Deployment Checklist

### Pre-Deployment
- [ ] All API keys obtained and configured
- [ ] Domain DNS configured
- [ ] SSL certificates ready
- [ ] Firewall rules configured
- [ ] Environment file complete

### Deployment
- [ ] Docker images built
- [ ] Database migrations run
- [ ] Services started
- [ ] Health checks passing
- [ ] SSL working

### Post-Deployment
- [ ] Superadmin created
- [ ] n8n workflows imported and activated
- [ ] Test inbound call
- [ ] Test outbound call
- [ ] Monitoring dashboards configured
- [ ] Backup schedule configured
- [ ] Alert rules set up

---

## Server Requirements

### Minimum (Development)
- 4 vCPU
- 8GB RAM
- 50GB SSD
- Ubuntu 22.04+

### Recommended (Production)
- 8+ vCPU
- 16GB+ RAM
- 100GB+ SSD
- Ubuntu 22.04+
- Dedicated IP address
- Open ports: 80, 443, 5060, 7880-7882

### High Availability
- Load balancer (AWS ALB / Cloudflare)
- Multiple agent workers
- PostgreSQL with replication
- Redis Sentinel or Cluster
- S3 for document storage

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| Services won't start | Missing env vars | Check .env file |
| Database connection | Wrong credentials | Verify POSTGRES_* vars |
| SIP calls failing | Firewall | Open port 5060 + RTP range |
| Agent not connecting | LiveKit URL | Check LIVEKIT_URL format |
| Slow responses | LLM latency | Use faster model or OpenRouter |

---

## Support Contacts

- LiveKit: https://livekit.io/docs
- Telnyx: https://developers.telnyx.com
- Deepgram: https://developers.deepgram.com
- OpenAI: https://platform.openai.com/docs

---

## Congratulations! 🎉

You have completed the Voice AI Platform setup. The system is now ready for:
- Multi-tenant voice agent deployment
- Healthcare appointment booking
- Hospitality guest services
- Inbound and outbound phone calls
- Real-time credit tracking and billing

For additional features or customizations, refer to the documentation in the `docs/` folder.
