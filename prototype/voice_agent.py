#!/usr/bin/env python3
"""
Simple Voice AI Agent Prototype
Demonstrates STT → LLM → TTS pipeline with LiveKit
Based on official LiveKit Agents documentation
"""

import logging
import os
from dotenv import load_dotenv
from livekit import agents
from livekit.agents import Agent, AgentServer, AgentSession
from livekit.plugins import silero, deepgram, openai, cartesia

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VoiceAssistant(Agent):
    """Custom voice assistant agent"""

    def __init__(self) -> None:
        super().__init__(
            instructions="""You are a friendly voice assistant.
            Keep your responses concise and natural.
            You're here to help answer questions and have a conversation.
            Your responses are to the point, without complex formatting or emojis."""
        )


# Create the agent server
server = AgentServer()


@server.rtc_session()
async def voice_agent(ctx: agents.JobContext):
    """
    Main entrypoint for the voice agent.
    This runs when a participant joins a LiveKit room.
    """
    logger.info(f"Starting voice agent for room: {ctx.room.name}")

    # Create the agent session with STT, LLM, and TTS using direct plugins
    session = AgentSession(
        stt=deepgram.STT(),  # Speech-to-Text (Deepgram) - uses DEEPGRAM_API_KEY
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
    await session.generate_reply(
        instructions="Greet the user and offer your assistance."
    )

    logger.info("Voice assistant is now active and ready")


def main():
    """Run the voice agent worker"""
    logger.info("Starting LiveKit Voice Agent Worker")

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
        logger.error("Please copy .env.example to .env and add your API keys")
        return

    # Start the agent server
    agents.cli.run_app(server)


if __name__ == "__main__":
    main()
