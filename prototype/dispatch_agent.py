#!/usr/bin/env python3
"""
Manually dispatch an agent to a room
"""

import asyncio
import os
from dotenv import load_dotenv
from livekit import api

load_dotenv()

async def dispatch_agent():
    """Dispatch an agent to the room"""

    url = os.getenv("LIVEKIT_URL")
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")

    room_name = "voice-agent-test"

    print(f"🚀 Dispatching agent to room: {room_name}")

    lk_api = api.LiveKitAPI(url, api_key, api_secret)

    try:
        # Create agent dispatch
        response = await lk_api.agent_dispatch.create_dispatch(
            api.CreateAgentDispatchRequest(
                room=room_name,
            )
        )
        print(f"✅ Agent dispatch created!")
        print(f"   Dispatch ID: {response.dispatch_id}")
        print(f"   Agent Name: {response.agent_name}")

    except Exception as e:
        print(f"❌ Error dispatching agent: {e}")
        print("\nNote: Manual agent dispatch requires LiveKit Server v1.5.0+")
        print("For local testing, the agent should auto-join when configured correctly.")
    finally:
        await lk_api.aclose()

if __name__ == "__main__":
    asyncio.run(dispatch_agent())
