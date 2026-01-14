# Multi-Tenant Voice AI Platform

## Project Overview

A production-ready, multi-tenant Voice AI Agent platform for enterprise customer support across Healthcare, Hospitality, and other verticals.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              TENANT LAYER                                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                              │
│  │ Healthcare  │  │ Hospitality │  │  Tenant N   │                              │
│  │   Tenant    │  │   Tenant    │  │             │                              │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘                              │
└─────────┼────────────────┼────────────────┼─────────────────────────────────────┘
          │                │                │
          ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           AUTHENTICATION LAYER                                   │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │  Keycloak / Auth0 / Custom JWT Auth                                      │   │
│  │  - Multi-tenant RBAC                                                     │   │
│  │  - API Key Management                                                    │   │
│  │  - Credit/Usage Tracking                                                 │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            TELEPHONY LAYER                                       │
│                                                                                  │
│  INBOUND FLOW:                           OUTBOUND FLOW:                         │
│  ┌──────────┐    ┌──────────────┐        ┌──────────────┐    ┌──────────┐      │
│  │  PBX     │───▶│ SIP Trunk    │        │ SIP Trunk    │───▶│ Customer │      │
│  │ (Hotel)  │    │ (Telnyx/     │        │ (Telnyx/     │    │  Phone   │      │
│  └──────────┘    │  Twilio)     │        │  Twilio)     │    └──────────┘      │
│                  └──────┬───────┘        └──────▲───────┘                       │
│                         │                       │                               │
│                         ▼                       │                               │
│                  ┌──────────────────────────────┴───────┐                       │
│                  │         LiveKit SIP Server           │                       │
│                  │         (Port 5060 + RTP)            │                       │
│                  └──────────────────┬──────────────────┘                       │
└─────────────────────────────────────┼───────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           LIVEKIT ECOSYSTEM                                      │
│                                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────┐     │
│  │                    LiveKit Server (WebRTC)                              │     │
│  │                    - Room Management                                    │     │
│  │                    - Media Routing                                      │     │
│  │                    - Token Auth                                         │     │
│  └────────────────────────────────┬───────────────────────────────────────┘     │
│                                   │                                              │
│  ┌────────────────────────────────▼───────────────────────────────────────┐     │
│  │                    LiveKit Agent (Python)                               │     │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                     │     │
│  │  │    VAD      │  │ Agent Core  │  │   Tools     │                     │     │
│  │  │  (Silero)   │  │  + Prompts  │  │ (MCP Client)│                     │     │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                     │     │
│  └────────────────────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              AI CLOUD LAYER                                      │
│                                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                       │
│  │   Deepgram   │    │   GPT-4o     │    │   Cartesia   │                       │
│  │    (STT)     │    │   (LLM)      │    │    (TTS)     │                       │
│  │              │    │              │    │              │                       │
│  │ - Streaming  │    │ - Tool Call  │    │ - Low Latency│                       │
│  │ - Multilang  │    │ - Function   │    │ - Natural    │                       │
│  └──────────────┘    └──────────────┘    └──────────────┘                       │
└─────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            MCP SERVER LAYER (n8n)                                │
│                                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────┐     │
│  │                         n8n MCP Server                                  │     │
│  │                                                                         │     │
│  │  Tools Available:                                                       │     │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐       │     │
│  │  │ query_kb    │ │book_appt    │ │create_ticket│ │get_customer │       │     │
│  │  │ (LightRAG)  │ │(Calendar)   │ │(ServiceNow) │ │  (CRM)      │       │     │
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘       │     │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐       │     │
│  │  │check_in     │ │room_service │ │escalate_    │ │log_call     │       │     │
│  │  │  (PMS)      │ │  (PMS)      │ │  human      │ │ (Analytics) │       │     │
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘       │     │
│  └────────────────────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           BACKEND SERVICES                                       │
│                                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  LightRAG    │  │  ServiceNow  │  │    PMS       │  │  PostgreSQL  │         │
│  │   (RAG)      │  │   (ITSM)     │  │ (Property)   │  │   (Core DB)  │         │
│  │              │  │              │  │              │  │              │         │
│  │ - Knowledge  │  │ - Tickets    │  │ - Bookings   │  │ - Tenants    │         │
│  │ - Documents  │  │ - Incidents  │  │ - Check-in   │  │ - Users      │         │
│  │ - Graph      │  │ - CMDB       │  │ - Services   │  │ - Credits    │         │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Telephony** | Telnyx/Twilio | SIP Trunking, Phone Numbers |
| **Voice Runtime** | LiveKit + LiveKit SIP | WebRTC, SIP Bridge |
| **STT** | Deepgram | Speech-to-Text (streaming) |
| **LLM** | GPT-4o / Claude | Reasoning, Tool Calling |
| **TTS** | Cartesia | Text-to-Speech (low latency) |
| **RAG** | LightRAG | Knowledge Base, Graph RAG |
| **MCP/Tools** | n8n | Workflow automation, API orchestration |
| **Backend DB** | PostgreSQL | Tenants, Users, Credits, Logs |
| **Cache** | Redis | Sessions, Rate Limiting |
| **Auth** | Keycloak/Custom JWT | Multi-tenant RBAC |
| **Admin UI** | Next.js + Tailwind | Admin Dashboard |
| **Containers** | Docker + Docker Compose | Local & Production |

---

## Project Structure

```
voice-ai-platform/
├── PROJECT.md                    # This file
├── .claude/skills/                       # Claude Code Skills
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
├── docs/
│   ├── API.md
│   ├── TENANT-ONBOARDING.md
│   └── PROMPTS.md
├── templates/
│   ├── healthcare/
│   ├── hospitality/
│   └── generic/
├── configs/
│   ├── docker-compose.yml
│   ├── docker-compose.prod.yml
│   └── env.example
└── src/                          # Source code (generated)
    ├── backend/                  # FastAPI Backend
    ├── agent/                    # LiveKit Voice Agent
    ├── admin-ui/                 # Next.js Admin
    ├── n8n-workflows/            # n8n workflow exports
    └── lightrag/                 # LightRAG config
```

---

## Build Order (Follow Skills in Sequence)

1. **Prerequisites** → Set up Mac environment, Docker, API keys
2. **Database Schema** → PostgreSQL with multi-tenant tables
3. **Auth & RBAC** → JWT auth, roles, permissions
4. **LightRAG** → Knowledge base setup
5. **n8n MCP Server** → Tool definitions and workflows
6. **LiveKit** → Server + Agent setup
7. **Voice Agent** → Python agent with Deepgram/GPT-4o/Cartesia
8. **Telephony** → SIP trunk, phone numbers, inbound/outbound
9. **Admin Dashboard** → Tenant/user/credit management UI
10. **Credit System** → Token tracking, billing, limits
11. **Deployment** → Production deployment guide

---

## Multi-Tenant Model

```
Platform Admin (Super Admin)
    │
    ├── Tenant A (Healthcare Clinic)
    │   ├── Admin (can manage users, view reports)
    │   ├── Agent Config (system prompt, tools enabled)
    │   ├── Knowledge Base (clinic-specific docs)
    │   ├── Phone Numbers (inbound/outbound)
    │   └── Credit Balance (tokens, call minutes)
    │
    ├── Tenant B (Hotel Chain)
    │   ├── Admin
    │   ├── Agent Config
    │   ├── Knowledge Base
    │   ├── Phone Numbers
    │   └── Credit Balance
    │
    └── Tenant N...
```

---

## Credit System Overview

| Resource | Unit | Typical Rate |
|----------|------|--------------|
| Inbound Call | Per minute | 1 credit/min |
| Outbound Call | Per minute | 2 credits/min |
| STT (Deepgram) | Per minute | 0.5 credits/min |
| LLM (GPT-4o) | Per 1K tokens | 0.1 credits/1K |
| TTS (Cartesia) | Per 1K chars | 0.05 credits/1K |
| RAG Query | Per query | 0.02 credits |

Credits are deducted in real-time. Admins can top-up tenant accounts.

---

## Quick Start (After Building)

```bash
# 1. Clone and setup
git clone <your-repo>
cd voice-ai-platform

# 2. Copy environment
cp configs/env.example .env
# Edit .env with your API keys

# 3. Start all services
docker compose up -d

# 4. Initialize database
docker compose exec backend python -m alembic upgrade head

# 5. Create super admin
docker compose exec backend python scripts/create_superadmin.py

# 6. Access services
# - Admin UI: http://localhost:3000
# - n8n: http://localhost:5678
# - LightRAG: http://localhost:9621
# - LiveKit: ws://localhost:7880
```

---

## Next Steps

Open each skill file in order and follow the instructions with Claude Code:

```
.claude/skills/00-PREREQUISITES.md  →  Start here
```
