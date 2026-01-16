# Outbound Call Architecture - Migration Guide

This document explains the outbound calling architecture used in this project. It is designed to help migrate projects from **LangGraph + Twilio** to this **LiveKit Cloud + SIP** architecture.

---

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Key Components](#key-components)
3. [Technology Stack Comparison](#technology-stack-comparison)
4. [Step-by-Step Flow](#step-by-step-flow)
5. [Code Components](#code-components)
6. [Configuration](#configuration)
7. [Migration Mapping](#migration-mapping)
8. [Environment Setup](#environment-setup)
9. [Running Outbound Calls](#running-outbound-calls)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        OUTBOUND CALL ARCHITECTURE                                │
│                                                                                  │
│  ┌─────────────┐    ┌─────────────────┐    ┌─────────────────┐                 │
│  │   Trigger   │───▶│   LiveKit API   │───▶│  LiveKit Cloud  │                 │
│  │  (Script/   │    │  (Python SDK)   │    │   SIP Server    │                 │
│  │   Backend)  │    └─────────────────┘    └────────┬────────┘                 │
│  └─────────────┘                                    │                           │
│                                                     ▼                           │
│                                          ┌─────────────────┐                   │
│                                          │   SIP Trunk     │                   │
│                                          │ (Twilio BYOC)   │                   │
│                                          └────────┬────────┘                   │
│                                                   │                            │
│                                                   ▼                            │
│                                          ┌─────────────────┐                   │
│                                          │  Customer Phone │                   │
│                                          │     (PSTN)      │                   │
│                                          └─────────────────┘                   │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                        VOICE AGENT (Runs in LiveKit Room)                │   │
│  │                                                                          │   │
│  │  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐          │   │
│  │  │  Silero  │───▶│ Deepgram │───▶│  OpenAI  │───▶│ Cartesia │          │   │
│  │  │   VAD    │    │   STT    │    │  GPT-4o  │    │   TTS    │          │   │
│  │  └──────────┘    └──────────┘    └──────────┘    └──────────┘          │   │
│  │                                                                          │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### High-Level Flow

1. **Trigger** initiates an outbound call via LiveKit API
2. **LiveKit Cloud** creates a SIP participant through the outbound trunk
3. **SIP Trunk** (Twilio BYOC) routes the call to PSTN
4. **Customer answers** the call
5. **Voice Agent** is dispatched to the LiveKit room
6. **Agent** handles the conversation using STT → LLM → TTS pipeline

---

## Key Components

### 1. LiveKit Cloud (Voice Runtime)
- **Role**: Central voice communication platform
- **Handles**: Room management, audio/video streaming, SIP integration
- **URL**: `wss://your-project.livekit.cloud`

### 2. SIP Trunk (Twilio BYOC)
- **Role**: Bridges LiveKit to PSTN (phone network)
- **Type**: Outbound trunk for making calls
- **Address**: `outbound-trunk-garima.pstn.twilio.com`
- **Authentication**: Username/password credentials

### 3. Voice Agent (Python Worker)
- **Role**: Handles conversation logic
- **Components**:
  - **VAD (Silero)**: Detects when user is speaking
  - **STT (Deepgram)**: Converts speech to text
  - **LLM (OpenAI GPT-4o)**: Generates responses
  - **TTS (Cartesia)**: Converts text to speech

### 4. Agent Dispatch
- **Role**: Routes voice agents to rooms
- **Mechanism**: Dispatch rules or manual dispatch via API

---

## Technology Stack Comparison

| Component | Old Stack (Twilio/LangGraph) | New Stack (LiveKit) |
|-----------|------------------------------|---------------------|
| **Telephony** | Twilio Voice API | LiveKit SIP + Twilio BYOC |
| **Voice Streaming** | Twilio Media Streams | LiveKit WebRTC Rooms |
| **Agent Framework** | LangGraph | LiveKit Agents SDK |
| **STT** | Twilio/Whisper | Deepgram |
| **LLM** | OpenAI via LangChain | OpenAI via LiveKit Plugin |
| **TTS** | ElevenLabs/Twilio | Cartesia |
| **VAD** | Manual/External | Silero (built-in) |
| **State Management** | LangGraph State | LiveKit Room State |
| **Call Control** | TwiML/REST API | LiveKit SIP API |

---

## Step-by-Step Flow

### Outbound Call Initiation

```
1. Script calls LiveKit API
   └── CreateSIPParticipantRequest
       ├── sip_trunk_id: "ST_txDQCysAYNDh" (outbound trunk)
       ├── sip_call_to: "+61410241020" (destination number)
       ├── room_name: "call-outbound-{timestamp}"
       └── participant_identity: "outbound-caller"

2. LiveKit Cloud processes request
   └── Creates a new Room (if not exists)
   └── Initiates SIP INVITE via trunk
   └── Connects call audio to room

3. Call connects to PSTN
   └── Twilio BYOC routes to destination
   └── Customer phone rings
   └── Customer answers

4. Agent Dispatch
   └── CreateAgentDispatchRequest
       ├── room: "call-outbound-{timestamp}"
       └── agent_name: "telephony-agent"

5. Voice Agent activates
   └── Joins the LiveKit room
   └── Starts STT/LLM/TTS pipeline
   └── Begins conversation
```

---

## Code Components

### File Structure

```
prototype/
├── outbound_call.py              # Main outbound call script
├── voice_agent_telephony.py      # Voice agent with telephony support
├── voice_agent.py                # Basic voice agent
├── create_dispatch_rules.py      # Create SIP dispatch rules
├── create_outbound_dispatch.py   # Create outbound-specific dispatch
├── update_outbound_dispatch.py   # Update dispatch rules
├── config/
│   └── outbound-trunk.json       # Trunk configuration
├── requirements.txt              # Python dependencies
└── .env                          # Environment variables
```

### 1. Outbound Call Script (`outbound_call.py`)

This is the entry point for initiating outbound calls.

**Key Function**: `make_outbound_call(to_number, room_name)`

```python
async def make_outbound_call(to_number: str, room_name: str = None):
    # Initialize LiveKit API
    livekit_api = api.LiveKitAPI()

    # Create SIP participant request
    request = CreateSIPParticipantRequest(
        sip_trunk_id=OUTBOUND_TRUNK_ID,      # Your outbound trunk ID
        sip_call_to=to_number,                # E.164 format phone number
        room_name=room_name,                  # Auto-generated if not provided
        participant_identity="outbound-caller",
        participant_name=f"Outbound Call to {to_number}",
        krisp_enabled=True,                   # Noise cancellation
        wait_until_answered=True              # Wait for answer
    )

    # Initiate the call
    participant = await livekit_api.sip.create_sip_participant(request)

    # Dispatch agent to room
    agent_dispatch_request = CreateAgentDispatchRequest(
        room=room_name,
        agent_name="telephony-agent"
    )
    dispatch = await livekit_api.agent_dispatch.create_dispatch(agent_dispatch_request)
```

### 2. Voice Agent (`voice_agent_telephony.py`)

The agent that handles the conversation.

**Key Components**:

```python
# Agent definition
class VoiceAssistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""You are a friendly voice assistant on a phone call.
            Keep your responses very concise and conversational."""
        )

# Agent server with named agent
server = AgentServer()

@server.rtc_session(agent_name="telephony-agent")
async def voice_agent(ctx: agents.JobContext):
    # Create session with AI pipeline
    session = AgentSession(
        stt=deepgram.STT(),           # Speech-to-Text
        llm=openai.LLM(model="gpt-4o"), # Language Model
        tts=cartesia.TTS(),           # Text-to-Speech
        vad=silero.VAD.load(),        # Voice Activity Detection
    )

    # Start the session in the room
    await session.start(
        room=ctx.room,
        agent=VoiceAssistant(),
    )

    # Generate initial greeting
    await session.generate_reply(
        instructions="Greet the caller warmly and ask how you can help them today."
    )
```

### 3. Dispatch Rules (`create_dispatch_rules.py`)

Configures how agents are assigned to calls.

```python
# Room configuration with agent assignment
room_config = RoomConfiguration(
    agents=[
        RoomAgentDispatch(
            agent_name="telephony-agent",  # Must match @server.rtc_session(agent_name=)
        )
    ]
)

# Dispatch rule for outbound calls
request = CreateSIPDispatchRuleRequest(
    rule=SIPDispatchRule(
        dispatch_rule_direct=SIPDispatchRuleDirect(
            room_name="outbound-call-",    # Room name prefix
            pin=""
        )
    ),
    trunk_ids=[OUTBOUND_TRUNK_ID],
    name="Outbound Calls",
    room_config=room_config,
)
```

---

## Configuration

### SIP Trunk Configuration (`config/outbound-trunk.json`)

```json
{
  "trunk": {
    "name": "Twilio Outbound Trunk",
    "address": "outbound-trunk-garima.pstn.twilio.com",
    "numbers": ["+61255630920"],
    "authUsername": "test-admin",
    "authPassword": "Pazzword@123"
  }
}
```

**Creating the trunk via LiveKit CLI**:
```bash
lk sip outbound create --config config/outbound-trunk.json
```

### Environment Variables (`.env`)

```bash
# LiveKit Cloud Configuration
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your_api_key_here
LIVEKIT_API_SECRET=your_api_secret_here

# AI Service API Keys
DEEPGRAM_API_KEY=your_deepgram_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
CARTESIA_API_KEY=your_cartesia_api_key_here
```

---

## Migration Mapping

### From Twilio Voice API to LiveKit SIP

| Twilio Concept | LiveKit Equivalent |
|----------------|-------------------|
| `client.calls.create()` | `livekit_api.sip.create_sip_participant()` |
| TwiML `<Connect><Stream>` | LiveKit Room + Agent Dispatch |
| Twilio Media Streams | LiveKit Audio Tracks |
| `CallSid` | `participant_id` / `room_name` |
| Twilio Webhooks | LiveKit Webhooks |
| Voice URL | Agent Dispatch Rules |

### From LangGraph to LiveKit Agents

| LangGraph Concept | LiveKit Agents Equivalent |
|-------------------|---------------------------|
| `StateGraph` | `AgentSession` state |
| `@graph.node` | Agent methods / generate_reply |
| `graph.add_edge` | Session flow control |
| `ToolNode` | LiveKit function calling |
| `MessagesState` | Room metadata / participant attributes |
| `checkpointer` | External state store (Redis/DB) |

### STT/TTS Migration

| Old Service | New Service | Notes |
|-------------|-------------|-------|
| Twilio Speech | Deepgram STT | Better accuracy, streaming |
| Whisper | Deepgram STT | Real-time vs batch |
| ElevenLabs | Cartesia TTS | Lower latency |
| AWS Polly | Cartesia TTS | More natural voices |

---

## Environment Setup

### Prerequisites

1. **LiveKit Cloud Account**
   - Sign up at https://cloud.livekit.io
   - Create a project
   - Get API key and secret

2. **Twilio Account** (for SIP trunk)
   - Create Elastic SIP Trunk
   - Configure BYOC (Bring Your Own Carrier)
   - Get trunk credentials

3. **AI Service Accounts**
   - Deepgram: https://console.deepgram.com
   - OpenAI: https://platform.openai.com
   - Cartesia: https://cartesia.ai

### Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Dependencies (`requirements.txt`)

```
livekit
livekit-api
livekit-agents
livekit-plugins-deepgram
livekit-plugins-openai
livekit-plugins-cartesia
livekit-plugins-silero
python-dotenv
```

---

## Running Outbound Calls

### Step 1: Start the Voice Agent Worker

The agent worker must be running to handle calls:

```bash
source venv/bin/activate
python voice_agent_telephony.py dev
```

This starts the agent worker that:
- Connects to LiveKit Cloud
- Listens for room events
- Dispatches `telephony-agent` when needed

### Step 2: Make an Outbound Call

```bash
source venv/bin/activate
python outbound_call.py +61410241020
```

**With custom room name**:
```bash
python outbound_call.py +61410241020 my-custom-room
```

### Expected Output

```
Initiating outbound call...
  To:   +61410241020
  Room: call-outbound-1768549299
  Trunk: ST_txDQCysAYNDh

Call connected successfully!
  Participant SID: PA_XGGVZVfrm8aH
  Room: call-outbound-1768549299

Dispatching agent to room...
  Agent dispatch ID: AD_6trGHWYJBdwj

The voice agent is now active in the call.
```

---

## Key IDs and Constants

| Constant | Value | Description |
|----------|-------|-------------|
| `OUTBOUND_TRUNK_ID` | `ST_txDQCysAYNDh` | LiveKit SIP outbound trunk |
| `INBOUND_TRUNK_ID` | `ST_N8mmUzK2obs2` | LiveKit SIP inbound trunk |
| `AGENT_NAME` | `telephony-agent` | Agent name for dispatch |

---

## Integration Points for Migration

### 1. Replace Twilio Call Initiation

**Old (Twilio)**:
```python
from twilio.rest import Client
client = Client(account_sid, auth_token)
call = client.calls.create(
    to="+61410241020",
    from_="+61255630920",
    url="https://your-server.com/voice"
)
```

**New (LiveKit)**:
```python
from livekit import api
from livekit.protocol.sip import CreateSIPParticipantRequest

livekit_api = api.LiveKitAPI()
request = CreateSIPParticipantRequest(
    sip_trunk_id="ST_txDQCysAYNDh",
    sip_call_to="+61410241020",
    room_name="call-outbound-123",
    participant_identity="outbound-caller",
)
participant = await livekit_api.sip.create_sip_participant(request)
```

### 2. Replace LangGraph Agent with LiveKit Agent

**Old (LangGraph)**:
```python
from langgraph.graph import StateGraph

graph = StateGraph(MessagesState)
graph.add_node("agent", call_model)
graph.add_node("tools", tool_node)
graph.add_edge("agent", "tools")
app = graph.compile()
```

**New (LiveKit Agents)**:
```python
from livekit.agents import Agent, AgentSession

class VoiceAssistant(Agent):
    def __init__(self):
        super().__init__(instructions="Your prompt here")

session = AgentSession(
    stt=deepgram.STT(),
    llm=openai.LLM(model="gpt-4o"),
    tts=cartesia.TTS(),
    vad=silero.VAD.load(),
)
await session.start(room=ctx.room, agent=VoiceAssistant())
```

### 3. Replace Media Streams with LiveKit Tracks

**Old (Twilio Media Streams)**:
- WebSocket connection to receive audio
- Manual STT integration
- Manual audio playback

**New (LiveKit)**:
- Audio automatically flows through room
- STT/TTS handled by plugins
- No manual audio handling needed

---

## Troubleshooting

### Common Issues

1. **"No module named 'livekit'"**
   ```bash
   source venv/bin/activate
   pip install livekit-api livekit-agents
   ```

2. **"Missing LiveKit credentials"**
   - Check `.env` file exists
   - Verify `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET` are set

3. **Call fails to connect**
   - Verify trunk ID is correct
   - Check Twilio SIP trunk configuration
   - Ensure number is in E.164 format (`+` prefix)

4. **Agent doesn't join call**
   - Ensure agent worker is running (`python voice_agent_telephony.py dev`)
   - Verify agent name matches dispatch rule (`telephony-agent`)

---

## Summary

This architecture replaces the traditional Twilio + LangGraph stack with:

1. **LiveKit Cloud** for voice runtime (rooms, audio streaming)
2. **LiveKit SIP** for PSTN connectivity (via Twilio BYOC)
3. **LiveKit Agents SDK** for conversation handling
4. **Plugin-based AI services** (Deepgram, OpenAI, Cartesia)

The key advantages:
- Unified voice infrastructure
- Real-time audio streaming (WebRTC)
- Built-in STT/TTS/VAD plugins
- Simpler agent development
- Better latency and audio quality
