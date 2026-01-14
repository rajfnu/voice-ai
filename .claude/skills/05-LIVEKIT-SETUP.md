# Skill 05: LiveKit Setup (Voice Runtime)

## Objective
Set up LiveKit server and SIP infrastructure for real-time voice communication.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            LiveKit Infrastructure                                │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                         LiveKit Server                                   │    │
│  │                                                                          │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                   │    │
│  │  │ WebRTC SFU   │  │ Room Manager │  │ Token Auth   │                   │    │
│  │  │              │  │              │  │              │                   │    │
│  │  │ - Media      │  │ - Rooms      │  │ - API Key    │                   │    │
│  │  │ - Tracks     │  │ - Partici-   │  │ - API Secret │                   │    │
│  │  │ - Routing    │  │   pants      │  │ - JWT Tokens │                   │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘                   │    │
│  │                                                                          │    │
│  │  Ports: 7880 (HTTP/WS), 7881 (TCP), 7882 (UDP)                          │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                         LiveKit SIP Server                               │    │
│  │                                                                          │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                   │    │
│  │  │ SIP Endpoint │  │ SIP Trunks   │  │ Dispatch     │                   │    │
│  │  │              │  │              │  │ Rules        │                   │    │
│  │  │ Port: 5060   │  │ - Telnyx     │  │              │                   │    │
│  │  │ (UDP/TCP)    │  │ - Twilio     │  │ - Inbound    │                   │    │
│  │  │              │  │              │  │ - Outbound   │                   │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘                   │    │
│  │                                                                          │    │
│  │  Ports: 5060 (SIP), 10000-60000 (RTP/Media)                             │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Option A: LiveKit Cloud (Recommended for Starting)

### A.1 Sign Up

1. Go to https://cloud.livekit.io
2. Create a free account
3. Create a new project

### A.2 Get Credentials

From your LiveKit Cloud dashboard:

```bash
# Note these values:
LIVEKIT_URL=wss://your-project-xxxxx.livekit.cloud
LIVEKIT_API_KEY=APIxxxxxxxx
LIVEKIT_API_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### A.3 Update .env

```bash
# Add to your .env file
LIVEKIT_URL=wss://your-project-xxxxx.livekit.cloud
LIVEKIT_API_KEY=APIxxxxxxxx
LIVEKIT_API_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

---

## Option B: Self-Hosted LiveKit (Production)

### B.1 Generate API Credentials

```bash
# Generate secure credentials
LIVEKIT_API_KEY=$(openssl rand -hex 12)
LIVEKIT_API_SECRET=$(openssl rand -hex 32)

echo "LIVEKIT_API_KEY=${LIVEKIT_API_KEY}"
echo "LIVEKIT_API_SECRET=${LIVEKIT_API_SECRET}"
```

### B.2 Create LiveKit Configuration

```bash
cd ~/voice-ai-platform

mkdir -p configs/livekit

cat > configs/livekit/livekit.yaml << 'EOF'
# LiveKit Server Configuration
port: 7880
rtc:
  tcp_port: 7881
  udp_port: 7882
  use_external_ip: true
  
keys:
  # Replace with your generated keys
  APIxxxxxxxx: your-api-secret-here

redis:
  address: redis:6379
  
logging:
  level: info
  json: false
  
room:
  # Room settings
  empty_timeout: 300
  max_participants: 50
  
turn:
  enabled: true
  domain: turn.yourdomain.com
  tls_port: 5349
  udp_port: 3478
EOF
```

### B.3 Create Docker Compose

```bash
cat > docker-compose.livekit.yml << 'EOF'
version: '3.8'
services:
  livekit:
    image: livekit/livekit-server:latest
    container_name: voice-ai-livekit
    ports:
      - "7880:7880"
      - "7881:7881"
      - "7882:7882/udp"
    command: --config /etc/livekit.yaml
    volumes:
      - ./configs/livekit/livekit.yaml:/etc/livekit.yaml
    depends_on:
      - redis
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    container_name: voice-ai-livekit-redis
    volumes:
      - livekit_redis:/data
    restart: unless-stopped

  # LiveKit SIP Server (for phone calls)
  livekit-sip:
    image: livekit/sip:latest
    container_name: voice-ai-livekit-sip
    ports:
      - "5060:5060/udp"
      - "5060:5060/tcp"
    environment:
      - LIVEKIT_URL=ws://livekit:7880
      - LIVEKIT_API_KEY=${LIVEKIT_API_KEY}
      - LIVEKIT_API_SECRET=${LIVEKIT_API_SECRET}
      - SIP_PORT=5060
    depends_on:
      - livekit
    restart: unless-stopped

volumes:
  livekit_redis:
EOF
```

### B.4 Start LiveKit

```bash
# Update livekit.yaml with your actual keys first!

# Start services
docker compose -f docker-compose.livekit.yml up -d

# Check logs
docker compose -f docker-compose.livekit.yml logs -f livekit
```

### B.5 Verify LiveKit is Running

```bash
# Check health
curl http://localhost:7880

# Should return something like:
# {"video":true,"audio":true}
```

---

## Step 2: Install LiveKit CLI

```bash
# Mac
brew install livekit-cli

# Or via Go
go install github.com/livekit/livekit-cli/cmd/lk@latest

# Verify
lk --version
```

---

## Step 3: Configure CLI

```bash
# Set up CLI with your credentials
lk project add \
  --api-key ${LIVEKIT_API_KEY} \
  --api-secret ${LIVEKIT_API_SECRET} \
  --url ${LIVEKIT_URL} \
  --name voice-ai-local
```

---

## Step 4: Test Token Generation

```bash
# Generate a test token
lk token create \
  --api-key ${LIVEKIT_API_KEY} \
  --api-secret ${LIVEKIT_API_SECRET} \
  --join \
  --room test-room \
  --identity test-user \
  --valid-for 24h

# Copy the token for testing
```

---

## Step 5: Test with LiveKit Meet

1. Go to https://meet.livekit.io
2. Enter your LiveKit URL
3. Paste the token you generated
4. Join the room and test audio/video

---

## Step 6: Create Token Service

Create `services/livekit_service.py`:

```python
# src/backend/app/services/livekit_service.py
from livekit import api
from typing import Optional
from datetime import timedelta

from app.core.config import settings


class LiveKitService:
    """Service for LiveKit operations."""
    
    def __init__(self):
        self.api_key = settings.LIVEKIT_API_KEY
        self.api_secret = settings.LIVEKIT_API_SECRET
        self.url = settings.LIVEKIT_URL
    
    def create_token(
        self,
        room_name: str,
        participant_identity: str,
        participant_name: Optional[str] = None,
        ttl: timedelta = timedelta(hours=1),
        can_publish: bool = True,
        can_subscribe: bool = True,
        can_publish_data: bool = True,
    ) -> str:
        """
        Create a LiveKit access token.
        
        Args:
            room_name: Name of the room to join
            participant_identity: Unique identifier for the participant
            participant_name: Display name for the participant
            ttl: Token validity duration
            can_publish: Whether participant can publish media
            can_subscribe: Whether participant can subscribe to media
            can_publish_data: Whether participant can publish data messages
        
        Returns:
            JWT access token
        """
        token = api.AccessToken(self.api_key, self.api_secret)
        token.with_identity(participant_identity)
        
        if participant_name:
            token.with_name(participant_name)
        
        token.with_ttl(ttl)
        
        grant = api.VideoGrants(
            room_join=True,
            room=room_name,
            can_publish=can_publish,
            can_subscribe=can_subscribe,
            can_publish_data=can_publish_data,
        )
        token.with_grants(grant)
        
        return token.to_jwt()
    
    def create_agent_token(
        self,
        room_name: str,
        agent_name: str = "voice-agent",
    ) -> str:
        """Create token for voice agent."""
        return self.create_token(
            room_name=room_name,
            participant_identity=f"agent-{agent_name}",
            participant_name=agent_name,
            ttl=timedelta(hours=24),
            can_publish=True,
            can_subscribe=True,
            can_publish_data=True,
        )
    
    async def create_room(self, room_name: str) -> dict:
        """Create a new LiveKit room."""
        lk_api = api.LiveKitAPI(
            url=self.url,
            api_key=self.api_key,
            api_secret=self.api_secret,
        )
        
        room = await lk_api.room.create_room(
            api.CreateRoomRequest(name=room_name)
        )
        
        return {
            "name": room.name,
            "sid": room.sid,
            "creation_time": room.creation_time,
        }
    
    async def list_rooms(self) -> list:
        """List all active rooms."""
        lk_api = api.LiveKitAPI(
            url=self.url,
            api_key=self.api_key,
            api_secret=self.api_secret,
        )
        
        response = await lk_api.room.list_rooms(api.ListRoomsRequest())
        
        return [
            {
                "name": room.name,
                "sid": room.sid,
                "num_participants": room.num_participants,
            }
            for room in response.rooms
        ]
    
    async def delete_room(self, room_name: str) -> bool:
        """Delete a room."""
        lk_api = api.LiveKitAPI(
            url=self.url,
            api_key=self.api_key,
            api_secret=self.api_secret,
        )
        
        await lk_api.room.delete_room(
            api.DeleteRoomRequest(room=room_name)
        )
        return True


# Singleton
livekit_service = LiveKitService()
```

---

## Step 7: Create LiveKit API Routes

Create `api/routes/livekit.py`:

```python
# src/backend/app/api/routes/livekit.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import timedelta

from app.api.deps import get_current_active_user, CurrentUser
from app.services.livekit_service import livekit_service

router = APIRouter(prefix="/livekit", tags=["LiveKit"])


class TokenRequest(BaseModel):
    room_name: str
    participant_name: Optional[str] = None


class TokenResponse(BaseModel):
    token: str
    room_name: str
    url: str


@router.post("/token", response_model=TokenResponse)
async def get_room_token(
    request: TokenRequest,
    current_user: CurrentUser = Depends(get_current_active_user),
):
    """Get a token to join a LiveKit room."""
    token = livekit_service.create_token(
        room_name=request.room_name,
        participant_identity=str(current_user.user.id),
        participant_name=request.participant_name or current_user.user.full_name,
        ttl=timedelta(hours=1),
    )
    
    return TokenResponse(
        token=token,
        room_name=request.room_name,
        url=livekit_service.url,
    )


@router.get("/rooms")
async def list_rooms(
    current_user: CurrentUser = Depends(get_current_active_user),
):
    """List all active LiveKit rooms."""
    current_user.require_permission("calls:read")
    return await livekit_service.list_rooms()


@router.post("/rooms/{room_name}")
async def create_room(
    room_name: str,
    current_user: CurrentUser = Depends(get_current_active_user),
):
    """Create a new LiveKit room."""
    return await livekit_service.create_room(room_name)


@router.delete("/rooms/{room_name}")
async def delete_room(
    room_name: str,
    current_user: CurrentUser = Depends(get_current_active_user),
):
    """Delete a LiveKit room."""
    current_user.require_permission("calls:write")
    await livekit_service.delete_room(room_name)
    return {"message": f"Room {room_name} deleted"}
```

---

## Step 8: Simple Test Client

Create `test_livekit.py`:

```python
#!/usr/bin/env python3
"""Simple test script for LiveKit connection."""
import asyncio
from livekit import api, rtc
import os
from dotenv import load_dotenv

load_dotenv()


async def main():
    url = os.getenv("LIVEKIT_URL")
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")
    
    print(f"Connecting to LiveKit at {url}")
    
    # Create token
    token = api.AccessToken(api_key, api_secret)
    token.with_identity("test-user")
    token.with_name("Test User")
    token.with_grants(api.VideoGrants(
        room_join=True,
        room="test-room",
    ))
    
    jwt = token.to_jwt()
    print(f"\nToken: {jwt[:50]}...")
    
    # Connect to room
    room = rtc.Room()
    
    @room.on("participant_connected")
    def on_participant_connected(participant):
        print(f"Participant connected: {participant.identity}")
    
    @room.on("participant_disconnected")
    def on_participant_disconnected(participant):
        print(f"Participant disconnected: {participant.identity}")
    
    @room.on("track_subscribed")
    def on_track_subscribed(track, publication, participant):
        print(f"Track subscribed: {track.kind} from {participant.identity}")
    
    await room.connect(url, jwt)
    print(f"\n✅ Connected to room: {room.name}")
    print(f"   Local participant: {room.local_participant.identity}")
    
    # Keep alive for testing
    print("\nPress Ctrl+C to exit...")
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        await room.disconnect()
        print("\nDisconnected")


if __name__ == "__main__":
    asyncio.run(main())
```

```bash
# Run test
python test_livekit.py
```

---

## Verification Checklist

- [ ] LiveKit server running (cloud or self-hosted)
- [ ] Can generate tokens with CLI
- [ ] Can join room in LiveKit Meet
- [ ] API key and secret stored in .env
- [ ] Token service working
- [ ] API routes responding

---

## Ports Reference

| Service | Port | Protocol | Purpose |
|---------|------|----------|---------|
| LiveKit Server | 7880 | HTTP/WS | API & WebSocket |
| LiveKit Server | 7881 | TCP | Media (TCP fallback) |
| LiveKit Server | 7882 | UDP | Media (primary) |
| LiveKit SIP | 5060 | UDP/TCP | SIP signaling |
| LiveKit SIP | 10000-60000 | UDP | RTP media |

---

## Next Step

Proceed to: `.claude/skills/06-VOICE-AGENT.md`
