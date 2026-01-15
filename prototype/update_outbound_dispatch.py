#!/usr/bin/env python3
"""
Update outbound dispatch rule with agent assignment
"""
import os
import asyncio
from dotenv import load_dotenv
from livekit import api
from livekit.protocol.sip import (
    UpdateSIPDispatchRuleRequest,
    SIPDispatchRuleDirect,
    SIPDispatchRule,
)
from livekit.protocol.room import RoomConfiguration
from livekit.protocol.agent_dispatch import RoomAgentDispatch

load_dotenv()

DISPATCH_RULE_ID = "SDR_CvZuE8nYJFTF"
AGENT_NAME = "telephony-agent"


async def update_dispatch_rule():
    """Update dispatch rule with agent assignment"""

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

        # Update the dispatch rule
        request = UpdateSIPDispatchRuleRequest(
            sip_dispatch_rule_id=DISPATCH_RULE_ID,
            room_config=room_config,
        )

        rule = await livekit_api.sip.update_dispatch_rule(request)
        print(f"✅ Outbound dispatch rule updated: {rule.sip_dispatch_rule_id}")
        print(f"   Agent assigned: {AGENT_NAME}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await livekit_api.aclose()


if __name__ == "__main__":
    asyncio.run(update_dispatch_rule())
