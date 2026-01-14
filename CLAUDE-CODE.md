# Voice AI Platform - Claude Code Build Guide

## Overview

This project provides a complete set of **skill files** for building a multi-tenant Voice AI Agent platform using Claude Code in VS Code. Each skill file is a self-contained guide that Claude Code can follow to implement that component.

---

## Architecture Summary

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                          VOICE AI PLATFORM ARCHITECTURE                              │
│                                                                                      │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │                              TELEPHONY LAYER                                  │   │
│  │   Customer Phone → PSTN → SIP Trunk (Telnyx/Twilio) → LiveKit SIP Server    │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                        │                                             │
│                                        ▼                                             │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │                              LIVEKIT ECOSYSTEM                                │   │
│  │                                                                               │   │
│  │   ┌─────────────┐    ┌─────────────────────────────────────────────────┐    │   │
│  │   │   LiveKit   │    │            LiveKit Agent (Python)               │    │   │
│  │   │   Server    │◄──►│  ┌─────────┐  ┌─────────┐  ┌─────────┐         │    │   │
│  │   │   (Rooms)   │    │  │   VAD   │──│   STT   │──│   LLM   │──┐      │    │   │
│  │   └─────────────┘    │  │ Silero  │  │Deepgram │  │ GPT-4o  │  │      │    │   │
│  │                      │  └─────────┘  └─────────┘  └─────────┘  │      │    │   │
│  │                      │                                         ▼      │    │   │
│  │                      │  ┌─────────────────────────────────────────┐   │    │   │
│  │                      │  │              Tool Calls                 │   │    │   │
│  │                      │  │   query_kb │ book_apt │ create_ticket   │   │    │   │
│  │                      │  └─────────────────────────────────────────┘   │    │   │
│  │                      │                    │                    │      │    │   │
│  │                      │                    ▼               ┌────┴───┐  │    │   │
│  │                      │              ┌──────────┐          │  TTS   │  │    │   │
│  │                      │              │   MCP    │          │Cartesia│  │    │   │
│  │                      │              │  Client  │          └────────┘  │    │   │
│  │                      │              └────┬─────┘                      │    │   │
│  │                      └───────────────────┼────────────────────────────┘    │   │
│  └──────────────────────────────────────────┼─────────────────────────────────┘   │
│                                             │                                      │
│                                             ▼                                      │
│  ┌──────────────────────────────────────────────────────────────────────────────┐  │
│  │                           BACKEND SERVICES                                    │  │
│  │                                                                               │  │
│  │  ┌────────────────┐    ┌────────────────┐    ┌────────────────────────────┐  │  │
│  │  │      n8n       │    │    LightRAG    │    │     FastAPI Backend        │  │  │
│  │  │  MCP Server    │◄──►│  (Knowledge    │    │  ┌──────────────────────┐  │  │  │
│  │  │                │    │    Base)       │    │  │ PostgreSQL (Multi-  │  │  │  │
│  │  │  Tools:        │    │                │    │  │ Tenant + RBAC)      │  │  │  │
│  │  │  - query_kb    │    │  - Documents   │    │  ├──────────────────────┤  │  │  │
│  │  │  - book_appt   │    │  - Embeddings  │    │  │ Auth (JWT/API Keys) │  │  │  │
│  │  │  - check_avail │    │  - Graph RAG   │    │  ├──────────────────────┤  │  │  │
│  │  │  - create_tkt  │    │                │    │  │ Credit System       │  │  │  │
│  │  │  - checkin     │    │                │    │  ├──────────────────────┤  │  │  │
│  │  │  - escalate    │    │                │    │  │ Call Logs           │  │  │  │
│  │  └────────────────┘    └────────────────┘    │  └──────────────────────┘  │  │  │
│  │                                              └────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │                           ADMIN DASHBOARD (Next.js)                           │   │
│  │   Tenant Mgmt │ User Mgmt │ Credit Mgmt │ Call Logs │ KB Mgmt │ Analytics    │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## How to Use These Skills with Claude Code

### Step 1: Open Project in VS Code

```bash
# Clone or create the project directory
mkdir -p ~/voice-ai-platform
cd ~/voice-ai-platform

# Open in VS Code with Claude Code extension
code .
```

### Step 2: Copy Skills to Your Project

Skills are located in the `.claude/skills/` directory (standard Claude Code convention):

```
voice-ai-platform/
├── .claude/
│   └── .claude/skills/
│       ├── 00-PREREQUISITES.md
│       ├── 01-DATABASE-SCHEMA.md
│       ├── 02-AUTH-RBAC.md
│       ├── 03-LIGHTRAG-SETUP.md
│       ├── 04-N8N-MCP-SERVER.md
│       ├── 05-LIVEKIT-SETUP.md
│       ├── 06-VOICE-AGENT.md
│       ├── 07-TELEPHONY-SIP.md
│       ├── 08-ADMIN-DASHBOARD.md
│       ├── 09-CREDIT-SYSTEM.md
│       └── 10-DEPLOYMENT.md
├── docs/
├── configs/
└── src/
```

### Step 3: Use Claude Code to Build Each Component

For each skill, open the file and ask Claude Code to implement it:

```
@workspace Please implement the database schema from .claude/skills/01-DATABASE-SCHEMA.md
```

Or be more specific:

```
@workspace Following .claude/skills/02-AUTH-RBAC.md, create the JWT authentication
system with the security.py file and auth routes.
```

---

## Build Order (Follow This Sequence)

### Phase 1: Foundation
| # | Skill | What It Creates |
|---|-------|-----------------|
| 00 | Prerequisites | Dev environment, Docker, API keys |
| 01 | Database Schema | PostgreSQL tables, Alembic migrations |
| 02 | Auth & RBAC | JWT auth, API keys, permissions |

### Phase 2: AI Infrastructure
| # | Skill | What It Creates |
|---|-------|-----------------|
| 03 | LightRAG Setup | Knowledge base with graph RAG |
| 04 | n8n MCP Server | Tool layer (8 tools) |
| 05 | LiveKit Setup | Voice runtime, token generation |
| 06 | Voice Agent | Python agent with STT/LLM/TTS |

### Phase 3: Telephony & UI
| # | Skill | What It Creates |
|---|-------|-----------------|
| 07 | Telephony & SIP | Inbound/outbound phone calls |
| 08 | Admin Dashboard | Next.js management UI |
| 09 | Credit System | Usage tracking, billing |
| 10 | Deployment | Production setup |

---

## Claude Code Prompts for Each Skill

### Skill 00: Prerequisites
```
@workspace Read .claude/skills/00-PREREQUISITES.md and help me set up my Mac development 
environment. Create the directory structure and docker-compose files needed.
```

### Skill 01: Database Schema
```
@workspace Following .claude/skills/01-DATABASE-SCHEMA.md, create:
1. The SQLAlchemy models in src/backend/app/models/
2. The Alembic migration for the initial schema
3. The seed script for default roles
```

### Skill 02: Auth & RBAC
```
@workspace Implement the authentication system from .claude/skills/02-AUTH-RBAC.md:
1. Create core/security.py with JWT functions
2. Create api/deps.py with auth dependencies  
3. Create api/routes/auth.py with login/refresh endpoints
4. Create the permission decorator
```

### Skill 03: LightRAG Setup
```
@workspace Set up LightRAG following .claude/skills/03-LIGHTRAG-SETUP.md:
1. Create the docker-compose for LightRAG
2. Create the kb_service.py for querying
3. Create the KB API routes
```

### Skill 04: n8n MCP Server
```
@workspace Create the n8n MCP server from .claude/skills/04-N8N-MCP-SERVER.md:
1. Explain the n8n workflow setup
2. Create documentation for each of the 8 tools
3. Create the tool schemas
```

### Skill 05: LiveKit Setup
```
@workspace Set up LiveKit following .claude/skills/05-LIVEKIT-SETUP.md:
1. Create docker-compose for LiveKit
2. Create the livekit_service.py for token generation
3. Create the LiveKit API routes
```

### Skill 06: Voice Agent
```
@workspace Build the voice agent from .claude/skills/06-VOICE-AGENT.md:
1. Create src/agent/ directory structure
2. Create the main agent with VoiceAssistant
3. Create the MCP client for tool calls
4. Create the system prompts for Healthcare and Hospitality
```

### Skill 07: Telephony & SIP
```
@workspace Implement telephony from .claude/skills/07-TELEPHONY-SIP.md:
1. Create the SIP trunk configuration
2. Create the SIP service for outbound calls
3. Create the campaign manager for bulk calling
4. Create the webhook handlers
```

### Skill 08: Admin Dashboard
```
@workspace Build the admin dashboard from .claude/skills/08-ADMIN-DASHBOARD.md:
1. Initialize Next.js project in src/admin-ui/
2. Create the authentication pages
3. Create the tenant management pages
4. Create the credit management pages
```

### Skill 09: Credit System
```
@workspace Implement the credit system from .claude/skills/09-CREDIT-SYSTEM.md:
1. Create the credit configuration
2. Create the credit service
3. Create the credit API routes
4. Create the usage tracker for the agent
```

### Skill 10: Deployment
```
@workspace Set up production deployment from .claude/skills/10-DEPLOYMENT.md:
1. Create the production docker-compose
2. Create the nginx configuration
3. Create the Dockerfiles
4. Create the deployment scripts
```

---

## Project Structure (Final)

```
voice-ai-platform/
├── .claude/skills/                          # Build guides (you're here)
│   ├── 00-PREREQUISITES.md
│   ├── 01-DATABASE-SCHEMA.md
│   ├── 02-AUTH-RBAC.md
│   ├── 03-LIGHTRAG-SETUP.md
│   ├── 04-N8N-MCP-SERVER.md
│   ├── 05-LIVEKIT-SETUP.md
│   ├── 06-VOICE-AGENT.md
│   ├── 07-TELEPHONY-SIP.md
│   ├── 08-ADMIN-DASHBOARD.md
│   ├── 09-CREDIT-SYSTEM.md
│   └── 10-DEPLOYMENT.md
│
├── docs/                            # Documentation
│   ├── API.md                       # API reference
│   ├── PROMPTS.md                   # System prompt templates
│   └── TENANT-ONBOARDING.md         # Onboarding guide
│
├── configs/                         # Configuration files
│   ├── docker-compose.yml           # Local development
│   ├── docker-compose.prod.yml      # Production
│   ├── env.example                  # Environment template
│   ├── nginx/                       # Nginx configs
│   ├── livekit/                     # LiveKit configs
│   └── prometheus/                  # Monitoring configs
│
├── src/
│   ├── backend/                     # FastAPI Backend
│   │   ├── app/
│   │   │   ├── api/
│   │   │   │   ├── deps.py          # Auth dependencies
│   │   │   │   └── routes/
│   │   │   │       ├── auth.py
│   │   │   │       ├── tenants.py
│   │   │   │       ├── users.py
│   │   │   │       ├── credits.py
│   │   │   │       ├── calls.py
│   │   │   │       ├── kb.py
│   │   │   │       ├── livekit.py
│   │   │   │       └── webhooks.py
│   │   │   ├── core/
│   │   │   │   ├── config.py
│   │   │   │   ├── security.py
│   │   │   │   └── credit_config.py
│   │   │   ├── db/
│   │   │   │   ├── base.py
│   │   │   │   └── session.py
│   │   │   ├── models/
│   │   │   │   ├── tenant.py
│   │   │   │   ├── user.py
│   │   │   │   ├── role.py
│   │   │   │   ├── call_log.py
│   │   │   │   ├── credit.py
│   │   │   │   └── phone_number.py
│   │   │   ├── schemas/
│   │   │   └── services/
│   │   │       ├── auth_service.py
│   │   │       ├── credit_service.py
│   │   │       ├── kb_service.py
│   │   │       ├── livekit_service.py
│   │   │       ├── sip_service.py
│   │   │       └── campaign_service.py
│   │   ├── alembic/
│   │   ├── scripts/
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   │
│   ├── agent/                       # LiveKit Voice Agent
│   │   ├── agents/
│   │   │   └── voice_agent.py
│   │   ├── plugins/
│   │   │   └── mcp_client.py
│   │   ├── prompts/
│   │   │   ├── healthcare.py
│   │   │   └── hospitality.py
│   │   ├── utils/
│   │   │   └── usage_tracker.py
│   │   ├── config.py
│   │   ├── main.py
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   │
│   ├── admin-ui/                    # Next.js Admin Dashboard
│   │   ├── src/
│   │   │   ├── app/
│   │   │   ├── components/
│   │   │   └── lib/
│   │   ├── Dockerfile
│   │   └── package.json
│   │
│   ├── n8n-workflows/               # Exported n8n workflows
│   │   └── mcp-server.json
│   │
│   └── lightrag/                    # LightRAG (cloned)
│       ├── Dockerfile
│       └── docker-compose.yml
│
├── templates/                       # Prompt templates
│   ├── healthcare.md
│   └── hospitality.md
│
├── scripts/                         # Utility scripts
│   ├── deploy.sh
│   └── backup.sh
│
├── CLAUDE-CODE.md                   # This file
├── QUICKSTART.md                    # Quick start guide
└── README.md                        # Project readme
```

---

## Key Technologies

| Component | Technology | Purpose |
|-----------|------------|---------|
| Voice Runtime | LiveKit | Real-time audio/video rooms |
| Speech-to-Text | Deepgram | Convert speech to text |
| LLM | GPT-4o | Conversation intelligence |
| Text-to-Speech | Cartesia | Natural voice synthesis |
| Knowledge Base | LightRAG | Graph-based RAG |
| Tool Layer | n8n + MCP | External tool integration |
| Backend | FastAPI | REST API server |
| Database | PostgreSQL | Multi-tenant data |
| Auth | JWT + API Keys | Authentication |
| Admin UI | Next.js | Management dashboard |
| Telephony | Telnyx/Twilio | Phone connectivity |

---

## Multi-Tenant Features

- **Tenant Isolation**: Each tenant has separate data, KB, credits
- **RBAC**: Super Admin, Tenant Admin, Tenant User, API Only roles
- **Credit System**: Per-tenant credit balance with usage tracking
- **Call Types**: Configurable inbound/outbound per tenant
- **Custom Prompts**: Each tenant can customize agent behavior
- **Phone Numbers**: Multiple numbers per tenant with warmth tracking

---

## Credit Rates (Configurable)

| Resource | Rate |
|----------|------|
| Inbound Call | 1.0 credit/minute |
| Outbound Call | 2.0 credits/minute |
| STT (Deepgram) | 0.5 credits/minute |
| TTS (Cartesia) | 0.05 credits/1K chars |
| LLM Input | 0.05 credits/1K tokens |
| LLM Output | 0.15 credits/1K tokens |
| RAG Query | 0.02 credits/query |

---

## Quick Commands

```bash
# Start local development
docker compose -f configs/docker-compose.yml up -d

# Run database migrations
cd src/backend && alembic upgrade head

# Start backend
cd src/backend && uvicorn app.main:app --reload

# Start voice agent
cd src/agent && python main.py dev

# Run tests
cd src/backend && pytest
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Docker can't connect | Ensure Docker Desktop is running |
| LightRAG not responding | Check Ollama is running for embeddings |
| n8n workflow inactive | Activate workflow in n8n UI |
| Agent not connecting | Verify LIVEKIT_URL format |
| Credits not deducting | Check internal API key config |

---

## Support

- **LiveKit Docs**: https://docs.livekit.io
- **Deepgram Docs**: https://developers.deepgram.com
- **n8n Docs**: https://docs.n8n.io
- **LightRAG**: https://github.com/HKUDS/LightRAG

---

## Next Steps After Building

1. **Test locally** with browser voice
2. **Add knowledge base content** for your use case
3. **Customize prompts** for Healthcare or Hospitality
4. **Set up phone numbers** with Telnyx
5. **Deploy to production** following skill 10
6. **Onboard first tenant** following docs/TENANT-ONBOARDING.md
