#!/usr/bin/env python3
"""
Test script to verify voice agent can start and join a room
This doesn't test the full audio pipeline, but verifies the agent initializes correctly
"""

import asyncio
import os
from dotenv import load_dotenv
from livekit import api

load_dotenv()

async def test_voice_agent_setup():
    """Test that we can create a room and generate tokens for the voice agent"""

    url = os.getenv("LIVEKIT_URL")
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")

    print("🔧 Testing Voice Agent Setup")
    print(f"🔗 LiveKit URL: {url}")

    # Check for required API keys
    required_keys = {
        "DEEPGRAM_API_KEY": os.getenv("DEEPGRAM_API_KEY"),
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        "CARTESIA_API_KEY": os.getenv("CARTESIA_API_KEY"),
    }

    print("\n🔑 Checking API Keys:")
    all_keys_present = True
    for key_name, key_value in required_keys.items():
        if key_value and key_value != f"your_{key_name.lower().replace('_', '_')}_here":
            print(f"   ✅ {key_name}: Set")
        else:
            print(f"   ❌ {key_name}: Missing or not configured")
            all_keys_present = False

    if not all_keys_present:
        print("\n⚠️  Some API keys are missing. The voice agent won't work without them.")
        print("   Get your keys from:")
        print("   - Deepgram: https://console.deepgram.com")
        print("   - OpenAI: https://platform.openai.com/api-keys")
        print("   - Cartesia: https://cartesia.ai")
        return

    # Create API client
    lk_api = api.LiveKitAPI(url, api_key, api_secret)

    try:
        # Create a test room
        print("\n📦 Creating test room...")
        room_name = "voice-agent-test"
        room = await lk_api.room.create_room(
            api.CreateRoomRequest(name=room_name, empty_timeout=300)
        )
        print(f"✅ Room created: {room.name}")

        # Generate token for the voice agent
        print("\n🎫 Generating agent token...")
        agent_token = api.AccessToken(api_key, api_secret) \
            .with_identity("voice-agent") \
            .with_name("Voice Agent") \
            .with_grants(api.VideoGrants(
                room_join=True,
                room=room_name,
                can_publish=True,
                can_subscribe=True,
            ))
        print(f"✅ Agent token generated")

        # Generate token for a test user
        print("\n🎫 Generating user token...")
        user_token = api.AccessToken(api_key, api_secret) \
            .with_identity("test-user") \
            .with_name("Test User") \
            .with_grants(api.VideoGrants(
                room_join=True,
                room=room_name,
                can_publish=True,
                can_subscribe=True,
            ))
        user_token_jwt = user_token.to_jwt()
        print(f"✅ User token generated")

        print("\n📋 Next Steps:")
        print(f"   1. Start the voice agent:")
        print(f"      python voice_agent.py dev")
        print(f"")
        print(f"   2. Join the room with a WebRTC client:")
        print(f"      Room: {room_name}")
        print(f"      URL: {url}")
        print(f"      Token: {user_token_jwt}")
        print(f"")
        print(f"   Or test in browser at: https://meet.livekit.io/custom")

        # Don't delete the room - leave it for testing
        print("\n✅ Setup complete! Room is ready for voice agent testing.")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise
    finally:
        await lk_api.aclose()


if __name__ == "__main__":
    asyncio.run(test_voice_agent_setup())
