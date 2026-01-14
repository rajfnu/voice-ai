# Voice AI Platform - Quickstart Guide

## Goal
Get the Voice AI Platform running locally on your Mac in 30 minutes.

---

## Prerequisites Checklist

Before starting, ensure you have:

- [ ] **macOS** (Intel or Apple Silicon)
- [ ] **Docker Desktop** installed and running
- [ ] **Homebrew** installed
- [ ] **API Keys** (get free tiers):
  - [ ] OpenAI API key (GPT-4o)
  - [ ] Deepgram API key (STT)
  - [ ] Cartesia API key (TTS)

---

## Step 1: Install Tools (5 min)

```bash
# Update Homebrew
brew update

# Install required tools
brew install python@3.11 node livekit

# Install Ollama (for local embeddings)
brew install ollama

# Verify installations
python3.11 --version   # Should show 3.11.x
node --version         # Should show 18+ or 20+
lk --version           # LiveKit CLI
ollama --version       # Ollama
```

---

## Step 2: Start Ollama & Pull Models (5 min)

```bash
# Start Ollama service
ollama serve &

# Pull embedding model (for LightRAG)
ollama pull bge-m3:latest

# Pull reranker model (optional but recommended)
ollama pull bge-reranker-v2-m3
```

---

## Step 3: Clone/Create Project (2 min)

```bash
# Create project directory
mkdir -p ~/voice-ai-platform
cd ~/voice-ai-platform

# Create directory structure
mkdir -p src/{backend,agent,admin-ui,lightrag,n8n-workflows}
mkdir -p configs/{livekit,nginx}
mkdir -p docs templates scripts
```

---

## Step 4: Create Environment File (3 min)

```bash
# Create .env file
cat > .env << 'EOF'
# ============================================
# Voice AI Platform - Local Development
# ============================================

# Database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=localdev123
POSTGRES_DB=voice_ai_platform
DATABASE_URL=postgresql+asyncpg://postgres:localdev123@localhost:5432/voice_ai_platform

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
JWT_SECRET_KEY=local-dev-secret-key-change-in-production-12345678901234567890
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Internal API
INTERNAL_API_KEY=local-internal-api-key-32chars

# LiveKit (dev mode)
LIVEKIT_URL=ws://localhost:7880
LIVEKIT_API_KEY=devkey
LIVEKIT_API_SECRET=secret0123456789012345678901234567890

# AI Services (add your keys)
OPENAI_API_KEY=sk-your-openai-key-here
DEEPGRAM_API_KEY=your-deepgram-key-here
CARTESIA_API_KEY=your-cartesia-key-here

# LightRAG
LIGHTRAG_URL=http://localhost:9621
LIGHTRAG_API_KEY=dev-lightrag-api-key-12345678901234567890

# n8n
N8N_USER=admin
N8N_PASSWORD=admin123
N8N_MCP_WEBHOOK_ID=your-webhook-id

# Optional: OpenRouter (alternative LLM)
OPENROUTER_API_KEY=

# Environment
ENVIRONMENT=development
LOG_LEVEL=DEBUG
EOF

# Edit .env with your actual API keys
nano .env
```

---

## Step 5: Start Infrastructure (5 min)

Create and run docker-compose:

```bash
# Create docker-compose file
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  postgres:
    image: postgres:16-alpine
    container_name: vai-postgres
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: localdev123
      POSTGRES_DB: voice_ai_platform
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    container_name: vai-redis
    ports:
      - "6379:6379"

  livekit:
    image: livekit/livekit-server:latest
    container_name: vai-livekit
    command: --dev --bind 0.0.0.0
    environment:
      - LIVEKIT_KEYS=devkey:secret0123456789012345678901234567890
    ports:
      - "7880:7880"
      - "7881:7881"
      - "7882:7882/udp"

  n8n:
    image: n8nio/n8n:latest
    container_name: vai-n8n
    environment:
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=admin
      - N8N_BASIC_AUTH_PASSWORD=admin123
      - GENERIC_TIMEZONE=Australia/Sydney
    ports:
      - "5678:5678"
    volumes:
      - n8n_data:/home/node/.n8n
    extra_hosts:
      - "host.docker.internal:host-gateway"

volumes:
  postgres_data:
  n8n_data:
EOF

# Start services
docker compose up -d

# Verify all containers are running
docker ps
```

You should see 4 containers running: postgres, redis, livekit, n8n

---

## Step 6: Set Up LightRAG (5 min)

```bash
# Clone LightRAG
cd src
git clone https://github.com/HKUDS/LightRAG.git lightrag
cd lightrag

# Create custom docker-compose for LightRAG
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  lightrag:
    build: .
    container_name: vai-lightrag
    environment:
      - WEBUI_TITLE=Voice AI KB
      - AUTH_ACCOUNTS=admin:admin123
      - LIGHTRAG_API_KEY=dev-lightrag-api-key-12345678901234567890
      - LLM_BINDING=openai
      - LLM_MODEL=gpt-4o-mini
      - LLM_API_KEY=${OPENAI_API_KEY}
      - EMBEDDING_BINDING=ollama
      - EMBEDDING_MODEL=bge-m3:latest
      - EMBEDDING_BASE_URL=http://host.docker.internal:11434
    ports:
      - "9621:9621"
    volumes:
      - lightrag_data:/app/data
    extra_hosts:
      - "host.docker.internal:host-gateway"

volumes:
  lightrag_data:
EOF

# Start LightRAG (requires .env with OPENAI_API_KEY)
export $(cat ../../.env | grep -v '^#' | xargs)
docker compose up -d

# Verify LightRAG is running
curl http://localhost:9621/health
```

---

## Step 7: Create Voice Agent (5 min)

```bash
cd ~/voice-ai-platform/src/agent

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Create requirements.txt
cat > requirements.txt << 'EOF'
livekit-agents>=0.8.0
livekit-plugins-deepgram>=0.6.0
livekit-plugins-openai>=0.8.0
livekit-plugins-cartesia>=0.4.0
livekit-plugins-silero>=0.6.0
httpx>=0.25.0
python-dotenv>=1.0.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
EOF

# Install dependencies
pip install -r requirements.txt

# Create config.py
cat > config.py << 'EOF'
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    LIVEKIT_URL: str = "ws://localhost:7880"
    LIVEKIT_API_KEY: str = "devkey"
    LIVEKIT_API_SECRET: str = "secret0123456789012345678901234567890"
    OPENAI_API_KEY: str
    DEEPGRAM_API_KEY: str
    CARTESIA_API_KEY: str
    MCP_SERVER_URL: str = "http://localhost:5678/webhook/mcp"
    BACKEND_URL: str = "http://localhost:8000"
    
    class Config:
        env_file = "../../.env"

settings = Settings()
EOF

# Create main agent file
cat > main.py << 'EOF'
import asyncio
import logging
from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions
from livekit.agents.voice import VoiceAgent
from livekit.plugins import deepgram, openai, cartesia, silero

from config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("voice-agent")

SYSTEM_PROMPT = """You are Alex, a friendly virtual assistant.

Your role:
- Answer questions about our services
- Help schedule appointments
- Provide information from the knowledge base

Guidelines:
- Keep responses brief (2-3 sentences for voice)
- Be warm and conversational
- Say "Let me check that for you" before looking things up
- If unsure, offer to connect with a human

You have access to tools:
- query_kb: Search the knowledge base for information
"""

FIRST_MESSAGE = "Hi! I'm Alex. How can I help you today?"

async def entrypoint(ctx: agents.JobContext):
    await ctx.connect()
    
    session = AgentSession(
        vad=silero.VAD.load(),
        stt=deepgram.STT(api_key=settings.DEEPGRAM_API_KEY),
        llm=openai.LLM(
            api_key=settings.OPENAI_API_KEY,
            model="gpt-4o",
        ),
        tts=cartesia.TTS(
            api_key=settings.CARTESIA_API_KEY,
            voice="a0e99841-438c-4a64-b679-ae501e7d6091",  # Friendly female
        ),
    )
    
    agent = VoiceAgent(
        instructions=SYSTEM_PROMPT,
        session=session,
    )
    
    agent.start(ctx.room)
    
    # Say greeting
    await agent.say(FIRST_MESSAGE)
    
    logger.info(f"Agent started in room {ctx.room.name}")

if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))
EOF
```

---

## Step 8: Configure n8n MCP Server (5 min)

1. Open n8n: http://localhost:5678
2. Login: admin / admin123
3. Create new workflow called "Voice AI MCP"
4. Add **MCP Server Trigger** node
5. Add **HTTP Request** node for LightRAG query:
   - Method: POST
   - URL: `http://host.docker.internal:9621/query`
   - Headers: 
     - Accept: application/json
     - X-API-Key: dev-lightrag-api-key-12345678901234567890
   - Body (JSON):
     ```json
     {
       "query": "{{ $json.query }}",
       "mode": "mix"
     }
     ```
6. Connect nodes: MCP Trigger → HTTP Request
7. In MCP Trigger, add tool definition:
   ```json
   {
     "name": "query_kb",
     "description": "Search knowledge base",
     "inputSchema": {
       "type": "object",
       "properties": {
         "query": {"type": "string"}
       },
       "required": ["query"]
     }
   }
   ```
8. **Activate** the workflow
9. Copy the Production URL (you'll need this)

---

## Step 9: Test the System

### Test 1: Verify Services

```bash
# Check all services are up
docker ps

# Test LightRAG
curl http://localhost:9621/health

# Test LiveKit
curl http://localhost:7880

# Test n8n
curl http://localhost:5678/healthz
```

### Test 2: Add Content to Knowledge Base

Open LightRAG UI: http://localhost:9621
1. Login: admin / admin123
2. Go to Documents tab
3. Add some test content:
   ```
   Our business hours are Monday through Friday, 9 AM to 5 PM.
   We are closed on weekends and major holidays.
   For appointments, please call our main line or use the online booking system.
   ```
4. Wait for processing

### Test 3: Test Voice Agent

```bash
# In terminal 1: Start the agent
cd ~/voice-ai-platform/src/agent
source venv/bin/activate
python main.py dev

# In terminal 2: Create a room token
lk token create \
  --api-key devkey \
  --api-secret secret0123456789012345678901234567890 \
  --join --room test-room \
  --identity test-user \
  --valid-for 1h
```

Copy the token, then:
1. Go to https://meet.livekit.io
2. Enter LiveKit URL: `ws://localhost:7880`
3. Paste the token
4. Click Join
5. Speak: "What are your business hours?"

---

## Quick Reference

### URLs

| Service | URL | Credentials |
|---------|-----|-------------|
| n8n | http://localhost:5678 | admin / admin123 |
| LightRAG | http://localhost:9621 | admin / admin123 |
| LiveKit | ws://localhost:7880 | devkey / secret... |
| PostgreSQL | localhost:5432 | postgres / localdev123 |
| Redis | localhost:6379 | - |

### Commands

```bash
# Start all services
docker compose up -d

# Stop all services
docker compose down

# View logs
docker compose logs -f

# Start voice agent
cd src/agent && source venv/bin/activate && python main.py dev

# Generate room token
lk token create --api-key devkey --api-secret secret0123456789012345678901234567890 \
  --join --room my-room --identity user1 --valid-for 1h
```

### Troubleshooting

| Issue | Solution |
|-------|----------|
| Docker containers not starting | Run `docker compose down -v` then `docker compose up -d` |
| LightRAG can't reach Ollama | Ensure Ollama is running: `ollama serve` |
| Agent won't connect | Check LIVEKIT_URL is `ws://localhost:7880` not `wss://` |
| n8n webhook not working | Ensure workflow is **Active** (toggle in top right) |
| Voice not working in browser | Allow microphone permissions |

---

## Next Steps

1. ✅ **Local system working** - You're here!
2. 📖 **Read the skill files** - Follow `.claude/skills/01-DATABASE-SCHEMA.md` onwards
3. 🔧 **Build the backend** - FastAPI with multi-tenant support
4. 📞 **Add phone support** - Set up Telnyx SIP trunk
5. 🎨 **Build admin UI** - Next.js dashboard
6. 🚀 **Deploy to production** - Follow `.claude/skills/10-DEPLOYMENT.md`

---

## Getting Help

If you get stuck:

1. Check Docker logs: `docker compose logs [service-name]`
2. Check agent logs: Look at terminal output
3. Verify API keys: Ensure .env has valid keys
4. Test endpoints: Use curl to verify services respond

For Claude Code assistance:
```
@workspace I'm following the quickstart guide and [describe your issue]. 
Please help me troubleshoot.
```
