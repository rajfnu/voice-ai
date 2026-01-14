# Skill 07: Telephony & SIP (Phone Calls)

## Objective
Configure SIP trunking with Telnyx/Twilio for inbound and outbound phone calls through LiveKit.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         INBOUND CALL FLOW                                        │
│                                                                                  │
│  ┌─────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐          │
│  │ Caller  │───▶│    PBX      │───▶│ SIP Trunk   │───▶│  LiveKit    │          │
│  │ (PSTN)  │    │  (Hotel/    │    │  (Telnyx)   │    │ SIP Server  │          │
│  └─────────┘    │   Clinic)   │    └─────────────┘    └──────┬──────┘          │
│                 └─────────────┘                              │                  │
│                        OR                                    ▼                  │
│  ┌─────────┐    ┌─────────────┐                      ┌─────────────┐          │
│  │ Caller  │───▶│ SIP Trunk   │─────────────────────▶│  LiveKit    │          │
│  │ (PSTN)  │    │  (Telnyx)   │                      │ SIP Server  │          │
│  └─────────┘    └─────────────┘                      └──────┬──────┘          │
│                                                             │                  │
│                                                             ▼                  │
│                                                      ┌─────────────┐          │
│                                                      │   Dispatch  │          │
│                                                      │    Rules    │          │
│                                                      └──────┬──────┘          │
│                                                             │                  │
│                                                             ▼                  │
│                                                      ┌─────────────┐          │
│                                                      │   LiveKit   │          │
│                                                      │    Room     │          │
│                                                      │  + Agent    │          │
│                                                      └─────────────┘          │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                        OUTBOUND CALL FLOW                                        │
│                                                                                  │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────┐          │
│  │  Backend    │───▶│  LiveKit    │───▶│ SIP Trunk   │───▶│ Customer│          │
│  │  Trigger    │    │ SIP Server  │    │  (Telnyx)   │    │  Phone  │          │
│  │ (Campaign)  │    │  Outbound   │    └─────────────┘    └─────────┘          │
│  └─────────────┘    └─────────────┘                                             │
│                                                                                  │
│  Campaign Manager reads leads from DB/Sheet → Initiates outbound call           │
│  → LiveKit creates room → Agent joins → Customer answers → Conversation         │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Step 1: Set Up Telnyx Account

### 1.1 Create Account
1. Go to https://portal.telnyx.com
2. Sign up for an account
3. Complete identity verification (required for phone numbers)
4. Add $5-10 credit for testing

### 1.2 Purchase a Phone Number
1. Go to **Numbers** → **Search & Buy**
2. Select a local number (cheapest, ~$1/month)
3. Or select a toll-free number for more professional appearance
4. Note your number: `+1XXXXXXXXXX`

### 1.3 Create SIP Connection
1. Go to **Voice** → **SIP Trunking** → **SIP Connections**
2. Click **Create SIP Connection**
3. Configure:
   - **Name**: `voice-ai-platform`
   - **Type**: `Credentials (username/password)`
4. Note credentials:
   - **SIP Username**: (generated)
   - **SIP Password**: (generated)
   - **SIP URI**: `sip.telnyx.com`

### 1.4 Create Outbound Voice Profile
1. Go to **Voice** → **Outbound Voice Profiles**
2. Click **Create**
3. Configure:
   - **Name**: `voice-ai-outbound`
   - **Traffic Type**: `Conversational`
4. Associate with your SIP Connection
5. Add your phone number to the profile

### 1.5 Configure Inbound Settings
1. Go to **Numbers** → **My Numbers**
2. Click your number
3. Set **Connection**: Your SIP Connection
4. Set **Destination**: Your LiveKit SIP server address

---

## Step 2: Alternative - Twilio Setup

### 2.1 Create Twilio Account
1. Go to https://console.twilio.com
2. Sign up and verify
3. Note your **Account SID** and **Auth Token**

### 2.2 Get a Phone Number
1. Go to **Phone Numbers** → **Buy a Number**
2. Select your number
3. Configure Voice settings

### 2.3 Create SIP Domain
1. Go to **Elastic SIP Trunking** → **Trunks**
2. Create a new trunk
3. Add **Origination URI** pointing to LiveKit SIP

---

## Step 3: Configure LiveKit SIP Server

### 3.1 Create SIP Configuration

```bash
cd ~/voice-ai-platform

mkdir -p configs/livekit-sip

cat > configs/livekit-sip/sip-config.yaml << 'EOF'
# SIP Trunk Configuration for Telnyx
sip:
  # SIP Trunks (providers)
  trunks:
    - id: telnyx-trunk
      name: Telnyx Main
      # Inbound settings
      inbound:
        # Numbers associated with this trunk
        numbers:
          - "+1XXXXXXXXXX"  # Your Telnyx number
        # Allowed source IPs (Telnyx SIP IPs)
        allowed_addresses:
          - "64.125.111.0/24"
          - "185.246.205.0/24"
      # Outbound settings
      outbound:
        address: sip.telnyx.com:5060
        transport: tcp
        # Authentication
        auth:
          username: ${TELNYX_SIP_USERNAME}
          password: ${TELNYX_SIP_PASSWORD}
        # Headers to add
        headers:
          - name: X-Connection-ID
            value: ${TELNYX_CONNECTION_ID}

  # Dispatch Rules (route inbound calls to rooms/agents)
  dispatch_rules:
    # Healthcare tenant
    - name: healthcare-inbound
      trunk_ids:
        - telnyx-trunk
      rule:
        # Match by called number
        to_number: "+1HEALTHNUM"
        # Create room with prefix
        room_prefix: "healthcare-"
        # Metadata to pass to agent
        metadata:
          tenant_type: healthcare
          tenant_id: tenant-health-001
    
    # Hospitality tenant
    - name: hospitality-inbound
      trunk_ids:
        - telnyx-trunk
      rule:
        to_number: "+1HOTELNUM"
        room_prefix: "hotel-"
        metadata:
          tenant_type: hospitality
          tenant_id: tenant-hotel-001
    
    # Default catch-all
    - name: default-inbound
      trunk_ids:
        - telnyx-trunk
      rule:
        # No number filter = catch all
        room_prefix: "voice-"
        metadata:
          tenant_type: default
EOF
```

### 3.2 Update Docker Compose for SIP

```bash
cat > docker-compose.sip.yml << 'EOF'
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
    networks:
      - voice-ai-net

  livekit-sip:
    image: livekit/sip:latest
    container_name: voice-ai-sip
    ports:
      # SIP signaling
      - "5060:5060/udp"
      - "5060:5060/tcp"
      # RTP media (large range for concurrent calls)
      - "10000-10100:10000-10100/udp"
    environment:
      - LIVEKIT_URL=ws://livekit:7880
      - LIVEKIT_API_KEY=${LIVEKIT_API_KEY}
      - LIVEKIT_API_SECRET=${LIVEKIT_API_SECRET}
      # SIP settings
      - SIP_PORT_UDP=5060
      - SIP_PORT_TCP=5060
      # External IP (for NAT traversal)
      - SIP_EXTERNAL_IP=${PUBLIC_IP}
    volumes:
      - ./configs/livekit-sip/sip-config.yaml:/etc/sip.yaml
    depends_on:
      - livekit
    restart: unless-stopped
    networks:
      - voice-ai-net

  redis:
    image: redis:7-alpine
    container_name: voice-ai-redis
    volumes:
      - redis_data:/data
    networks:
      - voice-ai-net

networks:
  voice-ai-net:
    driver: bridge

volumes:
  redis_data:
EOF
```

---

## Step 4: Create Outbound Call Service

Create `src/backend/app/services/outbound_call_service.py`:

```python
# src/backend/app/services/outbound_call_service.py
import httpx
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID

from app.core.config import settings
from app.services.livekit_service import livekit_service


class OutboundCallService:
    """Service for initiating outbound calls."""
    
    def __init__(self):
        self.livekit_url = settings.LIVEKIT_URL
        self.api_key = settings.LIVEKIT_API_KEY
        self.api_secret = settings.LIVEKIT_API_SECRET
    
    async def initiate_call(
        self,
        tenant_id: UUID,
        to_number: str,
        from_number: str,
        agent_type: str = "healthcare",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Initiate an outbound call.
        
        Args:
            tenant_id: Tenant making the call
            to_number: Customer phone number (E.164 format)
            from_number: Caller ID to display
            agent_type: Type of agent to use
            metadata: Additional metadata for the call
        
        Returns:
            Call info including room name and call ID
        """
        # Generate room name
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        room_name = f"outbound-{tenant_id}-{timestamp}"
        
        # Prepare call metadata
        call_metadata = {
            "tenant_id": str(tenant_id),
            "agent_type": agent_type,
            "direction": "outbound",
            "to_number": to_number,
            "from_number": from_number,
            "initiated_at": datetime.utcnow().isoformat(),
            **(metadata or {}),
        }
        
        # Create room first
        await livekit_service.create_room(room_name)
        
        # Initiate SIP call via LiveKit API
        # This uses LiveKit's SIP participant API
        sip_participant = await self._create_sip_participant(
            room_name=room_name,
            to_number=to_number,
            from_number=from_number,
            metadata=call_metadata,
        )
        
        return {
            "room_name": room_name,
            "call_id": sip_participant.get("participant_id"),
            "status": "initiated",
            "to_number": to_number,
            "from_number": from_number,
        }
    
    async def _create_sip_participant(
        self,
        room_name: str,
        to_number: str,
        from_number: str,
        metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Create a SIP participant (outbound call)."""
        from livekit import api
        
        lk_api = api.LiveKitAPI(
            url=self.livekit_url.replace("ws://", "http://").replace("wss://", "https://"),
            api_key=self.api_key,
            api_secret=self.api_secret,
        )
        
        # Create SIP participant for outbound call
        request = api.CreateSIPParticipantRequest(
            room_name=room_name,
            sip_trunk_id="telnyx-trunk",
            sip_call_to=to_number,
            participant_identity=f"customer-{to_number}",
            participant_name="Customer",
            participant_metadata=str(metadata),
        )
        
        response = await lk_api.sip.create_sip_participant(request)
        
        return {
            "participant_id": response.participant_id,
            "sip_call_id": response.sip_call_id,
        }
    
    async def end_call(self, room_name: str) -> bool:
        """End an active call by closing the room."""
        return await livekit_service.delete_room(room_name)


# Singleton
outbound_call_service = OutboundCallService()
```

---

## Step 5: Create Outbound Campaign System

Create `src/backend/app/services/campaign_service.py`:

```python
# src/backend/app/services/campaign_service.py
import asyncio
from typing import List, Optional
from datetime import datetime, timedelta
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.models.campaign import Campaign, CampaignLead, LeadStatus
from app.models.tenant import Tenant
from app.services.outbound_call_service import outbound_call_service
from app.services.credit_service import credit_service


class CampaignService:
    """Service for managing outbound call campaigns."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_campaign(
        self,
        tenant_id: UUID,
        name: str,
        leads: List[dict],
        from_number: str,
        agent_type: str = "healthcare",
        max_concurrent_calls: int = 5,
        calls_per_day_limit: int = 100,
        start_time: str = "09:00",
        end_time: str = "17:00",
    ) -> Campaign:
        """Create a new outbound campaign."""
        campaign = Campaign(
            tenant_id=tenant_id,
            name=name,
            from_number=from_number,
            agent_type=agent_type,
            max_concurrent_calls=max_concurrent_calls,
            calls_per_day_limit=calls_per_day_limit,
            start_time=start_time,
            end_time=end_time,
            status="pending",
        )
        
        self.db.add(campaign)
        await self.db.flush()
        
        # Add leads
        for lead_data in leads:
            lead = CampaignLead(
                campaign_id=campaign.id,
                phone_number=lead_data["phone"],
                name=lead_data.get("name"),
                metadata=lead_data.get("metadata", {}),
                status=LeadStatus.PENDING,
            )
            self.db.add(lead)
        
        await self.db.commit()
        return campaign
    
    async def start_campaign(self, campaign_id: UUID) -> bool:
        """Start executing a campaign."""
        campaign = await self.db.get(Campaign, campaign_id)
        if not campaign:
            return False
        
        campaign.status = "running"
        campaign.started_at = datetime.utcnow()
        await self.db.commit()
        
        # Start processing in background
        asyncio.create_task(self._process_campaign(campaign_id))
        
        return True
    
    async def _process_campaign(self, campaign_id: UUID):
        """Process campaign leads (runs in background)."""
        while True:
            # Refresh campaign status
            campaign = await self.db.get(Campaign, campaign_id)
            if not campaign or campaign.status != "running":
                break
            
            # Check time window
            now = datetime.now()
            start_time = datetime.strptime(campaign.start_time, "%H:%M").time()
            end_time = datetime.strptime(campaign.end_time, "%H:%M").time()
            
            if not (start_time <= now.time() <= end_time):
                # Outside calling hours
                await asyncio.sleep(60)
                continue
            
            # Check daily limit
            today_calls = await self._get_today_call_count(campaign_id)
            if today_calls >= campaign.calls_per_day_limit:
                # Daily limit reached
                await asyncio.sleep(3600)  # Check again in an hour
                continue
            
            # Check concurrent calls
            active_calls = await self._get_active_call_count(campaign_id)
            if active_calls >= campaign.max_concurrent_calls:
                await asyncio.sleep(10)
                continue
            
            # Check tenant credits
            tenant = await self.db.get(Tenant, campaign.tenant_id)
            if tenant.credit_balance < 2.0:  # Minimum for a call
                campaign.status = "paused"
                campaign.pause_reason = "insufficient_credits"
                await self.db.commit()
                break
            
            # Get next pending lead
            result = await self.db.execute(
                select(CampaignLead)
                .where(CampaignLead.campaign_id == campaign_id)
                .where(CampaignLead.status == LeadStatus.PENDING)
                .limit(1)
            )
            lead = result.scalar_one_or_none()
            
            if not lead:
                # No more leads
                campaign.status = "completed"
                campaign.completed_at = datetime.utcnow()
                await self.db.commit()
                break
            
            # Initiate call
            try:
                lead.status = LeadStatus.CALLING
                lead.attempt_count += 1
                lead.last_attempt_at = datetime.utcnow()
                await self.db.commit()
                
                call_result = await outbound_call_service.initiate_call(
                    tenant_id=campaign.tenant_id,
                    to_number=lead.phone_number,
                    from_number=campaign.from_number,
                    agent_type=campaign.agent_type,
                    metadata={
                        "campaign_id": str(campaign_id),
                        "lead_id": str(lead.id),
                        "lead_name": lead.name,
                    },
                )
                
                lead.room_name = call_result["room_name"]
                await self.db.commit()
                
            except Exception as e:
                lead.status = LeadStatus.FAILED
                lead.error_message = str(e)
                await self.db.commit()
            
            # Small delay between calls
            await asyncio.sleep(2)
    
    async def handle_call_status(
        self,
        room_name: str,
        status: str,
        duration_seconds: int = 0,
    ):
        """Handle call status webhook from LiveKit."""
        # Find lead by room name
        result = await self.db.execute(
            select(CampaignLead)
            .where(CampaignLead.room_name == room_name)
        )
        lead = result.scalar_one_or_none()
        
        if not lead:
            return
        
        if status == "answered":
            lead.status = LeadStatus.IN_PROGRESS
            lead.answered_at = datetime.utcnow()
        
        elif status == "completed":
            lead.status = LeadStatus.COMPLETED
            lead.duration_seconds = duration_seconds
            lead.completed_at = datetime.utcnow()
            
            # Deduct credits
            campaign = await self.db.get(Campaign, lead.campaign_id)
            await credit_service.deduct_call_credits(
                tenant_id=campaign.tenant_id,
                duration_seconds=duration_seconds,
                direction="outbound",
            )
        
        elif status == "no_answer":
            if lead.attempt_count < 3:
                # Retry later
                lead.status = LeadStatus.PENDING
                lead.next_retry_at = datetime.utcnow() + timedelta(hours=2)
            else:
                lead.status = LeadStatus.NO_ANSWER
        
        elif status == "busy":
            lead.status = LeadStatus.BUSY
        
        elif status == "failed":
            lead.status = LeadStatus.FAILED
        
        await self.db.commit()
    
    async def _get_today_call_count(self, campaign_id: UUID) -> int:
        """Get number of calls made today."""
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0)
        result = await self.db.execute(
            select(func.count(CampaignLead.id))
            .where(CampaignLead.campaign_id == campaign_id)
            .where(CampaignLead.last_attempt_at >= today_start)
        )
        return result.scalar() or 0
    
    async def _get_active_call_count(self, campaign_id: UUID) -> int:
        """Get number of currently active calls."""
        result = await self.db.execute(
            select(func.count(CampaignLead.id))
            .where(CampaignLead.campaign_id == campaign_id)
            .where(CampaignLead.status.in_([
                LeadStatus.CALLING,
                LeadStatus.IN_PROGRESS,
            ]))
        )
        return result.scalar() or 0
```

---

## Step 6: Create Campaign Models

Create `src/backend/app/models/campaign.py`:

```python
# src/backend/app/models/campaign.py
import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, ForeignKey, DateTime, Text, JSON, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class LeadStatus(str, enum.Enum):
    PENDING = "pending"
    CALLING = "calling"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    NO_ANSWER = "no_answer"
    BUSY = "busy"
    FAILED = "failed"


class Campaign(Base):
    __tablename__ = "campaigns"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    
    # Campaign info
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Call settings
    from_number = Column(String(20), nullable=False)
    agent_type = Column(String(50), default="healthcare")
    
    # Limits
    max_concurrent_calls = Column(Integer, default=5)
    calls_per_day_limit = Column(Integer, default=100)
    
    # Time window
    start_time = Column(String(5), default="09:00")  # HH:MM
    end_time = Column(String(5), default="17:00")
    timezone = Column(String(50), default="UTC")
    
    # Status
    status = Column(String(20), default="pending")  # pending, running, paused, completed
    pause_reason = Column(String(255))
    
    # Timestamps
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    
    # Stats
    total_leads = Column(Integer, default=0)
    completed_calls = Column(Integer, default=0)
    successful_calls = Column(Integer, default=0)
    
    # Relationships
    tenant = relationship("Tenant")
    leads = relationship("CampaignLead", back_populates="campaign", cascade="all, delete-orphan")


class CampaignLead(Base):
    __tablename__ = "campaign_leads"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False)
    
    # Lead info
    phone_number = Column(String(20), nullable=False)
    name = Column(String(255))
    email = Column(String(255))
    metadata = Column(JSON, default=dict)
    
    # Call tracking
    status = Column(Enum(LeadStatus), default=LeadStatus.PENDING)
    room_name = Column(String(100))
    
    # Attempts
    attempt_count = Column(Integer, default=0)
    last_attempt_at = Column(DateTime(timezone=True))
    next_retry_at = Column(DateTime(timezone=True))
    
    # Results
    answered_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    duration_seconds = Column(Integer, default=0)
    
    # Outcome
    outcome = Column(String(100))
    notes = Column(Text)
    error_message = Column(String(500))
    
    # Relationship
    campaign = relationship("Campaign", back_populates="leads")
```

---

## Step 7: Create API Routes for Campaigns

Create `src/backend/app/api/routes/campaigns.py`:

```python
# src/backend/app/api/routes/campaigns.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from pydantic import BaseModel
from uuid import UUID

from app.db.session import get_db
from app.api.deps import get_current_active_user, CurrentUser, require_permission
from app.services.campaign_service import CampaignService

router = APIRouter(prefix="/campaigns", tags=["Campaigns"])


class LeadCreate(BaseModel):
    phone: str
    name: Optional[str] = None
    email: Optional[str] = None
    metadata: Optional[dict] = None


class CampaignCreate(BaseModel):
    name: str
    from_number: str
    agent_type: str = "healthcare"
    leads: List[LeadCreate]
    max_concurrent_calls: int = 5
    calls_per_day_limit: int = 100
    start_time: str = "09:00"
    end_time: str = "17:00"


class CampaignResponse(BaseModel):
    id: UUID
    name: str
    status: str
    total_leads: int
    completed_calls: int
    
    class Config:
        from_attributes = True


@router.post("/", response_model=CampaignResponse)
async def create_campaign(
    request: CampaignCreate,
    current_user: CurrentUser = Depends(require_permission("campaigns:write")),
    db: AsyncSession = Depends(get_db),
):
    """Create a new outbound call campaign."""
    if not current_user.tenant:
        raise HTTPException(status_code=403, detail="Tenant required")
    
    # Check if outbound calls are enabled
    if not current_user.tenant.outbound_calls_enabled:
        raise HTTPException(status_code=403, detail="Outbound calls not enabled for this tenant")
    
    service = CampaignService(db)
    campaign = await service.create_campaign(
        tenant_id=current_user.tenant.id,
        name=request.name,
        leads=[l.dict() for l in request.leads],
        from_number=request.from_number,
        agent_type=request.agent_type,
        max_concurrent_calls=request.max_concurrent_calls,
        calls_per_day_limit=request.calls_per_day_limit,
        start_time=request.start_time,
        end_time=request.end_time,
    )
    
    return campaign


@router.post("/{campaign_id}/start")
async def start_campaign(
    campaign_id: UUID,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser = Depends(require_permission("campaigns:write")),
    db: AsyncSession = Depends(get_db),
):
    """Start a campaign."""
    service = CampaignService(db)
    success = await service.start_campaign(campaign_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    return {"message": "Campaign started", "campaign_id": str(campaign_id)}


@router.post("/{campaign_id}/pause")
async def pause_campaign(
    campaign_id: UUID,
    current_user: CurrentUser = Depends(require_permission("campaigns:write")),
    db: AsyncSession = Depends(get_db),
):
    """Pause a running campaign."""
    campaign = await db.get(Campaign, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    campaign.status = "paused"
    await db.commit()
    
    return {"message": "Campaign paused"}


@router.get("/", response_model=List[CampaignResponse])
async def list_campaigns(
    current_user: CurrentUser = Depends(require_permission("campaigns:read")),
    db: AsyncSession = Depends(get_db),
):
    """List all campaigns for the tenant."""
    result = await db.execute(
        select(Campaign)
        .where(Campaign.tenant_id == current_user.tenant.id)
        .order_by(Campaign.created_at.desc())
    )
    return result.scalars().all()
```

---

## Step 8: Webhook Handler for Call Events

Create `src/backend/app/api/routes/webhooks.py`:

```python
# src/backend/app/api/routes/webhooks.py
from fastapi import APIRouter, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.services.campaign_service import CampaignService

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


@router.post("/livekit/sip")
async def livekit_sip_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Handle LiveKit SIP call events."""
    payload = await request.json()
    
    event_type = payload.get("event")
    room_name = payload.get("room", {}).get("name")
    
    service = CampaignService(db)
    
    if event_type == "participant_joined":
        # Call answered
        await service.handle_call_status(room_name, "answered")
    
    elif event_type == "participant_left":
        duration = payload.get("participant", {}).get("joined_duration_ms", 0) // 1000
        await service.handle_call_status(room_name, "completed", duration)
    
    elif event_type == "room_finished":
        # Room closed
        pass
    
    return {"status": "ok"}


@router.post("/telnyx")
async def telnyx_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Handle Telnyx call events."""
    payload = await request.json()
    data = payload.get("data", {})
    event_type = data.get("event_type")
    
    # Extract call info
    call_control_id = data.get("payload", {}).get("call_control_id")
    
    if event_type == "call.initiated":
        pass  # Call is starting
    
    elif event_type == "call.answered":
        pass  # Customer answered
    
    elif event_type == "call.hangup":
        hangup_cause = data.get("payload", {}).get("hangup_cause")
        # Handle based on hangup cause
    
    return {"status": "ok"}
```

---

## Step 9: Phone Number Warming Strategy

Create a warming workflow in n8n or backend:

```python
# Phone warming logic
WARMING_CONFIG = {
    "initial_calls_per_day": 5,
    "increment_per_day": 10,
    "max_calls_per_day": 100,
    "warming_period_days": 14,
}

async def get_phone_capacity(phone_number: str, days_active: int) -> int:
    """Calculate how many calls a phone can make based on warming."""
    if days_active >= WARMING_CONFIG["warming_period_days"]:
        return WARMING_CONFIG["max_calls_per_day"]
    
    return min(
        WARMING_CONFIG["initial_calls_per_day"] + 
        (days_active * WARMING_CONFIG["increment_per_day"]),
        WARMING_CONFIG["max_calls_per_day"]
    )
```

---

## Testing Checklist

- [ ] Telnyx/Twilio account created
- [ ] Phone number purchased
- [ ] SIP trunk configured
- [ ] LiveKit SIP server running
- [ ] Inbound call routes to agent
- [ ] Outbound call initiates
- [ ] Call status webhooks working
- [ ] Campaign system tested

---

## Important: Legal Compliance

⚠️ **Cold calling without consent is illegal in most jurisdictions.**

Ensure you have:
- Proper consent from call recipients
- Do Not Call list compliance
- TCPA compliance (US)
- GDPR compliance (EU)
- Local regulations compliance

---

## Next Step

Proceed to: `.claude/skills/08-ADMIN-DASHBOARD.md`
