# Voice AI Platform

A production-ready, multi-tenant Voice AI Agent platform for Healthcare and Hospitality verticals.

## 🎯 What This Does

Build intelligent voice agents that can:
- **Answer phone calls** (inbound) and make calls (outbound)
- **Book appointments** through natural conversation
- **Query knowledge bases** using advanced RAG
- **Create support tickets** in ServiceNow/PMS
- **Track usage** with per-tenant credit billing

## 🏗️ Architecture

```
Phone Call → SIP Trunk → LiveKit → AI Agent → Tools/KB → Response
                              ↓
                         [Deepgram STT]
                         [GPT-4o LLM]
                         [Cartesia TTS]
```

## 🚀 Quick Start

```bash
# 1. Clone and enter directory
cd ~/voice-ai-platform

# 2. Copy environment template
cp configs/env.example .env

# 3. Add your API keys to .env

# 4. Start infrastructure
docker compose -f configs/docker-compose.yml up -d

# 5. Start voice agent
cd src/agent && python main.py dev
```

See [QUICKSTART.md](QUICKSTART.md) for detailed setup instructions.

## 📚 Build Guide (Skills)

This project uses **skill files** - self-contained guides for Claude Code to implement each component:

| Skill | Component | Description |
|-------|-----------|-------------|
| [00](.claude/skills/00-PREREQUISITES.md) | Prerequisites | Dev environment setup |
| [01](.claude/skills/01-DATABASE-SCHEMA.md) | Database | Multi-tenant PostgreSQL schema |
| [02](.claude/skills/02-AUTH-RBAC.md) | Auth & RBAC | JWT, API keys, permissions |
| [03](.claude/skills/03-LIGHTRAG-SETUP.md) | LightRAG | Knowledge base with graph RAG |
| [04](.claude/skills/04-N8N-MCP-SERVER.md) | n8n MCP | Tool layer (8 tools) |
| [05](.claude/skills/05-LIVEKIT-SETUP.md) | LiveKit | Voice runtime |
| [06](.claude/skills/06-VOICE-AGENT.md) | Voice Agent | Python agent with AI |
| [07](.claude/skills/07-TELEPHONY-SIP.md) | Telephony | Phone/SIP integration |
| [08](.claude/skills/08-ADMIN-DASHBOARD.md) | Admin UI | Next.js dashboard |
| [09](.claude/skills/09-CREDIT-SYSTEM.md) | Credits | Usage tracking & billing |
| [10](.claude/skills/10-DEPLOYMENT.md) | Deployment | Production setup |

See [CLAUDE-CODE.md](CLAUDE-CODE.md) for how to use these with Claude Code.

## 🔧 Tech Stack

| Layer | Technology |
|-------|------------|
| Voice Runtime | LiveKit |
| Speech-to-Text | Deepgram |
| LLM | GPT-4o |
| Text-to-Speech | Cartesia |
| Knowledge Base | LightRAG |
| Tool Server | n8n (MCP) |
| Backend | FastAPI |
| Database | PostgreSQL |
| Cache | Redis |
| Admin UI | Next.js |
| Auth | JWT + API Keys |
| Telephony | Telnyx / Twilio |

## 💼 Use Cases

### Healthcare
- Appointment scheduling
- Insurance verification questions
- Clinic information
- Prescription refill requests
- Emergency routing

### Hospitality
- Guest check-in
- Room service orders
- Concierge services
- Issue resolution
- Local recommendations

## 🏢 Multi-Tenant Features

- **Tenant Isolation**: Separate data, KB, credits per tenant
- **RBAC**: Super Admin, Tenant Admin, Tenant User roles
- **Credit System**: Per-tenant billing with usage tracking
- **Custom Agents**: Configurable prompts per tenant
- **Phone Numbers**: Multiple numbers with warmth management

## 💰 Credit Rates

| Resource | Rate |
|----------|------|
| Inbound Call | 1.0 credit/min |
| Outbound Call | 2.0 credits/min |
| STT | 0.5 credits/min |
| TTS | 0.05 credits/1K chars |
| LLM | 0.05-0.15 credits/1K tokens |
| RAG Query | 0.02 credits |

## 📁 Project Structure

```
voice-ai-platform/
├── .claude/skills/   # Build guides for Claude Code
├── docs/             # API docs, prompts, onboarding
├── configs/          # Docker, nginx, env templates
├── src/
│   ├── backend/      # FastAPI server
│   ├── agent/        # LiveKit voice agent
│   ├── admin-ui/     # Next.js dashboard
│   ├── lightrag/     # Knowledge base
│   └── n8n-workflows/# Exported workflows
├── templates/        # Prompt templates
└── scripts/          # Deploy/backup scripts
```

## 📖 Documentation

- [CLAUDE-CODE.md](CLAUDE-CODE.md) - How to use skill files with Claude Code
- [QUICKSTART.md](QUICKSTART.md) - Get running in 30 minutes
- [docs/API.md](docs/API.md) - API reference
- [docs/PROMPTS.md](docs/PROMPTS.md) - System prompt templates
- [docs/TENANT-ONBOARDING.md](docs/TENANT-ONBOARDING.md) - Onboarding guide

## 🔑 Required API Keys

| Service | Get Key At |
|---------|------------|
| OpenAI | https://platform.openai.com/api-keys |
| Deepgram | https://console.deepgram.com |
| Cartesia | https://cartesia.ai |
| Telnyx (optional) | https://portal.telnyx.com |

## 🤝 Contributing

1. Read the skill files to understand the architecture
2. Follow the coding patterns established
3. Test locally before deploying
4. Update documentation as needed

## 📄 License

MIT License - See LICENSE file

---

Built with ❤️ using LiveKit, LightRAG, and n8n
