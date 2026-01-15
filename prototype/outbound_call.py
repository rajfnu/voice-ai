#!/usr/bin/env python3
"""
Outbound Call Script (LiveKit API)
Initiates outbound phone calls using LiveKit SIP and connects them to voice agent
"""

import os
import sys
import asyncio
from dotenv import load_dotenv
from livekit import api
from livekit.protocol.sip import CreateSIPParticipantRequest
from livekit.protocol.agent_dispatch import CreateAgentDispatchRequest, RoomAgentDispatch

# Load environment variables
load_dotenv()

# Outbound trunk ID (created with lk sip outbound create)
OUTBOUND_TRUNK_ID = "ST_txDQCysAYNDh"


async def make_outbound_call(to_number: str, room_name: str = None):
    """
    Initiate an outbound call via LiveKit SIP

    Args:
        to_number: Phone number to call (E.164 format, e.g., +61410241020)
        room_name: Name of the room to connect the call to (auto-generated if not provided)
    """
    # Get LiveKit credentials
    livekit_url = os.getenv('LIVEKIT_URL')
    livekit_api_key = os.getenv('LIVEKIT_API_KEY')
    livekit_api_secret = os.getenv('LIVEKIT_API_SECRET')

    if not all([livekit_url, livekit_api_key, livekit_api_secret]):
        print("ERROR: Missing LiveKit credentials")
        print("Please set these environment variables in .env:")
        print("  LIVEKIT_URL")
        print("  LIVEKIT_API_KEY")
        print("  LIVEKIT_API_SECRET")
        sys.exit(1)

    # Generate room name if not provided
    if not room_name:
        import time
        room_name = f"call-outbound-{int(time.time())}"

    print(f"Initiating outbound call...")
    print(f"  To:   {to_number}")
    print(f"  Room: {room_name}")
    print(f"  Trunk: {OUTBOUND_TRUNK_ID}")

    # Initialize LiveKit API
    livekit_api = api.LiveKitAPI()

    try:
        # Create SIP participant request
        request = CreateSIPParticipantRequest(
            sip_trunk_id=OUTBOUND_TRUNK_ID,
            sip_call_to=to_number,
            room_name=room_name,
            participant_identity="outbound-caller",
            participant_name=f"Outbound Call to {to_number}",
            krisp_enabled=True,  # Enable noise cancellation
            wait_until_answered=True  # Wait until call is answered
        )

        # Create the SIP participant (initiates the call)
        participant = await livekit_api.sip.create_sip_participant(request)

        print(f"\n✅ Call connected successfully!")
        print(f"  Participant SID: {participant.participant_id}")
        print(f"  Room: {participant.room_name}")

        # Manually dispatch an agent to the room
        print(f"\nDispatching agent to room...")
        agent_dispatch_request = CreateAgentDispatchRequest(
            room=room_name,
            agent_name="telephony-agent"
        )
        dispatch = await livekit_api.agent_dispatch.create_dispatch(agent_dispatch_request)
        print(f"  Agent dispatch ID: {dispatch.id}")

        print(f"\nThe voice agent is now active in the call.")
        print(f"Call status can be monitored via participant attributes.")

        return participant

    except Exception as e:
        print(f"\n❌ Error initiating call: {e}")

        # Extract SIP error details if available
        if hasattr(e, 'metadata'):
            sip_status_code = e.metadata.get('sip_status_code')
            sip_status = e.metadata.get('sip_status')
            if sip_status_code:
                print(f"  SIP Error Code: {sip_status_code}")
            if sip_status:
                print(f"  SIP Error: {sip_status}")

        sys.exit(1)

    finally:
        await livekit_api.aclose()


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python outbound_call.py <phone_number> [room_name]")
        print("\nExample:")
        print("  python outbound_call.py +61410241020")
        print("  python outbound_call.py +61410241020 my-custom-room")
        print("\nNote: Phone number must be in E.164 format (+country_code + number)")
        sys.exit(1)

    to_number = sys.argv[1]
    room_name = sys.argv[2] if len(sys.argv) > 2 else None

    # Validate phone number format
    if not to_number.startswith('+'):
        print("ERROR: Phone number must be in E.164 format (starting with +)")
        print("Example: +61410241020")
        sys.exit(1)

    # Run the async function
    asyncio.run(make_outbound_call(to_number, room_name))


if __name__ == "__main__":
    main()
