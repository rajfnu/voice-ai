#!/usr/bin/env python3
"""
Simple LiveKit prototype test
Tests basic connection and room creation
"""

import asyncio
import os
from dotenv import load_dotenv
from livekit import api

load_dotenv()

async def test_livekit():
    """Test LiveKit server connection and room creation"""

    # Get credentials from environment
    url = os.getenv("LIVEKIT_URL")
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")

    print(f"🔗 Connecting to LiveKit at: {url}")
    print(f"🔑 Using API Key: {api_key}")

    # Create API client
    lk_api = api.LiveKitAPI(url, api_key, api_secret)

    try:
        # Test 1: Create a room
        print("\n📦 Test 1: Creating a room...")
        room_name = "test-room-001"
        room = await lk_api.room.create_room(
            api.CreateRoomRequest(name=room_name)
        )
        print(f"✅ Room created: {room.name} (SID: {room.sid})")

        # Test 2: List rooms
        print("\n📋 Test 2: Listing all rooms...")
        rooms = await lk_api.room.list_rooms(api.ListRoomsRequest())
        print(f"✅ Found {len(rooms.rooms)} room(s):")
        for r in rooms.rooms:
            print(f"   - {r.name} (participants: {r.num_participants})")

        # Test 3: Generate access token
        print("\n🎫 Test 3: Generating access token...")
        token = api.AccessToken(api_key, api_secret) \
            .with_identity("test-user") \
            .with_name("Test User") \
            .with_grants(api.VideoGrants(
                room_join=True,
                room=room_name,
            ))

        access_token = token.to_jwt()
        print(f"✅ Token generated (length: {len(access_token)})")
        print(f"   Token: {access_token[:50]}...")

        # Test 4: Get room info
        print("\n📊 Test 4: Getting room details...")
        room_info = await lk_api.room.list_rooms(
            api.ListRoomsRequest(names=[room_name])
        )
        if room_info.rooms:
            r = room_info.rooms[0]
            print(f"✅ Room details:")
            print(f"   Name: {r.name}")
            print(f"   SID: {r.sid}")
            print(f"   Created: {r.creation_time}")
            print(f"   Participants: {r.num_participants}")

        # Test 5: Clean up - delete room
        print("\n🧹 Test 5: Cleaning up...")
        await lk_api.room.delete_room(api.DeleteRoomRequest(room=room_name))
        print(f"✅ Room deleted: {room_name}")

        print("\n🎉 All tests passed! LiveKit is working correctly.")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise
    finally:
        await lk_api.aclose()

if __name__ == "__main__":
    asyncio.run(test_livekit())
