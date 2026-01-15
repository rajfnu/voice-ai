#!/usr/bin/env python3
"""
Create SIP Dispatch Rules with Agent Assignment
"""
import os
import asyncio
from dotenv import load_dotenv
from livekit import api
from livekit.protocol.sip import (
    CreateSIPDispatchRuleRequest,
    SIPDispatchRuleDirect,
    SIPDispatchRule,
)
from livekit.protocol.room import RoomConfiguration, RoomAgent
from livekit.protocol.agent_dispatch import RoomAgentDispatch

load_dotenv()

# Trunk IDs
INBOUND_TRUNK_ID = "ST_N8mmUzK2obs2"
OUTBOUND_TRUNK_ID = "ST_txDQCysAYNDh"
AGENT_NAME = "telephony-agent"


async def create_dispatch_rules():
    """Create SIP dispatch rules with agent assignment"""

    livekit_api = api.LiveKitAPI()

    try:
        # Create inbound dispatch rule with agent assignment
        print("Creating inbound dispatch rule...")

        # Configure room with agent dispatch
        room_config = RoomConfiguration(
            agents=[
                RoomAgentDispatch(
                    agent_name=AGENT_NAME,
                )
            ]
        )

        inbound_request = CreateSIPDispatchRuleRequest(
            rule=SIPDispatchRule(
                dispatch_rule_direct=SIPDispatchRuleDirect(
                    room_name="call-_<caller>_<random>",
                    pin=""
                )
            ),
            trunk_ids=[INBOUND_TRUNK_ID],
            hide_phone_number=False,
            name="Inbound Calls",
            metadata="",
            attributes={},
            room_config=room_config,
        )

        inbound_rule = await livekit_api.sip.create_sip_dispatch_rule(inbound_request)
        print(f"✅ Inbound rule created: {inbound_rule.sip_dispatch_rule_id}")
        print(f"   Agent assigned: {AGENT_NAME}")

        # Create outbound dispatch rule with agent assignment
        print("\nCreating outbound dispatch rule...")

        # Configure room with agent dispatch (same config)
        outbound_room_config = RoomConfiguration(
            agents=[
                RoomAgentDispatch(
                    agent_name=AGENT_NAME,
                )
            ]
        )

        outbound_request = CreateSIPDispatchRuleRequest(
            rule=SIPDispatchRule(
                dispatch_rule_direct=SIPDispatchRuleDirect(
                    room_name="outbound-call-",  # Match the prefix used in outbound_call.py
                    pin=""
                )
            ),
            trunk_ids=[OUTBOUND_TRUNK_ID],
            hide_phone_number=False,
            name="Outbound Calls",
            metadata="",
            attributes={},
            room_config=outbound_room_config,
        )

        outbound_rule = await livekit_api.sip.create_sip_dispatch_rule(outbound_request)
        print(f"✅ Outbound rule created: {outbound_rule.sip_dispatch_rule_id}")
        print(f"   Agent assigned: {AGENT_NAME}")

        print("\n✅ All dispatch rules configured with agent assignment!")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await livekit_api.aclose()


if __name__ == "__main__":
    asyncio.run(create_dispatch_rules())
