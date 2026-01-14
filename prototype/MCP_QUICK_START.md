# MCP Integration Quick Start

## Your Question Answered

**Q: Where in the sequence diagram does MCP fit, and which file needs to be changed for MCP integration?**

**A: MCP fits BETWEEN the LLM and TTS steps. The file to modify is `voice_agent_telephony.py` (or use the new `voice_agent_mcp.py`).**

## Visual Answer

```
Phone Call Processing Flow:

┌─────────────────────────────────────────────────────────────┐
│  1. Phone → Twilio → LiveKit SIP → LiveKit Cloud            │
│                                                              │
│  2. LiveKit Cloud → voice_agent_mcp.py (your local machine) │
│                                                              │
│     a) Deepgram STT                                          │
│        Audio → Text: "Create a ticket for network issue"    │
│                                                              │
│     b) OpenAI GPT-4o                                         │
│        Understands: Need to call create_servicenow_ticket() │
│                                                              │
│     🔴 c) MCP LAYER (HAPPENS HERE!)                         │
│        - Executes function: create_servicenow_ticket()      │
│        - Calls backend: ServiceNow API                      │
│        - Gets result: {ticket_number: "INC12345"}           │
│                                                              │
│     d) GPT-4o (with result)                                  │
│        Generates: "Created ticket INC12345"                  │
│                                                              │
│     e) Cartesia TTS                                          │
│        Text → Audio                                          │
│                                                              │
│  3. Audio flows back: Agent → LiveKit → Twilio → Phone      │
└─────────────────────────────────────────────────────────────┘
```

## File to Modify

**Primary file: `voice_agent_mcp.py`** (complete example provided)

Key sections:

### 1. Backend Client Classes (Lines 25-220)
```python
class ServiceNowClient:
    # Handles ServiceNow API calls

class BookingSystemClient:
    # Handles booking system API calls

class CalendarClient:
    # Handles calendar API calls
```

### 2. Function Context - The MCP Layer (Lines 230-350)
```python
class AssistantFunctions(llm.FunctionContext):
    """This is where MCP integration happens"""

    @llm.ai_callable(description="Create ServiceNow ticket")
    async def create_servicenow_ticket(self, ...):
        # Calls ServiceNow API
        result = await servicenow.create_ticket(...)
        return f"Ticket {result['ticket_number']} created"
```

### 3. Agent Session Configuration (Line 390)
```python
session = AgentSession(
    stt=deepgram.STT(),
    llm=openai.LLM(model="gpt-4o"),
    tts=cartesia.TTS(),
    vad=silero.VAD.load(),
    fnc_ctx=AssistantFunctions(),  # 🔴 THIS LINE ENABLES MCP
)
```

## Three Required Changes

### Change 1: Add Backend Client Classes

Add API client classes for your backend systems at the top of the file:

```python
class ServiceNowClient:
    def __init__(self):
        self.instance_url = os.getenv("SERVICENOW_INSTANCE_URL")
        # ... credentials

    async def create_ticket(self, description: str) -> dict:
        # Call ServiceNow REST API
        # Return result
```

### Change 2: Define Functions for LLM to Call

Create function context with @llm.ai_callable decorated methods:

```python
class AssistantFunctions(llm.FunctionContext):

    @llm.ai_callable(description="Create a ServiceNow ticket")
    async def create_servicenow_ticket(self, description: str):
        result = await servicenow.create_ticket(description)
        return f"Ticket {result['ticket_number']} created"
```

### Change 3: Add fnc_ctx to AgentSession

Enable function calling in the agent session:

```python
session = AgentSession(
    stt=deepgram.STT(),
    llm=openai.LLM(model="gpt-4o"),
    tts=cartesia.TTS(),
    vad=silero.VAD.load(),
    fnc_ctx=AssistantFunctions(),  # 🔴 Add this line
)
```

## Quick Setup (5 Steps)

### Step 1: Add Backend Credentials to .env

```bash
# ServiceNow
SERVICENOW_INSTANCE_URL=https://your-instance.service-now.com
SERVICENOW_USERNAME=your_username
SERVICENOW_PASSWORD=your_password

# Booking System
BOOKING_SYSTEM_URL=https://api.yourbooking.com
BOOKING_SYSTEM_API_KEY=your_api_key

# Calendar
CALENDAR_TYPE=google
CALENDAR_API_CREDENTIALS=/path/to/credentials.json
```

### Step 2: Use the MCP-Enabled Agent

```bash
cd /Users/garimatyagi/work/voice-ai/prototype
source venv/bin/activate
python voice_agent_mcp.py start
```

### Step 3: Update Dispatch Rule (Optional)

If you want to use the new agent name:

```bash
lk sip dispatch create config/dispatch-rule-mcp.json
```

### Step 4: Test a Function Call

Call your Twilio number and say:

- "Create a support ticket for printer issues"
- "Book an appointment for tomorrow at 2pm"
- "Schedule a meeting for Friday at 10am"

### Step 5: Monitor Logs

Watch the agent terminal for function calls:

```
INFO: Function called: create_servicenow_ticket
INFO: ServiceNow API response: {ticket_number: "INC12345"}
INFO: Response: "Ticket INC12345 created successfully"
```

## Example Function Call Flow

### User Request
```
User: "I need to report a network outage in building 5"
```

### Processing Steps

**1. STT (Deepgram)**
```
Audio → Text: "I need to report a network outage in building 5"
```

**2. LLM Analysis (GPT-4o)**
```
Intent: Create ServiceNow ticket
Function to call: create_servicenow_ticket(
    short_description="Network outage in building 5",
    description="User reported network connectivity issues in building 5",
    priority="2"
)
```

**3. MCP Layer Execution**
```python
# In voice_agent_mcp.py
async def create_servicenow_ticket(self, short_description, description, priority):
    # Call ServiceNow REST API
    result = await servicenow.create_ticket(short_description, description, priority)
    # Result: {"ticket_number": "INC0012345", "status": "New"}
    return f"Ticket created: {result['ticket_number']}"
```

**4. Backend API Call**
```http
POST https://your-instance.service-now.com/api/now/table/incident
Content-Type: application/json
Authorization: Basic <credentials>

{
  "short_description": "Network outage in building 5",
  "description": "User reported network connectivity issues in building 5",
  "priority": "2"
}

Response: {
  "result": {
    "number": "INC0012345",
    "state": "New"
  }
}
```

**5. LLM Response Generation (GPT-4o)**
```
"I've created a support ticket for the network outage in building 5.
Your ticket number is INC0012345."
```

**6. TTS (Cartesia)**
```
Text → Audio: "I've created a support ticket..."
```

**7. User Hears**
```
"I've created a support ticket for the network outage in building 5.
Your ticket number is INC0012345."
```

## Key Files Reference

| File | Purpose |
|------|---------|
| `voice_agent_mcp.py` | Main agent with MCP integration (NEW) |
| `voice_agent_telephony.py` | Original agent without MCP |
| `MCP_INTEGRATION.md` | Complete MCP documentation |
| `config/dispatch-rule-mcp.json` | Dispatch rule for MCP agent |
| `.env` | Backend system credentials |

## Comparison: With vs Without MCP

### Without MCP (voice_agent_telephony.py)
```
User: "Create a ticket for printer issues"
Agent: "I understand you need help with printer issues.
        Please contact IT support at ext. 1234"
```
❌ **No actual action taken**

### With MCP (voice_agent_mcp.py)
```
User: "Create a ticket for printer issues"
Agent: [Calls create_servicenow_ticket()]
       [Creates actual ticket via API]
       "I've created ticket INC0012345 for your printer issues.
        IT support has been notified."
```
✅ **Actual ticket created in ServiceNow**

## Next Steps

1. ✅ **Read**: `MCP_INTEGRATION.md` for complete documentation
2. ✅ **Review**: `voice_agent_mcp.py` to see full implementation
3. ⬜ **Configure**: Add backend credentials to `.env`
4. ⬜ **Test**: Run the MCP-enabled agent locally
5. ⬜ **Customize**: Add your own backend integrations

## Common Questions

**Q: Can I use the existing voice_agent_telephony.py?**
A: Yes, but you need to add the function context. It's easier to start with voice_agent_mcp.py.

**Q: What if I don't have ServiceNow?**
A: The mock implementations work out of the box for testing. Replace with your actual APIs later.

**Q: How do I add more functions?**
A: Add methods to AssistantFunctions class with @llm.ai_callable decorator.

**Q: Will this work with phone calls?**
A: Yes! The entire flow works the same: Phone → Twilio → LiveKit → Agent (with MCP) → Backend APIs.

**Q: How long do function calls take?**
A: Typically 500ms-2s depending on your backend API response time.

## Support

For detailed information, see:
- `MCP_INTEGRATION.md` - Complete guide with examples
- `voice_agent_mcp.py` - Full working implementation
- LiveKit Agents Docs: https://docs.livekit.io/agents/function-calling/
