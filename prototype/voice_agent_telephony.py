#!/usr/bin/env python3
"""
Voice AI Agent with Telephony Support
Handles both web clients and phone calls via Twilio
"""

import logging
import os
from dotenv import load_dotenv
from livekit import agents
from livekit.agents import Agent, AgentServer, AgentSession
from livekit.plugins import silero, openai, cartesia

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VoiceAssistant(Agent):
    """Custom voice assistant agent for telephony"""

    def __init__(self) -> None:
        super().__init__(
            instructions="""You are a friendly voice assistant on a phone call.
            Keep your responses very concise and conversational, as if talking to someone on the phone.
            Speak naturally without using any formatting, emojis, or special characters.
            Be helpful and to the point."""
        )


# Create the agent server
server = AgentServer()


# Use explicit agent name for telephony dispatch
@server.rtc_session(agent_name="telephony-agent")
async def voice_agent(ctx: agents.JobContext):
    """
    Main entrypoint for the voice agent.
    This runs when a participant joins a LiveKit room (web or phone call).
    """
    logger.info(f"Starting voice agent for room: {ctx.room.name}")

    # Check if this is a phone call (SIP participant)
    is_phone_call = ctx.room.name.startswith("call-")

    if is_phone_call:
        logger.info("Phone call detected - telephony mode enabled")
    else:
        logger.info("Web client detected - standard mode")

    # Create the agent session with STT, LLM, and TTS using direct plugins
    session = AgentSession(
        stt=cartesia.STT(),  # Speech-to-Text (Cartesia) - uses CARTESIA_API_KEY
        llm=openai.LLM(model="gpt-4o"),  # Large Language Model (OpenAI) - uses OPENAI_API_KEY
        tts=cartesia.TTS(),  # Text-to-Speech (Cartesia) - uses CARTESIA_API_KEY
        vad=silero.VAD.load(),  # Voice Activity Detection
    )

    # Start the session
    await session.start(
        room=ctx.room,
        agent=VoiceAssistant(),
    )

    # Generate initial greeting
    if is_phone_call:
        await session.generate_reply(
            instructions="Greet the caller warmly and ask how you can help them today."
        )
    else:
        await session.generate_reply(
            instructions="Greet the user and offer your assistance."
        )

    logger.info("Voice assistant is now active and ready")


def main():
    """Run the voice agent worker"""
    logger.info("Starting LiveKit Voice Agent Worker (Telephony Mode)")

    # Verify required environment variables
    required_vars = [
        "LIVEKIT_URL",
        "LIVEKIT_API_KEY",
        "LIVEKIT_API_SECRET",
        "OPENAI_API_KEY",
        "CARTESIA_API_KEY",
    ]

    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please copy .env.example to .env and add your API keys")
        return

    # Start the agent server
    agents.cli.run_app(server)


if __name__ == "__main__":
    main()
