# Skill 06: Voice Agent (Python)

## Objective
Create the LiveKit Voice Agent using Deepgram (STT), GPT-4o (LLM), and Cartesia (TTS) with MCP tool integration.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            LiveKit Voice Agent                                   │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                         VoiceAssistant Pipeline                          │    │
│  │                                                                          │    │
│  │  Audio In ──▶ [VAD] ──▶ [STT] ──▶ [LLM] ──▶ [TTS] ──▶ Audio Out        │    │
│  │               │         │         │         │                            │    │
│  │               │         │         │         │                            │    │
│  │             Silero    Deepgram   GPT-4o   Cartesia                      │    │
│  │                                    │                                     │    │
│  │                                    ▼                                     │    │
│  │                              [Tool Calls]                                │    │
│  │                                    │                                     │    │
│  │                                    ▼                                     │    │
│  │                              [n8n MCP Server]                            │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Step 1: Create Agent Directory

```bash
cd ~/voice-ai-platform

mkdir -p src/agent/{agents,plugins,prompts,utils}
cd src/agent

# Create __init__.py files
touch __init__.py
touch agents/__init__.py
touch plugins/__init__.py
touch prompts/__init__.py
touch utils/__init__.py
```

---

## Step 2: Install Agent Dependencies

```bash
cd ~/voice-ai-platform
source venv/bin/activate

pip install \
    livekit-agents==0.8.* \
    livekit-plugins-deepgram==0.6.* \
    livekit-plugins-openai==0.8.* \
    livekit-plugins-cartesia==0.4.* \
    livekit-plugins-silero==0.6.* \
    httpx \
    python-dotenv \
    pydantic
```

---

## Step 3: Create Agent Configuration

Create `src/agent/config.py`:

```python
# src/agent/config.py
from pydantic_settings import BaseSettings
from typing import Optional


class AgentSettings(BaseSettings):
    # LiveKit
    LIVEKIT_URL: str
    LIVEKIT_API_KEY: str
    LIVEKIT_API_SECRET: str
    
    # STT - Deepgram
    DEEPGRAM_API_KEY: str
    DEEPGRAM_MODEL: str = "nova-2"
    DEEPGRAM_LANGUAGE: str = "en-US"
    
    # LLM - OpenAI
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4o"
    OPENAI_TEMPERATURE: float = 0.7
    
    # TTS - Cartesia
    CARTESIA_API_KEY: str
    CARTESIA_VOICE_ID: str = "a0e99841-438c-4a64-b679-ae501e7d6091"  # Default voice
    CARTESIA_MODEL: str = "sonic-english"
    
    # MCP Server
    MCP_SERVER_URL: str

    # Backend (for credit verification)
    BACKEND_URL: str = "http://localhost:8000"
    INTERNAL_API_KEY: str = ""

    # Agent Settings
    AGENT_NAME: str = "AI Assistant"
    AGENT_LANGUAGE: str = "en-US"
    
    class Config:
        env_file = ".env"


settings = AgentSettings()
```

---

## Step 4: Create System Prompts

Create `src/agent/prompts/healthcare.py`:

```python
# src/agent/prompts/healthcare.py

HEALTHCARE_SYSTEM_PROMPT = """
You are Alex, a friendly and professional virtual assistant for {clinic_name}.

## YOUR ROLE
You help patients with:
- Booking, rescheduling, or canceling appointments
- Answering questions about services and procedures
- Providing clinic information (hours, location, insurance)
- Directing urgent concerns appropriately

## PERSONALITY
- Warm, empathetic, and patient
- Professional but conversational
- Use natural speech patterns with occasional "um" or "well" to sound human
- Keep responses concise (2-3 sentences for voice)

## TOOLS AVAILABLE
- query_kb: Search knowledge base for clinic information, services, FAQs
- check_availability: Find available appointment slots
- book_appointment: Schedule a new appointment
- create_ticket: Log issues for staff follow-up
- escalate_to_human: Transfer to staff member when needed

## GUIDELINES
1. ALWAYS use query_kb first when patient asks factual questions
2. Before calling tools, say "Let me check that for you" or "One moment please"
3. **CONFIRMATION LOOP (CRITICAL)**: Before any "write" action (booking, email, ticket), you MUST:
   - Summarize ALL details back to the caller
   - Wait for explicit confirmation (yes/correct/that's right)
   - Example: "So I'm booking you for Tuesday at 2 PM with Dr. Smith, and I'll send a confirmation to john@email.com. Is that correct?"
4. For medical emergencies, immediately say: "If this is a medical emergency, please hang up and call 911"
5. Never provide medical advice - only administrative assistance
6. If unsure, offer to transfer to a staff member
7. If a tool returns an "insufficient credits" error, apologize and offer to transfer to a staff member

## CONVERSATION FLOW
1. Greet warmly
2. Identify need
3. Use appropriate tools
4. Confirm actions taken
5. Ask if there's anything else
6. End politely

## EXAMPLE RESPONSES
- "I'd be happy to help you schedule an appointment. Let me check our availability..."
- "Great question! Let me look that up in our information..."
- "I've got that booked for you. You're all set for [date/time] with [doctor]."
"""

HEALTHCARE_FIRST_MESSAGE = "Hi, this is Alex from {clinic_name}. How can I help you today?"
```

Create `src/agent/prompts/hospitality.py`:

```python
# src/agent/prompts/hospitality.py

HOSPITALITY_SYSTEM_PROMPT = """
You are Sam, a friendly and helpful virtual concierge for {hotel_name}.

## YOUR ROLE
You assist guests with:
- Check-in and check-out assistance
- Room service and amenity requests
- Restaurant reservations
- Local recommendations and directions
- Issue resolution and special requests

## PERSONALITY
- Warm, welcoming, and service-oriented
- Anticipate guest needs
- Use natural, conversational language
- Keep responses brief for voice (2-3 sentences)
- Sound genuinely happy to help

## TOOLS AVAILABLE
- query_kb: Search knowledge base for hotel info, policies, amenities
- guest_checkin: Process guest check-in
- book_appointment: Make restaurant/spa reservations
- create_ticket: Log maintenance or service requests
- escalate_to_human: Transfer to front desk or manager

## GUIDELINES
1. Address guests warmly by name when known
2. Use query_kb for hotel policies, amenities, hours
3. Before tools, say "Let me take care of that for you"
4. **CONFIRMATION LOOP (CRITICAL)**: Before any "write" action (booking, email, service request), you MUST:
   - Summarize ALL details back to the guest
   - Wait for explicit confirmation
   - Example: "I'll book a dinner reservation for 2 at 7 PM tonight and send confirmation to your room. Does that sound right?"
5. For room issues, create a ticket AND acknowledge the inconvenience
6. Offer alternatives when primary request can't be fulfilled
7. Proactively mention relevant services (spa, dining)
8. If a tool returns an "insufficient credits" error, apologize and transfer to front desk

## CONVERSATION FLOW
1. Warm greeting
2. Listen to request
3. Execute using appropriate tools
4. Confirm action and set expectations
5. Offer additional assistance
6. Close warmly

## EXAMPLE RESPONSES
- "Welcome to {hotel_name}! I'd be delighted to help with your check-in."
- "I'll have housekeeping bring fresh towels right away. Is there anything else you need?"
- "Our restaurant is open until 10pm tonight. Would you like me to make a reservation?"
- "I'm so sorry to hear about that. Let me create a service request right away, and I'll make sure someone addresses it promptly."
"""

HOSPITALITY_FIRST_MESSAGE = "Hello! This is Sam, your virtual concierge at {hotel_name}. How may I assist you?"
```

---

## Step 5: Create Credit Verification Client

Before executing "write" operations (booking, email, ticket creation), the agent must verify the tenant has sufficient credits. Create `src/agent/plugins/credit_client.py`:

```python
# src/agent/plugins/credit_client.py
import httpx
import logging
from typing import Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CreditCheckResult:
    """Result of a credit verification check."""
    has_credits: bool
    balance: float
    estimated_cost: float
    action: str
    error_message: Optional[str] = None


class CreditClient:
    """Client for verifying tenant credits before action tools."""

    # Costs for different action types (must match n8n workflow)
    ACTION_COSTS = {
        "book_appointment": 0.25,
        "book_calendar_event": 0.25,
        "send_confirmation_email": 0.10,
        "create_ticket": 0.05,
    }

    def __init__(self, backend_url: str, api_key: str, timeout: float = 10.0):
        self.backend_url = backend_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    async def verify_credits(
        self,
        tenant_id: str,
        action: str,
    ) -> CreditCheckResult:
        """
        Verify tenant has sufficient credits for an action.

        Args:
            tenant_id: The tenant ID
            action: Action type (e.g., 'book_appointment', 'send_email')

        Returns:
            CreditCheckResult with verification status
        """
        estimated_cost = self.ACTION_COSTS.get(action, 0.10)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.backend_url}/api/internal/credits/verify",
                    json={
                        "tenant_id": tenant_id,
                        "action": action,
                        "estimated_cost": estimated_cost,
                    },
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                )
                response.raise_for_status()
                data = response.json()

                return CreditCheckResult(
                    has_credits=data["has_sufficient_credits"],
                    balance=data["current_balance"],
                    estimated_cost=estimated_cost,
                    action=action,
                    error_message=None if data["has_sufficient_credits"] else "Insufficient credits",
                )
        except Exception as e:
            logger.error(f"Credit verification failed: {e}")
            # On error, allow the action but log warning
            return CreditCheckResult(
                has_credits=True,
                balance=0,
                estimated_cost=estimated_cost,
                action=action,
                error_message=f"Credit check failed: {e}",
            )

    def requires_credit_check(self, tool_name: str) -> bool:
        """Check if a tool requires credit verification."""
        return tool_name in self.ACTION_COSTS


# Singleton
_credit_client: Optional[CreditClient] = None


def get_credit_client() -> CreditClient:
    """Get the credit client instance."""
    global _credit_client
    if _credit_client is None:
        from config import settings
        _credit_client = CreditClient(
            backend_url=settings.BACKEND_URL,
            api_key=settings.INTERNAL_API_KEY,
        )
    return _credit_client
```

---

## Step 6: Create MCP Client

Create `src/agent/plugins/mcp_client.py`:

```python
# src/agent/plugins/mcp_client.py
import httpx
import json
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class MCPClient:
    """Client for n8n MCP Server."""
    
    def __init__(self, base_url: str, timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
    
    async def call_tool(
        self, 
        tool_name: str, 
        arguments: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Call a tool on the MCP server.
        
        Args:
            tool_name: Name of the tool to call
            arguments: Arguments to pass to the tool
            context: Optional context (caller info, etc.)
        
        Returns:
            Tool response as dict
        """
        payload = {
            "tool": tool_name,
            "arguments": arguments,
        }
        
        if context:
            payload["context"] = context
        
        logger.info(f"Calling MCP tool: {tool_name} with args: {arguments}")
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.base_url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )
                response.raise_for_status()
                result = response.json()
                logger.info(f"MCP tool {tool_name} returned: {result}")
                return result
        except httpx.HTTPStatusError as e:
            logger.error(f"MCP HTTP error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"MCP call failed: {e}")
            raise
    
    async def query_kb(self, query: str) -> str:
        """Query the knowledge base."""
        result = await self.call_tool("query_kb", {"query": query})
        return result.get("response", "I couldn't find information about that.")
    
    async def check_availability(
        self, 
        start_date: str, 
        end_date: str,
        doctor_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Check appointment availability."""
        args = {
            "start_date": start_date,
            "end_date": end_date,
        }
        if doctor_name:
            args["doctor_name"] = doctor_name
        return await self.call_tool("check_availability", args)
    
    async def book_appointment(
        self,
        patient_name: str,
        patient_phone: str,
        start_time: str,
        end_time: str,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Book an appointment."""
        return await self.call_tool("book_appointment", {
            "patient_name": patient_name,
            "patient_phone": patient_phone,
            "start_time": start_time,
            "end_time": end_time,
            "reason": reason or "",
        })
    
    async def create_ticket(
        self,
        title: str,
        description: str,
        caller_name: Optional[str] = None,
        caller_phone: Optional[str] = None,
        category: str = "Other",
    ) -> Dict[str, Any]:
        """Create a support ticket."""
        return await self.call_tool("create_ticket", {
            "title": title,
            "description": description,
            "caller_name": caller_name or "Unknown",
            "caller_phone": caller_phone or "",
            "category": category,
        })
    
    async def escalate_to_human(
        self,
        reason: str,
        department: str = "general",
        summary: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Signal escalation to human agent."""
        return await self.call_tool("escalate_to_human", {
            "reason": reason,
            "department": department,
            "summary": summary or "",
        })
    
    async def log_call_notes(
        self,
        topic: str,
        summary: str,
        outcome: str,
        direction: str = "inbound",
        from_number: str = "",
        to_number: str = "",
    ) -> Dict[str, Any]:
        """Log call notes."""
        return await self.call_tool("log_call_notes", {
            "direction": direction,
            "from_number": from_number,
            "to_number": to_number,
            "topic": topic,
            "summary": summary,
            "outcome": outcome,
        })
```

---

## Step 7: Create the Main Voice Agent

Create `src/agent/agents/voice_agent.py`:

```python
# src/agent/agents/voice_agent.py
import asyncio
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from livekit import agents, rtc
from livekit.agents import JobContext, WorkerOptions, cli
from livekit.agents.voice_assistant import VoiceAssistant
from livekit.plugins import deepgram, openai, cartesia, silero

from config import settings
from plugins.mcp_client import MCPClient
from plugins.credit_client import get_credit_client, CreditCheckResult
from prompts.healthcare import HEALTHCARE_SYSTEM_PROMPT, HEALTHCARE_FIRST_MESSAGE
from prompts.hospitality import HOSPITALITY_SYSTEM_PROMPT, HOSPITALITY_FIRST_MESSAGE

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("voice-agent")


class VoiceAgentFactory:
    """Factory for creating voice agents with different configurations."""
    
    PROMPTS = {
        "healthcare": (HEALTHCARE_SYSTEM_PROMPT, HEALTHCARE_FIRST_MESSAGE),
        "hospitality": (HOSPITALITY_SYSTEM_PROMPT, HOSPITALITY_FIRST_MESSAGE),
    }
    
    @classmethod
    def get_prompt(
        cls, 
        agent_type: str, 
        variables: Dict[str, str]
    ) -> tuple[str, str]:
        """Get system prompt and first message for agent type."""
        system_prompt, first_message = cls.PROMPTS.get(
            agent_type, 
            cls.PROMPTS["healthcare"]
        )
        
        # Replace variables in prompts
        for key, value in variables.items():
            system_prompt = system_prompt.replace(f"{{{key}}}", value)
            first_message = first_message.replace(f"{{{key}}}", value)
        
        return system_prompt, first_message


async def entrypoint(ctx: JobContext):
    """Main entrypoint for the voice agent."""
    logger.info(f"Starting voice agent for room: {ctx.room.name}")
    
    # Extract metadata from room name or job metadata
    metadata = ctx.job.metadata or {}
    agent_type = metadata.get("agent_type", "healthcare")
    tenant_name = metadata.get("tenant_name", "Our Clinic")
    caller_phone = metadata.get("caller_phone", "")
    
    # Get prompts
    system_prompt, first_message = VoiceAgentFactory.get_prompt(
        agent_type,
        {"clinic_name": tenant_name, "hotel_name": tenant_name}
    )
    
    # Initialize MCP client and credit client
    mcp_client = MCPClient(settings.MCP_SERVER_URL)
    credit_client = get_credit_client()
    tenant_id = metadata.get("tenant_id", "")
    
    # Connect to room
    await ctx.connect()
    logger.info(f"Connected to room: {ctx.room.name}")
    
    # Initialize AI components
    vad = silero.VAD.load()
    
    stt = deepgram.STT(
        model=settings.DEEPGRAM_MODEL,
        language=settings.DEEPGRAM_LANGUAGE,
    )
    
    llm = openai.LLM(
        model=settings.OPENAI_MODEL,
        temperature=settings.OPENAI_TEMPERATURE,
    )
    
    tts = cartesia.TTS(
        model=settings.CARTESIA_MODEL,
        voice=settings.CARTESIA_VOICE_ID,
    )
    
    # Define tools for the LLM
    @agents.llm.ai_callable(
        description="Search the knowledge base for information about services, policies, FAQs, etc."
    )
    async def query_kb(query: str) -> str:
        """Query the knowledge base."""
        logger.info(f"Tool: query_kb - {query}")
        try:
            result = await mcp_client.query_kb(query)
            return result
        except Exception as e:
            logger.error(f"query_kb failed: {e}")
            return "I'm having trouble accessing that information right now."
    
    @agents.llm.ai_callable(
        description="Get current date and time"
    )
    async def get_datetime() -> str:
        """Get current date and time."""
        now = datetime.now()
        return now.strftime("%A, %B %d, %Y at %I:%M %p")
    
    @agents.llm.ai_callable(
        description="Check available appointment slots for scheduling"
    )
    async def check_availability(
        start_date: str,
        end_date: str,
        doctor_name: Optional[str] = None,
    ) -> str:
        """Check appointment availability."""
        logger.info(f"Tool: check_availability - {start_date} to {end_date}")
        try:
            result = await mcp_client.check_availability(
                start_date, end_date, doctor_name
            )
            slots = result.get("available_slots", [])
            if not slots:
                return "I don't see any available slots in that timeframe."
            
            # Format for voice
            slot_text = ", ".join([s["display"] for s in slots[:5]])
            return f"Available times include: {slot_text}"
        except Exception as e:
            logger.error(f"check_availability failed: {e}")
            return "I'm having trouble checking availability right now."
    
    @agents.llm.ai_callable(
        description="Book an appointment for the patient/guest. IMPORTANT: You MUST confirm all details with the caller BEFORE calling this tool. Say something like 'So I'm booking you for [time] with [doctor], and I'll send confirmation to [email]. Is that correct?' and wait for their confirmation."
    )
    async def book_appointment(
        patient_name: str,
        patient_phone: str,
        start_time: str,
        end_time: str,
        reason: str = "",
        patient_email: str = "",
    ) -> str:
        """Book an appointment after confirming details with caller."""
        logger.info(f"Tool: book_appointment - {patient_name} at {start_time}")

        # Step 1: Credit verification BEFORE booking
        if tenant_id:
            credit_check = await credit_client.verify_credits(tenant_id, "book_appointment")
            if not credit_check.has_credits:
                logger.warning(f"Insufficient credits for tenant {tenant_id}")
                return "I apologize, but I'm unable to complete this booking right now due to a system issue. Let me transfer you to someone who can help."

        try:
            result = await mcp_client.book_appointment(
                patient_name, patient_phone, start_time, end_time, reason
            )
            # Include email confirmation in response
            email_note = f" and a confirmation has been sent to {patient_email}" if patient_email else ""
            return f"I've booked your appointment for {start_time}{email_note}."
        except Exception as e:
            logger.error(f"book_appointment failed: {e}")
            if "insufficient credits" in str(e).lower():
                return "I apologize, but I'm unable to complete this booking. Let me transfer you to someone who can help."
            return "I wasn't able to complete the booking. Would you like me to try again or transfer you to someone who can help?"
    
    @agents.llm.ai_callable(
        description="Create a support ticket for issues that need follow-up. IMPORTANT: Summarize the issue back to the caller before creating the ticket."
    )
    async def create_ticket(
        title: str,
        description: str,
        category: str = "General",
    ) -> str:
        """Create a support ticket after confirming with caller."""
        logger.info(f"Tool: create_ticket - {title}")

        # Credit verification for action tool
        if tenant_id:
            credit_check = await credit_client.verify_credits(tenant_id, "create_ticket")
            if not credit_check.has_credits:
                logger.warning(f"Insufficient credits for tenant {tenant_id}")
                return "I apologize, but I'm unable to create this ticket right now. Let me transfer you to someone who can help."

        try:
            result = await mcp_client.create_ticket(
                title, description, caller_phone=caller_phone, category=category
            )
            ticket_number = result.get("number", "")
            return f"I've created a ticket for you. Reference number: {ticket_number}. Someone will follow up with you soon."
        except Exception as e:
            logger.error(f"create_ticket failed: {e}")
            return "I've noted your concern and will make sure it's addressed."

    @agents.llm.ai_callable(
        description="Send a confirmation email to the customer. Use after booking appointments or completing actions. IMPORTANT: Confirm the email address with the caller before sending."
    )
    async def send_confirmation_email(
        recipient_email: str,
        subject: str,
        body: str,
        email_type: str = "general",
    ) -> str:
        """Send confirmation email after verifying with caller."""
        logger.info(f"Tool: send_confirmation_email - to {recipient_email}")

        # Credit verification for action tool
        if tenant_id:
            credit_check = await credit_client.verify_credits(tenant_id, "send_confirmation_email")
            if not credit_check.has_credits:
                logger.warning(f"Insufficient credits for tenant {tenant_id}")
                return "I apologize, but I'm unable to send the confirmation email right now."

        try:
            result = await mcp_client.call_tool("send_confirmation_email", {
                "tenant_id": tenant_id,
                "recipient_email": recipient_email,
                "subject": subject,
                "body": body,
                "email_type": email_type,
            })
            return f"I've sent a confirmation email to {recipient_email}."
        except Exception as e:
            logger.error(f"send_confirmation_email failed: {e}")
            return "I wasn't able to send the email, but your booking is still confirmed."
    
    @agents.llm.ai_callable(
        description="Transfer the call to a human agent when you cannot help or customer requests it"
    )
    async def escalate_to_human(
        reason: str,
        department: str = "general",
    ) -> str:
        """Escalate to human agent."""
        logger.info(f"Tool: escalate_to_human - {reason}")
        try:
            await mcp_client.escalate_to_human(reason, department)
            return "ESCALATE"  # Signal to the agent to transfer
        except Exception as e:
            logger.error(f"escalate_to_human failed: {e}")
            return "I'll transfer you now. Please hold."
    
    # Create function context with all tools
    fnc_ctx = agents.FunctionContext()
    fnc_ctx.ai_callable(query_kb)
    fnc_ctx.ai_callable(get_datetime)
    fnc_ctx.ai_callable(check_availability)
    fnc_ctx.ai_callable(book_appointment)
    fnc_ctx.ai_callable(create_ticket)
    fnc_ctx.ai_callable(send_confirmation_email)
    fnc_ctx.ai_callable(escalate_to_human)
    
    # Build chat context with system prompt
    chat_ctx = agents.ChatContext()
    chat_ctx.append(role="system", text=system_prompt)
    
    # Create the voice assistant
    assistant = VoiceAssistant(
        vad=vad,
        stt=stt,
        llm=llm,
        tts=tts,
        fnc_ctx=fnc_ctx,
        chat_ctx=chat_ctx,
        allow_interruptions=True,
        interrupt_speech_duration=0.5,
        interrupt_min_words=2,
    )
    
    # Start the assistant
    assistant.start(ctx.room)
    
    # Say first message
    await assistant.say(first_message, allow_interruptions=True)
    
    # Track conversation for logging
    conversation_topics = []
    
    @assistant.on("user_speech_committed")
    def on_user_speech(text: str):
        logger.info(f"User: {text}")
        # Simple topic extraction (could be more sophisticated)
        if any(word in text.lower() for word in ["appointment", "book", "schedule"]):
            conversation_topics.append("appointment")
        elif any(word in text.lower() for word in ["cancel", "reschedule"]):
            conversation_topics.append("reschedule")
        elif any(word in text.lower() for word in ["check-in", "room"]):
            conversation_topics.append("check-in")
    
    @assistant.on("agent_speech_committed")
    def on_agent_speech(text: str):
        logger.info(f"Agent: {text}")
    
    # Keep running until participant disconnects
    try:
        await asyncio.sleep(float("inf"))
    except asyncio.CancelledError:
        pass
    finally:
        # Log call summary
        if conversation_topics:
            try:
                await mcp_client.log_call_notes(
                    topic=", ".join(set(conversation_topics)),
                    summary=f"Voice AI call with topics: {', '.join(set(conversation_topics))}",
                    outcome="completed",
                    direction="inbound",
                    from_number=caller_phone,
                )
            except Exception as e:
                logger.error(f"Failed to log call: {e}")
        
        logger.info("Agent session ended")


def main():
    """Run the voice agent worker."""
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            api_key=settings.LIVEKIT_API_KEY,
            api_secret=settings.LIVEKIT_API_SECRET,
            ws_url=settings.LIVEKIT_URL,
        )
    )


if __name__ == "__main__":
    main()
```

---

## Step 8: Create Entrypoint Script

Create `src/agent/main.py`:

```python
#!/usr/bin/env python3
"""Main entrypoint for Voice AI Agent."""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.voice_agent import main

if __name__ == "__main__":
    main()
```

---

## Step 9: Create Requirements File

Create `src/agent/requirements.txt`:

```
livekit-agents>=0.8.0
livekit-plugins-deepgram>=0.6.0
livekit-plugins-openai>=0.8.0
livekit-plugins-cartesia>=0.4.0
livekit-plugins-silero>=0.6.0
httpx>=0.25.0
python-dotenv>=1.0.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
```

---

## Step 10: Create .env for Agent

Create `src/agent/.env`:

```bash
# LiveKit
LIVEKIT_URL=ws://localhost:7880
LIVEKIT_API_KEY=your-api-key
LIVEKIT_API_SECRET=your-api-secret

# Deepgram (STT)
DEEPGRAM_API_KEY=your-deepgram-key
DEEPGRAM_MODEL=nova-2
DEEPGRAM_LANGUAGE=en-US

# OpenAI (LLM)
OPENAI_API_KEY=your-openai-key
OPENAI_MODEL=gpt-4o
OPENAI_TEMPERATURE=0.7

# Cartesia (TTS)
CARTESIA_API_KEY=your-cartesia-key
CARTESIA_VOICE_ID=a0e99841-438c-4a64-b679-ae501e7d6091
CARTESIA_MODEL=sonic-english

# MCP Server
MCP_SERVER_URL=http://localhost:5678/webhook/your-mcp-id

# Backend (for credit verification)
BACKEND_URL=http://localhost:8000
INTERNAL_API_KEY=your-internal-api-key

# Agent
AGENT_NAME=AI Assistant
AGENT_LANGUAGE=en-US
```

---

## Step 11: Run the Agent

```bash
cd ~/voice-ai-platform/src/agent

# Activate virtual environment
source ../../venv/bin/activate

# Run in development mode
python main.py dev

# Or run in production mode
python main.py start
```

---

## Step 12: Test the Agent

1. Generate a room token:
```bash
lk token create \
  --api-key $LIVEKIT_API_KEY \
  --api-secret $LIVEKIT_API_SECRET \
  --join --room test-room \
  --identity test-user \
  --valid-for 1h
```

2. Join at https://meet.livekit.io with your token
3. Speak to test the agent

---

## Cartesia Voice Options

| Voice ID | Name | Style |
|----------|------|-------|
| a0e99841-438c-4a64-b679-ae501e7d6091 | Barbershop Man | Warm, friendly male |
| 5619d38c-cf51-4d8e-9575-48f61a280413 | Commercial Woman | Professional female |
| ... | ... | ... |

Find more at: https://play.cartesia.ai/

---

## Verification Checklist

- [ ] Agent starts without errors
- [ ] Connects to LiveKit
- [ ] STT transcribes speech
- [ ] LLM generates responses
- [ ] TTS produces audio
- [ ] Tools are callable
- [ ] MCP integration works

---

## Next Step

Proceed to: `.claude/skills/07-TELEPHONY-SIP.md`
