#!/usr/bin/env python3
"""
Create outbound dispatch rule with agent assignment
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
from livekit.protocol.room import RoomConfiguration
from livekit.protocol.agent_dispatch import RoomAgentDispatch

load_dotenv()

OUTBOUND_TRUNK_ID = "ST_txDQCysAYNDh"
AGENT_NAME = "telephony-agent"


async def create_outbound_dispatch():
    """Create outbound dispatch rule with agent assignment"""

    livekit_api = api.LiveKitAPI()

    try:
        # Configure room with agent dispatch
        room_config = RoomConfiguration(
            agents=[
                RoomAgentDispatch(
                    agent_name=AGENT_NAME,
                )
            ]
        )

        request = CreateSIPDispatchRuleRequest(
            rule=SIPDispatchRule(
                dispatch_rule_direct=SIPDispatchRuleDirect(
                    room_name="outbound-call-",
                    pin=""
                )
            ),
            trunk_ids=[OUTBOUND_TRUNK_ID],
            hide_phone_number=False,
            name="Outbound Calls",
            metadata="",
            attributes={},
            room_config=room_config,
        )

        rule = await livekit_api.sip.create_sip_dispatch_rule(request)
        print(f"✅ Outbound dispatch rule created: {rule.sip_dispatch_rule_id}")
        print(f"   Agent assigned: {AGENT_NAME}")
        print(f"   Room pattern: outbound-call-")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await livekit_api.aclose()


if __name__ == "__main__":
    asyncio.run(create_outbound_dispatch())
