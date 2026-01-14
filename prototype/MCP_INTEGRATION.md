# MCP Integration Guide

Complete guide for integrating Model Context Protocol (MCP) servers with your LiveKit voice agent to connect backend systems.

## What is MCP Integration?

MCP (Model Context Protocol) allows your voice AI agent to interact with external systems through function calling. When a user asks the agent to perform an action (like "create a ticket" or "book an appointment"), the LLM can call backend APIs to complete the request.

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                      Phone Call with MCP                         │
└──────────────────────────────────────────────────────────────────┘

Phone → Twilio → LiveKit SIP → LiveKit Cloud
                                      ↓
                            ┌─────────────────┐
                            │ Agent (Local)   │
                            └─────────────────┘
                                      ↓
┌─────────────────────────────────────────────────────────────────┐
│                   Agent Processing Pipeline                      │
│                                                                  │
│  1. Deepgram STT                                                │
│     Audio → "Book me an appointment for tomorrow at 2pm"        │
│                                                                  │
│  2. OpenAI GPT-4o (with function calling)                       │
│     ┌─────────────────────────────────────────┐                │
│     │ Understands intent: Book appointment    │                │
│     │ Needs to call: book_appointment()       │                │
│     └─────────────────────────────────────────┘                │
│                      ↓                                           │
│  🔴 3. MCP Function Calling Layer (NEW!)                        │
│     ┌─────────────────────────────────────────┐                │
│     │ Execute: book_appointment(              │                │
│     │   date="2024-01-15",                    │                │
│     │   time="14:00",                         │                │
│     │   service_type="consultation",          │                │
│     │   customer_name="John",                 │                │
│     │   customer_phone="+61451171321"         │                │
│     │ )                                        │                │
│     └─────────────────────────────────────────┘                │
│                      ↓                                           │
│     ┌──────────────────────────────────────────────────┐       │
│     │  Call External Backend System                    │       │
│     │  ┌────────────────────────────────────────────┐  │       │
│     │  │ Booking System API                         │  │       │
│     │  │ POST /api/bookings                         │  │       │
│     │  │ {                                          │  │       │
│     │  │   "date": "2024-01-15",                    │  │       │
│     │  │   "time": "14:00",                         │  │       │
│     │  │   "service": "consultation"                │  │       │
│     │  │ }                                          │  │       │
│     │  └────────────────────────────────────────────┘  │       │
│     │                                                    │       │
│     │  Response: {                                      │       │
│     │    "booking_id": "BK12345",                       │       │
│     │    "status": "confirmed"                          │       │
│     │  }                                                 │       │
│     └──────────────────────────────────────────────────┘       │
│                      ↓                                           │
│  4. GPT-4o generates response                                   │
│     "Your appointment is booked for tomorrow at 2pm.            │
│      Your booking ID is BK12345."                               │
│                                                                  │
│  5. Cartesia TTS                                                │
│     Text → Audio                                                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                      ↓
    Audio flows back through LiveKit → Twilio → Phone
```

## When MCP Functions Execute

The MCP function calling happens **between steps 2 and 4** in the processing pipeline:

1. **User speaks**: "Book me an appointment tomorrow at 2pm"
2. **STT** (Deepgram): Converts audio to text
3. **LLM** (GPT-4o): Understands intent and decides to call `book_appointment()`
4. **🔴 MCP LAYER**: Executes the function, calls backend API, gets result
5. **LLM** (GPT-4o): Incorporates the function result into response
6. **TTS** (Cartesia): Converts response to audio
7. **User hears**: "Your appointment is booked for tomorrow at 2pm. Your booking ID is BK12345."

## Sequence Diagram with MCP

```
Caller          Twilio      LiveKit     Agent        Deepgram    GPT-4o      MCP Layer       Backend      Cartesia
  │               │           Cloud        │             │           │            │            Systems        │
  │─────Call─────>│             │          │             │           │            │              │            │
  │               │──SIP────────>│          │             │           │            │              │            │
  │               │             │──Join────>│             │           │            │              │            │
  │               │             │<─Ack──────│             │           │            │              │            │
  │               │             │          │──Greeting───────────────>│            │              │            │
  │               │             │          │<────────────────────"Hi"─│            │              │            │
  │               │             │          │─────────────────────────────────TTS──────────────────────────────>│
  │               │             │<─Audio───│<────────────────────────────────────────────────────────Audio─────│
  │<───Audio──────│<────────────│          │             │           │            │              │            │
  │               │             │          │             │           │            │              │            │
 [T0] User: "Book appointment for tomorrow at 2pm"                   │            │              │            │
  │──────────────>│──────────────>│────────>│             │           │            │              │            │
  │               │             │          │──Audio──────>│           │            │              │            │
  │               │             │          │<─Text─────────│           │            │              │            │
  │               │             │          │           "Book appointment..."       │              │            │
  │               │             │          │───────────────────────────>│           │              │            │
  │               │             │          │                           │           │              │            │
[T1] GPT-4o analyzes intent and decides to call function              │           │              │            │
  │               │             │          │<────Call─Function─────────│           │              │            │
  │               │             │          │                           │           │              │            │
[T2] MCP Layer executes function                                      │           │              │            │
  │               │             │          │────────────────────────────────────────>│             │            │
  │               │             │          │                           │           │  book_appointment()       │
  │               │             │          │                           │           │      │        │            │
[T3] Backend API call                                                 │           │      │        │            │
  │               │             │          │                           │           │──POST /api/bookings──────>│
  │               │             │          │                           │           │      │        │            │
  │               │             │          │                           │           │      │    Process         │
  │               │             │          │                           │           │      │    Request         │
  │               │             │          │                           │           │      │        │            │
[T4] Booking confirmed                                                │           │      │        │            │
  │               │             │          │                           │           │<─Success────────────────────│
  │               │             │          │                           │           │  {booking_id: "BK12345"}   │
  │               │             │          │<────────────────────────────────────────│             │            │
  │               │             │          │         Function result   │           │              │            │
  │               │             │          │───────────────────────────>│           │              │            │
  │               │             │          │                           │           │              │            │
[T5] GPT-4o generates response with booking details                   │           │              │            │
  │               │             │          │<──Response─Text───────────│           │              │            │
  │               │             │          │    "Booked for 2pm, ID: BK12345"      │              │            │
  │               │             │          │─────────────────────────────────TTS──────────────────────────────>│
  │               │             │<─Audio───│<────────────────────────────────────────────────────────Audio─────│
  │<───Audio──────│<────────────│          │             │           │            │              │            │
  │               │             │          │             │           │            │              │            │
[T6] User hears confirmation                                          │           │              │            │
```

**Timing breakdown:**
- T0 → T1: ~200ms (STT)
- T1 → T2: ~500ms (GPT-4o decides to call function)
- T2 → T4: ~500-2000ms (Backend API call - varies by system)
- T4 → T5: ~300ms (GPT-4o generates response with result)
- T5 → T6: ~400ms (TTS)
- **Total: ~2-4 seconds** from user request to confirmation

## Files Modified for MCP Integration

### 1. Main File: `voice_agent_mcp.py`

This is the new agent file with MCP integration. Key sections:

#### Backend Client Classes
```python
class ServiceNowClient:
    """Handles ServiceNow API calls for ticket management"""

class BookingSystemClient:
    """Handles booking system API calls for appointments"""

class CalendarClient:
    """Handles calendar API calls for meeting scheduling"""
```

#### Function Context (MCP Layer)
```python
class AssistantFunctions(llm.FunctionContext):
    """Functions that GPT-4o can call during conversation"""

    @llm.ai_callable(description="Create a ServiceNow incident ticket")
    async def create_servicenow_ticket(self, short_description: str, ...):
        # Calls ServiceNow API
        result = await servicenow.create_ticket(...)
        return "Ticket created! Number: INC12345"
```

#### Agent Session with Function Calling
```python
session = AgentSession(
    stt=deepgram.STT(),
    llm=openai.LLM(model="gpt-4o"),
    tts=cartesia.TTS(),
    vad=silero.VAD.load(),
    fnc_ctx=AssistantFunctions(),  # 🔴 Enables MCP/function calling
)
```

### 2. Environment Variables: `.env`

Add backend system credentials:

```bash
# Existing LiveKit & AI credentials
LIVEKIT_URL=wss://voice-ai-t33og8bs.livekit.cloud
LIVEKIT_API_KEY=APIt64HwHuxDjpP
LIVEKIT_API_SECRET=HqfrhweK4r3xaTEhRVBLoEwVekEr9sjGPaHMDvgDITrB
DEEPGRAM_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
CARTESIA_API_KEY=your_key_here

# 🔴 NEW: Backend system credentials for MCP
# ServiceNow
SERVICENOW_INSTANCE_URL=https://your-instance.service-now.com
SERVICENOW_USERNAME=your_username
SERVICENOW_PASSWORD=your_password

# Booking System
BOOKING_SYSTEM_URL=https://api.yourbooking.com
BOOKING_SYSTEM_API_KEY=your_api_key

# Calendar (Google Calendar / Outlook)
CALENDAR_TYPE=google
CALENDAR_API_CREDENTIALS=/path/to/credentials.json
```

### 3. Dispatch Rule: `config/dispatch-rule-mcp.json`

Create a new dispatch rule for the MCP-enabled agent:

```json
{
  "dispatch_rule": {
    "rule": {
      "dispatchRuleIndividual": {
        "roomPrefix": "call-"
      }
    },
    "roomConfig": {
      "agents": [{
        "agentName": "telephony-agent-mcp"
      }]
    }
  }
}
```

## Setup Instructions

### Step 1: Update Environment Variables

Edit `.env` and add your backend system credentials:

```bash
# Copy the template
cp .env .env.backup

# Edit .env and add backend credentials
nano .env
```

### Step 2: Install Additional Dependencies (if needed)

```bash
cd /Users/garimatyagi/work/voice-ai/prototype
source venv/bin/activate

# For ServiceNow
pip install pysnow

# For Google Calendar
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client

# For general HTTP requests (if not using specific SDKs)
pip install httpx aiohttp
```

### Step 3: Update Dispatch Rule

Create the new dispatch rule for MCP-enabled agent:

```bash
# Create dispatch rule for MCP agent
lk sip dispatch create config/dispatch-rule-mcp.json

# Verify it was created
lk sip dispatch list
```

Or update your existing dispatch rule to use `telephony-agent-mcp`.

### Step 4: Run the MCP-Enabled Agent

```bash
cd /Users/garimatyagi/work/voice-ai/prototype
source venv/bin/activate
python voice_agent_mcp.py start
```

### Step 5: Test with Phone Call

Call your Twilio number and try:

1. **ServiceNow Ticket**:
   - "I need to report a network issue"
   - Agent will ask for details and create a ticket

2. **Booking Appointment**:
   - "I'd like to book an appointment for tomorrow at 2pm"
   - Agent will check availability and book

3. **Schedule Meeting**:
   - "Schedule a team meeting for Friday at 10am"
   - Agent will create calendar event

## Backend System Implementation Examples

### ServiceNow Integration

Replace the mock implementation in `ServiceNowClient.create_ticket()`:

```python
import requests

async def create_ticket(self, short_description: str, description: str, priority: str = "3") -> dict:
    url = f"{self.instance_url}/api/now/table/incident"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    data = {
        "short_description": short_description,
        "description": description,
        "priority": priority,
        "caller_id": "phone_user",
        "urgency": priority,
        "impact": priority
    }

    response = requests.post(
        url,
        auth=(self.username, self.password),
        headers=headers,
        json=data
    )

    if response.status_code == 201:
        result = response.json()["result"]
        return {
            "success": True,
            "ticket_number": result["number"],
            "short_description": result["short_description"],
            "priority": result["priority"],
            "status": result["state"]
        }
    else:
        return {"success": False, "error": response.text}
```

### Google Calendar Integration

Replace the mock implementation in `CalendarClient.schedule_meeting()`:

```python
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from datetime import datetime, timedelta

async def schedule_meeting(self, title: str, date: str, start_time: str,
                          duration_minutes: int, attendees: list = None) -> dict:
    # Load credentials
    creds = Credentials.from_authorized_user_file(self.api_credentials)
    service = build('calendar', 'v3', credentials=creds)

    # Parse datetime
    start_datetime = f"{date}T{start_time}:00"
    end_datetime = (datetime.fromisoformat(start_datetime) +
                   timedelta(minutes=duration_minutes)).isoformat()

    # Create event with Google Meet
    event = {
        'summary': title,
        'start': {
            'dateTime': start_datetime,
            'timeZone': 'Australia/Sydney',
        },
        'end': {
            'dateTime': end_datetime,
            'timeZone': 'Australia/Sydney',
        },
        'attendees': [{'email': email} for email in (attendees or [])],
        'conferenceData': {
            'createRequest': {
                'requestId': f"meet-{int(datetime.now().timestamp())}"
            }
        }
    }

    # Create the event
    event = service.events().insert(
        calendarId='primary',
        body=event,
        conferenceDataVersion=1
    ).execute()

    return {
        "success": True,
        "event_id": event['id'],
        "title": event['summary'],
        "date": date,
        "start_time": start_time,
        "duration_minutes": duration_minutes,
        "status": "Confirmed",
        "meet_link": event.get('hangoutLink', '')
    }
```

### Custom Booking System Integration

Example for a REST API booking system:

```python
import httpx

async def book_appointment(self, date: str, time: str, service_type: str,
                          customer_name: str, customer_phone: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{self.api_url}/api/bookings",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "date": date,
                "time": time,
                "service_type": service_type,
                "customer": {
                    "name": customer_name,
                    "phone": customer_phone
                }
            }
        )

        if response.status_code == 201:
            data = response.json()
            return {
                "success": True,
                "booking_id": data["id"],
                "date": data["date"],
                "time": data["time"],
                "service_type": data["service_type"],
                "customer_name": customer_name,
                "status": data["status"]
            }
        else:
            return {"success": False, "error": response.text}
```

## Adding More Functions

To add new backend integrations:

### 1. Create Client Class

```python
class MySystemClient:
    """Client for your custom backend system"""

    def __init__(self):
        self.api_url = os.getenv("MYSYSTEM_URL")
        self.api_key = os.getenv("MYSYSTEM_API_KEY")

    async def do_something(self, param1: str, param2: str) -> dict:
        # Your API call logic here
        pass
```

### 2. Add Function to AssistantFunctions

```python
class AssistantFunctions(llm.FunctionContext):

    @llm.ai_callable(description="Description of what this function does")
    async def my_new_function(
        self,
        param1: Annotated[str, llm.TypeInfo(description="What param1 is for")],
        param2: Annotated[str, llm.TypeInfo(description="What param2 is for")]
    ):
        """Your function implementation"""
        my_system = MySystemClient()
        result = await my_system.do_something(param1, param2)
        return f"Action completed: {result}"
```

### 3. Update Agent Instructions

Update the `VoiceAssistantWithMCP` instructions to mention the new capability:

```python
instructions="""You are a helpful voice assistant with access to:
1. ServiceNow for support tickets
2. Booking system for appointments
3. Calendar for meetings
4. My New System for doing X  # <-- Add this

When users request these actions, use the appropriate function."""
```

## Testing MCP Functions

### Test ServiceNow Ticket Creation

Call and say: "I need to report a network connectivity issue in the office"

Expected flow:
1. Agent asks for more details
2. You provide description
3. Agent calls `create_servicenow_ticket()`
4. Agent confirms with ticket number

### Test Appointment Booking

Call and say: "I want to book a haircut for tomorrow afternoon"

Expected flow:
1. Agent checks availability
2. Agent offers available times
3. You choose a time
4. Agent calls `book_appointment()`
5. Agent confirms with booking ID

### Test Meeting Scheduling

Call and say: "Schedule a team standup meeting for Monday at 9am for 30 minutes"

Expected flow:
1. Agent checks calendar availability
2. Agent calls `schedule_calendar_meeting()`
3. Agent confirms and provides meeting link

## Troubleshooting

### Functions Not Being Called

**Issue**: Agent doesn't call functions even when requested

**Solutions**:
- Ensure `fnc_ctx=AssistantFunctions()` is set in AgentSession
- Check that GPT-4o is being used (not GPT-3.5)
- Review agent instructions to mention the functions
- Check function descriptions are clear

### Backend API Errors

**Issue**: Function calls fail with API errors

**Solutions**:
- Verify credentials in `.env` are correct
- Check API endpoints are reachable
- Review API rate limits
- Add error handling and logging
- Test APIs directly with curl/Postman first

### Slow Response Times

**Issue**: Long delays when calling functions

**Solutions**:
- Optimize backend API performance
- Add caching where appropriate
- Use async/await properly
- Consider timeout limits
- Implement fallback responses

## Security Considerations

### 1. Credential Management

- Never commit `.env` file to version control
- Use environment-specific credentials
- Rotate API keys regularly
- Use OAuth 2.0 where possible

### 2. Input Validation

```python
async def book_appointment(self, date: str, ...):
    # Validate date format
    try:
        datetime.strptime(date, '%Y-%m-%d')
    except ValueError:
        return "Invalid date format"

    # Validate phone number
    if not re.match(r'^\+?[1-9]\d{1,14}$', customer_phone):
        return "Invalid phone number"

    # Proceed with booking...
```

### 3. Rate Limiting

```python
from functools import wraps
import asyncio

def rate_limit(calls_per_minute: int):
    def decorator(func):
        calls = []

        @wraps(func)
        async def wrapper(*args, **kwargs):
            now = datetime.now()
            # Remove old calls
            calls[:] = [c for c in calls if (now - c).seconds < 60]

            if len(calls) >= calls_per_minute:
                return "Rate limit exceeded. Please try again later."

            calls.append(now)
            return await func(*args, **kwargs)

        return wrapper
    return decorator

@rate_limit(calls_per_minute=10)
async def create_ticket(self, ...):
    # Implementation
```

### 4. Audit Logging

```python
import logging

audit_logger = logging.getLogger('audit')

async def book_appointment(self, ...):
    audit_logger.info(f"Booking requested: {customer_name} - {date} {time}")

    result = await booking_system.book_appointment(...)

    audit_logger.info(f"Booking {'successful' if result['success'] else 'failed'}: {result}")

    return result
```

## Production Deployment

### Environment Variables

Use different `.env` files for each environment:

```bash
# Development
.env.development

# Staging
.env.staging

# Production
.env.production
```

Load based on environment:

```python
from dotenv import load_dotenv
import os

env = os.getenv('ENVIRONMENT', 'development')
load_dotenv(f'.env.{env}')
```

### Monitoring

Add monitoring for MCP function calls:

```python
from datetime import datetime

class MonitoredAssistantFunctions(llm.FunctionContext):

    async def _track_call(self, function_name: str, duration: float, success: bool):
        # Send metrics to monitoring system
        # Examples: Datadog, CloudWatch, Prometheus
        pass

    @llm.ai_callable(description="Create ServiceNow ticket")
    async def create_servicenow_ticket(self, ...):
        start_time = datetime.now()
        try:
            result = await servicenow.create_ticket(...)
            duration = (datetime.now() - start_time).total_seconds()
            await self._track_call('create_servicenow_ticket', duration, True)
            return result
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            await self._track_call('create_servicenow_ticket', duration, False)
            logger.error(f"ServiceNow error: {e}")
            return "Failed to create ticket"
```

## Next Steps

1. **Implement Real API Calls**: Replace mock implementations with actual API integrations
2. **Add Error Handling**: Improve error messages and fallback behavior
3. **Enhance Validation**: Add input validation for all function parameters
4. **Add More Functions**: Integrate additional backend systems as needed
5. **Testing**: Create comprehensive test suite for function calling
6. **Monitoring**: Set up logging and metrics for production

## Resources

- LiveKit Agents Function Calling: https://docs.livekit.io/agents/function-calling/
- OpenAI Function Calling: https://platform.openai.com/docs/guides/function-calling
- ServiceNow REST API: https://developer.servicenow.com/dev.do
- Google Calendar API: https://developers.google.com/calendar/api
- Model Context Protocol: https://modelcontextprotocol.io/
