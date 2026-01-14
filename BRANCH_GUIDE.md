# Branch Guide

This document explains the branch structure for the Voice AI project.

## Branch Structure

```
main
  └─ feature/livekit-prototype (LOCAL SETUP)
  └─ feature/livekit-cloud-telephony (CLOUD + TELEPHONY)
```

## Branch: `feature/livekit-prototype`

**Purpose:** Local LiveKit development and testing

**Use this branch for:**
- Local development with LiveKit server running in Docker
- Testing voice agent locally before deploying to cloud
- Rapid prototyping without incurring cloud costs
- Offline development

**Contains:**
- ✅ `voice_agent.py` - Basic voice agent for local testing
- ✅ `docker-compose.yml` - Local LiveKit server setup
- ✅ `test_livekit.py` - Connectivity tests
- ✅ `test_voice_agent.py` - Voice agent validation
- ✅ `.env.example` - Template with localhost configuration
- ✅ `README.md` - Setup instructions

**Configuration:**
```bash
# .env for this branch
LIVEKIT_URL=http://localhost:7880
LIVEKIT_API_KEY=devkey
LIVEKIT_API_SECRET=secret

DEEPGRAM_API_KEY=your_key
OPENAI_API_KEY=your_key
CARTESIA_API_KEY=your_key
```

**How to use:**
```bash
# Switch to this branch
git checkout feature/livekit-prototype

# Start local LiveKit server
cd prototype
docker compose up -d

# Run agent
source venv/bin/activate
python voice_agent.py dev

# Test in browser
open http://localhost:3000
```

**What's NOT in this branch:**
- ❌ Twilio integration
- ❌ SIP trunk configuration
- ❌ LiveKit Cloud credentials
- ❌ `voice_agent_telephony.py`
- ❌ `config/` folder with SIP configs
- ❌ Cloud setup documentation

---

## Branch: `feature/livekit-cloud-telephony`

**Purpose:** Production-ready cloud deployment with Twilio telephony

**Use this branch for:**
- Production deployment
- Phone call integration via Twilio
- LiveKit Cloud hosting
- MCP backend integrations (ServiceNow, booking, calendar)
- Scalable multi-user deployments

**Contains:**
- ✅ Everything from local branch
- ✅ `voice_agent_telephony.py` - Telephony-enabled agent
- ✅ `voice_agent_mcp.py` - Agent with MCP backend integrations
- ✅ `LIVEKIT_CLOUD_SETUP.md` - Complete cloud setup guide
- ✅ `TWILIO_SETUP.md` - Twilio integration guide
- ✅ `MCP_INTEGRATION.md` - Backend system integration guide
- ✅ `MCP_QUICK_START.md` - Quick reference for MCP
- ✅ `config/cloud-inbound-trunk.json` - SIP trunk configuration
- ✅ `config/dispatch-rule.json` - Agent dispatch rules
- ✅ `config/dispatch-rule-mcp.json` - MCP agent dispatch rules
- ✅ `config/twilio-twiml-configured.xml` - TwiML configuration

**Configuration:**
```bash
# .env for this branch
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=APIxxxxx
LIVEKIT_API_SECRET=your_secret

DEEPGRAM_API_KEY=your_key
OPENAI_API_KEY=your_key
CARTESIA_API_KEY=your_key

# Backend integrations (optional, for MCP)
SERVICENOW_INSTANCE_URL=https://your-instance.service-now.com
SERVICENOW_USERNAME=your_username
SERVICENOW_PASSWORD=your_password

BOOKING_SYSTEM_URL=https://api.yourbooking.com
BOOKING_SYSTEM_API_KEY=your_api_key

CALENDAR_TYPE=google
CALENDAR_API_CREDENTIALS=/path/to/credentials.json
```

**How to use:**
```bash
# Switch to this branch
git checkout feature/livekit-cloud-telephony

# Authenticate with LiveKit Cloud
lk cloud auth

# Run telephony agent
cd prototype
source venv/bin/activate
python voice_agent_telephony.py start

# Or run MCP-enabled agent
python voice_agent_mcp.py start

# Call your Twilio number to test
```

**What's EXTRA in this branch:**
- ✅ Twilio SIP integration
- ✅ LiveKit Cloud setup
- ✅ Phone call handling
- ✅ MCP backend integrations
- ✅ Production deployment guides
- ✅ SIP trunk and dispatch configurations

---

## When to Use Each Branch

### Use `feature/livekit-prototype` when:
1. **Developing locally** - Testing new agent features without cloud costs
2. **Prototyping** - Quick iterations on STT/LLM/TTS pipeline
3. **Learning** - Understanding LiveKit basics
4. **Offline work** - No internet connection needed
5. **Cost-conscious testing** - Avoid cloud usage charges

### Use `feature/livekit-cloud-telephony` when:
1. **Production deployment** - Serving real users
2. **Phone integration** - Need Twilio/SIP connectivity
3. **Scalability** - Multiple concurrent users
4. **Backend integration** - Connecting to ServiceNow, booking systems, calendars
5. **Public access** - Sharing with users outside your local network

---

## Switching Between Branches

### From Local → Cloud

```bash
# Make sure local work is committed
git add .
git commit -m "Your changes"

# Switch to cloud branch
git checkout feature/livekit-cloud-telephony

# Update .env with cloud credentials
cp .env .env.backup
# Edit .env with LiveKit Cloud credentials

# Run cloud agent
python voice_agent_telephony.py start
```

### From Cloud → Local

```bash
# Make sure cloud work is committed
git add .
git commit -m "Your changes"

# Switch to local branch
git checkout feature/livekit-prototype

# Update .env with localhost
cp .env .env.backup
# Edit .env with localhost:7880

# Start local LiveKit
docker compose up -d

# Run local agent
python voice_agent.py dev
```

---

## File Comparison

| File | Local Branch | Cloud Branch | Purpose |
|------|--------------|--------------|---------|
| `voice_agent.py` | ✅ | ✅ | Basic agent (web clients) |
| `voice_agent_telephony.py` | ❌ | ✅ | Telephony-enabled agent |
| `voice_agent_mcp.py` | ❌ | ✅ | MCP backend integrations |
| `docker-compose.yml` | ✅ | ✅ | Local LiveKit server |
| `config/cloud-inbound-trunk.json` | ❌ | ✅ | SIP trunk config |
| `config/dispatch-rule.json` | ❌ | ✅ | Agent dispatch rules |
| `LIVEKIT_CLOUD_SETUP.md` | ❌ | ✅ | Cloud setup guide |
| `TWILIO_SETUP.md` | ❌ | ✅ | Twilio integration guide |
| `MCP_INTEGRATION.md` | ❌ | ✅ | MCP integration guide |
| `test_livekit.py` | ✅ | ✅ | Connection tests |
| `README.md` | ✅ | ✅ | Basic setup instructions |

---

## Common Workflows

### Workflow 1: Develop Locally, Deploy to Cloud

```bash
# 1. Work on local branch
git checkout feature/livekit-prototype
# ... make changes to voice_agent.py ...
git add .
git commit -m "Add new feature"
git push

# 2. Merge to cloud branch
git checkout feature/livekit-cloud-telephony
git merge feature/livekit-prototype

# 3. Test in cloud
python voice_agent_telephony.py start
# ... test with Twilio phone call ...

# 4. Push to cloud branch
git push
```

### Workflow 2: Add Cloud-Only Feature (MCP Integration)

```bash
# Work directly on cloud branch
git checkout feature/livekit-cloud-telephony

# Add MCP integration
# ... modify voice_agent_mcp.py ...

git add .
git commit -m "Add ServiceNow integration"
git push

# Local branch remains unchanged
```

### Workflow 3: Bug Fix in Local, Apply to Cloud

```bash
# Fix in local branch
git checkout feature/livekit-prototype
# ... fix bug in voice_agent.py ...
git commit -m "Fix audio sync issue"
git push

# Cherry-pick to cloud branch
git checkout feature/livekit-cloud-telephony
git cherry-pick <commit-hash>
git push
```

---

## Branch History

### feature/livekit-prototype
```
6e41c70 - Implement working voice agent with full STT-LLM-TTS pipeline
c96e853 - Add voice AI agent with STT/LLM/TTS pipeline
aa00a0d - Add LiveKit prototype for local testing
```

### feature/livekit-cloud-telephony
```
2804699 - Add MCP integration for backend systems
4311e05 - Add LiveKit Cloud integration with SIP telephony support
0f1b81a - Add Twilio telephony integration for phone calls
6e41c70 - Implement working voice agent with full STT-LLM-TTS pipeline
c96e853 - Add voice AI agent with STT/LLM/TTS pipeline
aa00a0d - Add LiveKit prototype for local testing
```

---

## Quick Reference

| Task | Command |
|------|---------|
| Switch to local | `git checkout feature/livekit-prototype` |
| Switch to cloud | `git checkout feature/livekit-cloud-telephony` |
| List all branches | `git branch -a` |
| Show current branch | `git branch --show-current` |
| Compare branches | `git diff feature/livekit-prototype feature/livekit-cloud-telephony` |
| View branch commits | `git log --oneline --graph --all` |

---

## Tips

1. **Always commit before switching branches** to avoid losing work
2. **Use separate .env files** for each branch (.env.local vs .env.cloud)
3. **Don't force push cloud branch** unless you know what you're doing
4. **Test locally first** before deploying to cloud
5. **Keep branches in sync** by regularly merging local changes to cloud
6. **Use clear commit messages** to track what changed where

---

## Future Branches

As the project grows, consider:

- `feature/web-interface` - Web UI for agent management
- `feature/analytics` - Call analytics and reporting
- `feature/multi-language` - Multi-language support
- `feature/call-recording` - Call recording and transcription
- `develop` - Integration branch
- `staging` - Pre-production testing
- `production` - Production deployments

---

## Need Help?

- **Local setup**: See `prototype/README.md`
- **Cloud setup**: See `prototype/LIVEKIT_CLOUD_SETUP.md`
- **Twilio setup**: See `prototype/TWILIO_SETUP.md`
- **MCP integration**: See `prototype/MCP_INTEGRATION.md` or `prototype/MCP_QUICK_START.md`
- **Git issues**: `git status`, `git log`, `git diff`
