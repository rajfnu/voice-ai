#!/usr/bin/env python3
"""
Simple Voice AI Agent Prototype
Demonstrates STT → LLM → TTS pipeline with LiveKit
"""

import asyncio
import logging
import os
from dotenv import load_dotenv
from livekit import agents, rtc
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    WorkerOptions,
    cli,
)
from livekit.plugins import deepgram, openai, cartesia

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def entrypoint(ctx: JobContext):
    """
    Main entrypoint for the voice agent.
    This runs when a participant joins a LiveKit room.
    """
    logger.info(f"Starting voice agent for room: {ctx.room.name}")

    # Connect to the room
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    # Create the voice assistant with STT, LLM, and TTS
    assistant = agents.VoiceAssistant(
        vad=agents.silero.VAD.load(),  # Voice Activity Detection
        stt=deepgram.STT(),  # Speech-to-Text (Deepgram)
        llm=openai.LLM(model="gpt-4o"),  # Large Language Model (OpenAI)
        tts=cartesia.TTS(),  # Text-to-Speech (Cartesia)
        chat_ctx=agents.ChatContext().append(
            role="system",
            text=(
                "You are a friendly voice assistant. "
                "Keep your responses concise and natural. "
                "You're here to help answer questions and have a conversation."
            ),
        ),
    )

    # Start the assistant
    assistant.start(ctx.room)

    # Greet the user when they join
    await asyncio.sleep(1)  # Small delay to ensure audio is ready
    await assistant.say("Hello! I'm your voice assistant. How can I help you today?")

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

    # Start the worker
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
        ),
    )


if __name__ == "__main__":
    main()
