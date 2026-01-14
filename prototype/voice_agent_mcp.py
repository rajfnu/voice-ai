#!/usr/bin/env python3
"""
Voice AI Agent with MCP Integration
Handles phone calls with function calling for backend systems:
- ServiceNow (ticket management)
- Booking System (appointments)
- Calendar (meeting scheduling)
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Annotated
from dotenv import load_dotenv
from livekit import agents
from livekit.agents import Agent, AgentServer, AgentSession, llm
from livekit.plugins import silero, deepgram, openai, cartesia

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# MCP SERVER INTEGRATIONS - Backend System Connectors
# ============================================================================

class ServiceNowClient:
    """ServiceNow API client for ticket management"""

    def __init__(self):
        self.instance_url = os.getenv("SERVICENOW_INSTANCE_URL")
        self.username = os.getenv("SERVICENOW_USERNAME")
        self.password = os.getenv("SERVICENOW_PASSWORD")

    async def create_ticket(self, short_description: str, description: str, priority: str = "3") -> dict:
        """
        Create a ServiceNow incident ticket

        Args:
            short_description: Brief summary of the issue
            description: Detailed description
            priority: Priority level (1=Critical, 2=High, 3=Moderate, 4=Low)

        Returns:
            Ticket details including ticket number
        """
        logger.info(f"Creating ServiceNow ticket: {short_description}")

        # TODO: Replace with actual ServiceNow REST API call
        # Example implementation:
        # import requests
        # url = f"{self.instance_url}/api/now/table/incident"
        # headers = {"Content-Type": "application/json", "Accept": "application/json"}
        # data = {
        #     "short_description": short_description,
        #     "description": description,
        #     "priority": priority,
        #     "caller_id": "phone_user"
        # }
        # response = requests.post(url, auth=(self.username, self.password), headers=headers, json=data)
        # result = response.json()

        # Mock response for now
        ticket_number = f"INC{datetime.now().strftime('%Y%m%d%H%M%S')}"
        return {
            "success": True,
            "ticket_number": ticket_number,
            "short_description": short_description,
            "priority": priority,
            "status": "New"
        }


class BookingSystemClient:
    """Booking system API client for appointment scheduling"""

    def __init__(self):
        self.api_url = os.getenv("BOOKING_SYSTEM_URL")
        self.api_key = os.getenv("BOOKING_SYSTEM_API_KEY")

    async def check_availability(self, date: str, service_type: str) -> list:
        """
        Check available appointment slots

        Args:
            date: Date in YYYY-MM-DD format
            service_type: Type of service/appointment

        Returns:
            List of available time slots
        """
        logger.info(f"Checking availability for {service_type} on {date}")

        # TODO: Replace with actual booking system API call
        # Mock response with available slots
        return [
            {"time": "09:00", "available": True},
            {"time": "10:30", "available": True},
            {"time": "14:00", "available": True},
            {"time": "15:30", "available": True}
        ]

    async def book_appointment(self, date: str, time: str, service_type: str,
                              customer_name: str, customer_phone: str) -> dict:
        """
        Book an appointment

        Args:
            date: Date in YYYY-MM-DD format
            time: Time in HH:MM format
            service_type: Type of service
            customer_name: Customer name
            customer_phone: Customer phone number

        Returns:
            Booking confirmation details
        """
        logger.info(f"Booking {service_type} for {customer_name} on {date} at {time}")

        # TODO: Replace with actual booking system API call
        # Example:
        # import requests
        # url = f"{self.api_url}/api/bookings"
        # headers = {"Authorization": f"Bearer {self.api_key}"}
        # data = {
        #     "date": date,
        #     "time": time,
        #     "service_type": service_type,
        #     "customer": {"name": customer_name, "phone": customer_phone}
        # }
        # response = requests.post(url, headers=headers, json=data)
        # return response.json()

        # Mock response
        booking_id = f"BK{datetime.now().strftime('%Y%m%d%H%M%S')}"
        return {
            "success": True,
            "booking_id": booking_id,
            "date": date,
            "time": time,
            "service_type": service_type,
            "customer_name": customer_name,
            "status": "Confirmed"
        }


class CalendarClient:
    """Calendar API client for meeting scheduling (Google Calendar, Outlook, etc.)"""

    def __init__(self):
        self.calendar_type = os.getenv("CALENDAR_TYPE", "google")  # google, outlook, etc.
        self.api_credentials = os.getenv("CALENDAR_API_CREDENTIALS")

    async def check_availability(self, date: str, start_time: str, duration_minutes: int) -> bool:
        """
        Check if a time slot is available

        Args:
            date: Date in YYYY-MM-DD format
            start_time: Start time in HH:MM format
            duration_minutes: Meeting duration

        Returns:
            True if slot is available, False otherwise
        """
        logger.info(f"Checking calendar availability for {date} at {start_time}")

        # TODO: Replace with actual calendar API call
        # For Google Calendar:
        # from google.oauth2.credentials import Credentials
        # from googleapiclient.discovery import build
        # service = build('calendar', 'v3', credentials=creds)
        # events_result = service.events().list(
        #     calendarId='primary',
        #     timeMin=start_datetime,
        #     timeMax=end_datetime,
        #     singleEvents=True
        # ).execute()

        # Mock response
        return True

    async def schedule_meeting(self, title: str, date: str, start_time: str,
                              duration_minutes: int, attendees: list = None) -> dict:
        """
        Schedule a calendar meeting

        Args:
            title: Meeting title
            date: Date in YYYY-MM-DD format
            start_time: Start time in HH:MM format
            duration_minutes: Meeting duration
            attendees: List of attendee email addresses

        Returns:
            Meeting details including event ID and join link
        """
        logger.info(f"Scheduling meeting '{title}' for {date} at {start_time}")

        # TODO: Replace with actual calendar API call
        # For Google Calendar with Google Meet:
        # event = {
        #     'summary': title,
        #     'start': {'dateTime': start_datetime, 'timeZone': 'UTC'},
        #     'end': {'dateTime': end_datetime, 'timeZone': 'UTC'},
        #     'attendees': [{'email': email} for email in attendees],
        #     'conferenceData': {
        #         'createRequest': {'requestId': f"meet-{datetime.now().timestamp()}"}
        #     }
        # }
        # event = service.events().insert(calendarId='primary', body=event,
        #                                 conferenceDataVersion=1).execute()

        # Mock response
        event_id = f"EVT{datetime.now().strftime('%Y%m%d%H%M%S')}"
        return {
            "success": True,
            "event_id": event_id,
            "title": title,
            "date": date,
            "start_time": start_time,
            "duration_minutes": duration_minutes,
            "status": "Confirmed",
            "meet_link": f"https://meet.google.com/mock-{event_id}"
        }


# ============================================================================
# FUNCTION DEFINITIONS FOR LLM FUNCTION CALLING
# ============================================================================

# Initialize backend clients
servicenow = ServiceNowClient()
booking_system = BookingSystemClient()
calendar = CalendarClient()


class AssistantFunctions(llm.FunctionContext):
    """
    Function definitions that the LLM can call during conversation.
    These integrate with MCP servers / backend systems.
    """

    @llm.ai_callable(
        description="Create a ServiceNow incident ticket for technical issues or support requests"
    )
    async def create_servicenow_ticket(
        self,
        short_description: Annotated[str, llm.TypeInfo(description="Brief summary of the issue")],
        description: Annotated[str, llm.TypeInfo(description="Detailed description of the issue")],
        priority: Annotated[str, llm.TypeInfo(description="Priority: 1=Critical, 2=High, 3=Moderate, 4=Low")] = "3"
    ):
        """Create a ServiceNow incident ticket"""
        result = await servicenow.create_ticket(short_description, description, priority)

        if result["success"]:
            return f"Ticket created successfully! Your ticket number is {result['ticket_number']}. " \
                   f"Priority is set to {priority} and status is {result['status']}."
        else:
            return "I encountered an error creating the ticket. Please try again or contact support directly."

    @llm.ai_callable(
        description="Check available appointment slots for a specific date and service"
    )
    async def check_appointment_availability(
        self,
        date: Annotated[str, llm.TypeInfo(description="Date in YYYY-MM-DD format")],
        service_type: Annotated[str, llm.TypeInfo(description="Type of service or appointment needed")]
    ):
        """Check available appointment slots"""
        slots = await booking_system.check_availability(date, service_type)

        if slots:
            times = [slot["time"] for slot in slots if slot["available"]]
            return f"Available times for {service_type} on {date}: {', '.join(times)}"
        else:
            return f"No available slots found for {service_type} on {date}."

    @llm.ai_callable(
        description="Book an appointment for a customer"
    )
    async def book_appointment(
        self,
        date: Annotated[str, llm.TypeInfo(description="Date in YYYY-MM-DD format")],
        time: Annotated[str, llm.TypeInfo(description="Time in HH:MM format")],
        service_type: Annotated[str, llm.TypeInfo(description="Type of service")],
        customer_name: Annotated[str, llm.TypeInfo(description="Customer's name")],
        customer_phone: Annotated[str, llm.TypeInfo(description="Customer's phone number")]
    ):
        """Book an appointment"""
        result = await booking_system.book_appointment(date, time, service_type, customer_name, customer_phone)

        if result["success"]:
            return f"Appointment booked! Your booking ID is {result['booking_id']}. " \
                   f"{service_type} is scheduled for {date} at {time}. Status: {result['status']}."
        else:
            return "I couldn't complete the booking. Please try again."

    @llm.ai_callable(
        description="Schedule a meeting on the calendar with optional attendees"
    )
    async def schedule_calendar_meeting(
        self,
        title: Annotated[str, llm.TypeInfo(description="Meeting title or subject")],
        date: Annotated[str, llm.TypeInfo(description="Date in YYYY-MM-DD format")],
        start_time: Annotated[str, llm.TypeInfo(description="Start time in HH:MM format")],
        duration_minutes: Annotated[int, llm.TypeInfo(description="Meeting duration in minutes")] = 30,
        attendees: Annotated[str, llm.TypeInfo(description="Comma-separated email addresses of attendees")] = ""
    ):
        """Schedule a calendar meeting"""
        # First check availability
        is_available = await calendar.check_availability(date, start_time, duration_minutes)

        if not is_available:
            return f"Sorry, that time slot is not available. Please choose a different time."

        # Parse attendees
        attendee_list = [email.strip() for email in attendees.split(",")] if attendees else []

        # Schedule the meeting
        result = await calendar.schedule_meeting(title, date, start_time, duration_minutes, attendee_list)

        if result["success"]:
            response = f"Meeting scheduled! '{title}' is set for {date} at {start_time} " \
                      f"for {duration_minutes} minutes."
            if result.get("meet_link"):
                response += f" Join link: {result['meet_link']}"
            return response
        else:
            return "I couldn't schedule the meeting. Please try again."


# ============================================================================
# VOICE ASSISTANT WITH MCP INTEGRATION
# ============================================================================

class VoiceAssistantWithMCP(Agent):
    """Voice assistant with backend system integration via MCP/function calling"""

    def __init__(self) -> None:
        super().__init__(
            instructions="""You are a helpful voice assistant on a phone call with access to several backend systems.

            You can help users with:
            1. Creating ServiceNow tickets for technical issues or support requests
            2. Booking appointments for various services
            3. Scheduling calendar meetings

            When users ask to perform these actions:
            - Ask for all necessary information before calling functions
            - Confirm details with the user before booking/creating
            - Use the appropriate function to complete their request
            - Provide clear confirmation after the action is complete

            Keep your responses conversational and concise, as if talking on the phone.
            Always confirm the action was successful and provide any relevant IDs or confirmation numbers."""
        )


# Create the agent server
server = AgentServer()


@server.rtc_session(agent_name="telephony-agent-mcp")
async def voice_agent_mcp(ctx: agents.JobContext):
    """
    Voice agent with MCP integration.
    Handles phone calls with function calling for backend systems.
    """
    logger.info(f"Starting MCP-enabled voice agent for room: {ctx.room.name}")

    # Check if this is a phone call
    is_phone_call = ctx.room.name.startswith("call-")

    if is_phone_call:
        logger.info("Phone call detected - telephony mode with MCP enabled")
    else:
        logger.info("Web client detected - standard mode with MCP enabled")

    # Create the agent session with function calling
    session = AgentSession(
        stt=deepgram.STT(),
        llm=openai.LLM(model="gpt-4o"),
        tts=cartesia.TTS(),
        vad=silero.VAD.load(),
        fnc_ctx=AssistantFunctions(),  # 🔴 This enables MCP/function calling
    )

    # Start the session
    await session.start(
        room=ctx.room,
        agent=VoiceAssistantWithMCP(),
    )

    # Generate initial greeting
    if is_phone_call:
        await session.generate_reply(
            instructions="""Greet the caller warmly and let them know you can help with:
            - Creating support tickets
            - Booking appointments
            - Scheduling meetings
            Ask how you can assist them today."""
        )
    else:
        await session.generate_reply(
            instructions="Greet the user and explain what you can help with."
        )

    logger.info("MCP-enabled voice assistant is now active")


def main():
    """Run the MCP-enabled voice agent worker"""
    logger.info("Starting LiveKit Voice Agent Worker with MCP Integration")

    # Verify required environment variables
    required_vars = [
        "LIVEKIT_URL",
        "LIVEKIT_API_KEY",
        "LIVEKIT_API_SECRET",
        "DEEPGRAM_API_KEY",
        "OPENAI_API_KEY",
        "CARTESIA_API_KEY",
    ]

    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please update your .env file with the required credentials")
        return

    # Optional backend system credentials
    logger.info("Backend system configuration:")
    logger.info(f"  ServiceNow: {'Configured' if os.getenv('SERVICENOW_INSTANCE_URL') else 'Using mock'}")
    logger.info(f"  Booking System: {'Configured' if os.getenv('BOOKING_SYSTEM_URL') else 'Using mock'}")
    logger.info(f"  Calendar: {'Configured' if os.getenv('CALENDAR_API_CREDENTIALS') else 'Using mock'}")

    # Start the agent server
    agents.cli.run_app(server)


if __name__ == "__main__":
    main()
