# Skill 00: Prerequisites Setup

## Objective
Set up the Mac development environment with all required tools, dependencies, and API keys.

---

## Step 1: Install Core Tools

### 1.1 Homebrew (if not installed)
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### 1.2 Docker Desktop
```bash
# Download and install Docker Desktop for Mac
# https://www.docker.com/products/docker-desktop/

# Verify installation
docker --version
docker compose version
```

### 1.3 Development Tools
```bash
brew update
brew install node@20
brew install python@3.11
brew install git
brew install jq
brew install httpie
brew install livekit
brew install ollama
```

### 1.4 Python Environment Setup
```bash
# Create project directory
mkdir -p ~/voice-ai-platform
cd ~/voice-ai-platform

# Create Python virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install base dependencies
pip install \
    fastapi[all] \
    uvicorn \
    sqlalchemy \
    alembic \
    asyncpg \
    pydantic \
    python-jose[cryptography] \
    passlib[bcrypt] \
    httpx \
    redis \
    python-multipart
```

### 1.5 Node.js Setup
```bash
# Verify Node version (should be 20+)
node --version

# Install pnpm (faster than npm)
npm install -g pnpm
```

---

## Step 2: Required API Keys

Create accounts and get API keys from these services:

### 2.1 LLM Providers (choose at least one)

| Provider | Sign Up | Key Location |
|----------|---------|--------------|
| OpenAI | https://platform.openai.com | API Keys section |
| OpenRouter | https://openrouter.ai | Keys in dashboard |
| Anthropic | https://console.anthropic.com | API Keys |

### 2.2 Speech Services

| Service | Sign Up | Purpose |
|---------|---------|---------|
| Deepgram | https://console.deepgram.com | STT (Speech-to-Text) |
| Cartesia | https://play.cartesia.ai | TTS (Text-to-Speech) |

### 2.3 Telephony Provider (for phone calls)

| Provider | Sign Up | Purpose |
|----------|---------|---------|
| Telnyx | https://portal.telnyx.com | SIP Trunking, Phone Numbers |
| Twilio | https://console.twilio.com | Alternative SIP provider |

### 2.4 LiveKit (optional - for cloud deployment)

| Service | Sign Up |
|---------|---------|
| LiveKit Cloud | https://cloud.livekit.io |

---

## Step 3: Create Environment File

```bash
cd ~/voice-ai-platform
mkdir -p configs

cat > configs/env.example << 'EOF'
# ===========================================
# VOICE AI PLATFORM - ENVIRONMENT VARIABLES
# ===========================================

# ----- Database -----
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/voice_ai_platform
REDIS_URL=redis://localhost:6379/0

# ----- JWT Auth -----
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# ----- Platform Settings -----
PLATFORM_NAME="Voice AI Platform"
ADMIN_EMAIL=admin@yourdomain.com
ENVIRONMENT=development

# ----- LLM Provider -----
# Option 1: OpenAI
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o

# Option 2: OpenRouter
OPENROUTER_API_KEY=sk-or-...
OPENROUTER_MODEL=openai/gpt-4o

# Option 3: Anthropic
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-sonnet-4-20250514

# ----- Speech Services -----
DEEPGRAM_API_KEY=...
CARTESIA_API_KEY=...
CARTESIA_VOICE_ID=a0e99841-438c-4a64-b679-ae501e7d6091

# ----- LiveKit -----
LIVEKIT_URL=ws://localhost:7880
LIVEKIT_API_KEY=devkey
LIVEKIT_API_SECRET=secret

# ----- LightRAG -----
LIGHTRAG_URL=http://localhost:9621
LIGHTRAG_API_KEY=your-lightrag-api-key

# ----- n8n -----
N8N_URL=http://localhost:5678
N8N_MCP_WEBHOOK_URL=http://localhost:5678/webhook/mcp

# ----- Telephony (Telnyx) -----
TELNYX_API_KEY=KEY...
TELNYX_SIP_USERNAME=
TELNYX_SIP_PASSWORD=
TELNYX_PHONE_NUMBER=+1234567890

# ----- Ollama (Local) -----
OLLAMA_BASE_URL=http://localhost:11434

# ----- Credit System -----
DEFAULT_TENANT_CREDITS=1000
CREDIT_RATE_INBOUND_PER_MIN=1.0
CREDIT_RATE_OUTBOUND_PER_MIN=2.0
CREDIT_RATE_STT_PER_MIN=0.5
CREDIT_RATE_LLM_PER_1K_TOKENS=0.1
CREDIT_RATE_TTS_PER_1K_CHARS=0.05
CREDIT_RATE_RAG_QUERY=0.02
EOF

# Create actual .env from example
cp configs/env.example .env
echo "⚠️  Edit .env with your actual API keys!"
```

---

## Step 4: Project Directory Structure

```bash
cd ~/voice-ai-platform

# Create full directory structure
mkdir -p src/{backend,agent,admin-ui,n8n-workflows,lightrag}
mkdir -p src/backend/{app,tests,scripts,alembic}
mkdir -p src/backend/app/{api,core,db,models,schemas,services}
mkdir -p src/agent/{agents,plugins,prompts}
mkdir -p src/admin-ui/{app,components,lib}
mkdir -p configs
mkdir -p docs
mkdir -p templates/{healthcare,hospitality,generic}
mkdir -p skills

# Create placeholder files
touch src/backend/app/__init__.py
touch src/backend/app/api/__init__.py
touch src/backend/app/core/__init__.py
touch src/backend/app/db/__init__.py
touch src/backend/app/models/__init__.py
touch src/backend/app/schemas/__init__.py
touch src/backend/app/services/__init__.py
```

---

## Step 5: Start Local Services

### 5.1 Start Ollama (for local embeddings)
```bash
# Start Ollama service
ollama serve &

# Pull required models
ollama pull bge-m3:latest
ollama pull bge-reranker-v2-m3
ollama pull llama3.2:latest  # Optional local LLM
```

### 5.2 Start PostgreSQL and Redis (Docker)
```bash
cd ~/voice-ai-platform

cat > docker-compose.dev.yml << 'EOF'
version: '3.8'
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: voice_ai_platform
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
  redis_data:
EOF

# Start services
docker compose -f docker-compose.dev.yml up -d

# Verify
docker compose -f docker-compose.dev.yml ps
```

---

## Step 6: Verify Setup

Run this verification script:

```bash
cat > verify_setup.sh << 'EOF'
#!/bin/bash

echo "🔍 Verifying Voice AI Platform Setup..."
echo ""

# Check Docker
if command -v docker &> /dev/null; then
    echo "✅ Docker: $(docker --version)"
else
    echo "❌ Docker not found"
fi

# Check Python
if command -v python3.11 &> /dev/null; then
    echo "✅ Python: $(python3.11 --version)"
else
    echo "❌ Python 3.11 not found"
fi

# Check Node
if command -v node &> /dev/null; then
    echo "✅ Node.js: $(node --version)"
else
    echo "❌ Node.js not found"
fi

# Check LiveKit CLI
if command -v livekit-cli &> /dev/null || command -v lk &> /dev/null; then
    echo "✅ LiveKit CLI installed"
else
    echo "⚠️  LiveKit CLI not found (optional)"
fi

# Check Ollama
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "✅ Ollama running"
else
    echo "⚠️  Ollama not running (run: ollama serve)"
fi

# Check PostgreSQL
if docker compose -f docker-compose.dev.yml ps postgres 2>/dev/null | grep -q "running"; then
    echo "✅ PostgreSQL running"
else
    echo "❌ PostgreSQL not running"
fi

# Check Redis
if docker compose -f docker-compose.dev.yml ps redis 2>/dev/null | grep -q "running"; then
    echo "✅ Redis running"
else
    echo "❌ Redis not running"
fi

# Check .env file
if [ -f ".env" ]; then
    echo "✅ .env file exists"
else
    echo "⚠️  .env file not found (copy from configs/env.example)"
fi

echo ""
echo "Setup verification complete!"
EOF

chmod +x verify_setup.sh
./verify_setup.sh
```

---

## Step 7: Install LiveKit Agent Dependencies

```bash
cd ~/voice-ai-platform
source venv/bin/activate

# Install LiveKit Agent SDK and plugins
pip install \
    livekit \
    livekit-agents \
    livekit-plugins-deepgram \
    livekit-plugins-openai \
    livekit-plugins-cartesia \
    livekit-plugins-silero
```

---

## Checklist Before Moving to Next Skill

- [ ] Docker Desktop running
- [ ] Python 3.11 virtual environment activated
- [ ] Node.js 20+ installed
- [ ] Ollama running with bge-m3 model
- [ ] PostgreSQL container running
- [ ] Redis container running
- [ ] .env file created with your API keys
- [ ] Project directory structure created

---

## Next Step

Proceed to: `.claude/skills/01-DATABASE-SCHEMA.md`
