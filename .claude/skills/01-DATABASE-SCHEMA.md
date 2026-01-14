# Skill 01: Database Schema (Multi-Tenant)

## Objective
Create the PostgreSQL database schema for multi-tenant Voice AI Platform with users, RBAC, credits, and call logging.

---

## Schema Overview

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│     tenants     │──────▶│      users      │──────▶│   user_roles    │
│                 │       │                 │       │                 │
│ - id            │       │ - id            │       │ - user_id       │
│ - name          │       │ - tenant_id     │       │ - role_id       │
│ - slug          │       │ - email         │       └─────────────────┘
│ - settings      │       │ - password_hash │               │
│ - credits       │       │ - is_active     │               ▼
└─────────────────┘       └─────────────────┘       ┌─────────────────┐
        │                         │                │     roles       │
        │                         │                │                 │
        ▼                         ▼                │ - id            │
┌─────────────────┐       ┌─────────────────┐      │ - name          │
│ tenant_configs  │       │   api_keys      │      │ - permissions   │
│                 │       │                 │      └─────────────────┘
│ - tenant_id     │       │ - tenant_id     │
│ - agent_prompt  │       │ - key_hash      │
│ - phone_numbers │       │ - scopes        │
│ - tools_enabled │       │ - expires_at    │
└─────────────────┘       └─────────────────┘

┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│   call_logs     │       │ credit_txns     │       │ knowledge_bases │
│                 │       │                 │       │                 │
│ - id            │       │ - id            │       │ - id            │
│ - tenant_id     │       │ - tenant_id     │       │ - tenant_id     │
│ - direction     │       │ - amount        │       │ - name          │
│ - from_number   │       │ - type          │       │ - lightrag_id   │
│ - to_number     │       │ - call_id       │       │ - doc_count     │
│ - duration_sec  │       │ - description   │       └─────────────────┘
│ - credits_used  │       │ - created_at    │
│ - transcript    │       └─────────────────┘
│ - status        │
└─────────────────┘
```

---

## Step 1: Create SQLAlchemy Models

### 1.1 Base Model Setup

```bash
cd ~/voice-ai-platform/src/backend/app
```

Create `db/base.py`:

```python
# src/backend/app/db/base.py
from datetime import datetime
from typing import Any
from sqlalchemy import Column, DateTime, func
from sqlalchemy.ext.declarative import as_declarative, declared_attr


@as_declarative()
class Base:
    id: Any
    __name__: str
    
    # Generate __tablename__ automatically
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
```

### 1.2 Tenant Model

Create `models/tenant.py`:

```python
# src/backend/app/models/tenant.py
import uuid
from sqlalchemy import Column, String, Boolean, Float, JSON, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class Tenant(Base):
    __tablename__ = "tenants"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Credits
    credit_balance = Column(Float, default=0.0, nullable=False)
    credit_limit = Column(Float, default=1000.0, nullable=False)
    
    # Features enabled
    inbound_calls_enabled = Column(Boolean, default=True)
    outbound_calls_enabled = Column(Boolean, default=False)
    
    # Settings (JSON for flexibility)
    settings = Column(JSON, default=dict)
    
    # Contact info
    admin_email = Column(String(255))
    billing_email = Column(String(255))
    
    # Relationships
    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    configs = relationship("TenantConfig", back_populates="tenant", uselist=False, cascade="all, delete-orphan")
    api_keys = relationship("APIKey", back_populates="tenant", cascade="all, delete-orphan")
    call_logs = relationship("CallLog", back_populates="tenant", cascade="all, delete-orphan")
    credit_transactions = relationship("CreditTransaction", back_populates="tenant", cascade="all, delete-orphan")
    knowledge_bases = relationship("KnowledgeBase", back_populates="tenant", cascade="all, delete-orphan")


class TenantConfig(Base):
    __tablename__ = "tenant_configs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    # Voice Agent Configuration
    agent_name = Column(String(100), default="AI Assistant")
    system_prompt = Column(Text)
    first_message = Column(Text)
    voice_id = Column(String(100))  # Cartesia voice ID
    language = Column(String(10), default="en-US")
    
    # LLM Settings
    llm_provider = Column(String(50), default="openai")  # openai, anthropic, openrouter
    llm_model = Column(String(100), default="gpt-4o")
    llm_temperature = Column(Float, default=0.7)
    
    # STT/TTS Settings
    stt_provider = Column(String(50), default="deepgram")
    tts_provider = Column(String(50), default="cartesia")
    
    # Phone Numbers (JSON array)
    phone_numbers = Column(JSON, default=list)
    
    # Tools enabled (JSON array of tool names)
    tools_enabled = Column(JSON, default=list)
    
    # Webhook URLs for events
    webhook_url = Column(String(500))
    
    # Business hours (JSON)
    business_hours = Column(JSON, default=dict)
    
    # Escalation settings
    escalation_phone = Column(String(20))
    escalation_email = Column(String(255))
    
    # Relationship
    tenant = relationship("Tenant", back_populates="configs")
```

### 1.3 User and RBAC Models

Create `models/user.py`:

```python
# src/backend/app/models/user.py
import uuid
from sqlalchemy import Column, String, Boolean, ForeignKey, Table, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


# Association table for user-role many-to-many
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
)


class Role(Base):
    __tablename__ = "roles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(255))
    
    # Permissions as JSON array
    # e.g., ["tenants:read", "tenants:write", "users:read", "calls:read", "credits:manage"]
    permissions = Column(JSON, default=list)
    
    # Is this a system role (cannot be deleted)
    is_system = Column(Boolean, default=False)
    
    # Relationships
    users = relationship("User", secondary=user_roles, back_populates="roles")


class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True)  # Null for super admins
    
    # Auth
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # Profile
    full_name = Column(String(255))
    phone = Column(String(20))
    
    # Status
    is_active = Column(Boolean, default=True)
    is_superadmin = Column(Boolean, default=False)  # Platform-level admin
    
    # Settings
    settings = Column(JSON, default=dict)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="users")
    roles = relationship("Role", secondary=user_roles, back_populates="users")
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
```

### 1.4 API Key Model

Create `models/api_key.py`:

```python
# src/backend/app/models/api_key.py
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, ForeignKey, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class APIKey(Base):
    __tablename__ = "api_keys"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Key info
    name = Column(String(100), nullable=False)
    key_prefix = Column(String(10), nullable=False)  # First 8 chars for identification
    key_hash = Column(String(255), nullable=False)  # Hashed full key
    
    # Scopes/permissions for this key
    scopes = Column(JSON, default=list)  # e.g., ["calls:read", "kb:query"]
    
    # Status
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    
    # Rate limiting
    rate_limit_per_minute = Column(Integer, default=60)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="api_keys")
    user = relationship("User", back_populates="api_keys")
```

### 1.5 Call Logging Model

Create `models/call_log.py`:

```python
# src/backend/app/models/call_log.py
import uuid
from sqlalchemy import Column, String, Integer, Float, ForeignKey, Text, Enum, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.db.base import Base


class CallDirection(str, enum.Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class CallStatus(str, enum.Enum):
    INITIATED = "initiated"
    RINGING = "ringing"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    NO_ANSWER = "no_answer"
    BUSY = "busy"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CallLog(Base):
    __tablename__ = "call_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    
    # Call identifiers
    livekit_room_id = Column(String(100), index=True)
    sip_call_id = Column(String(100))
    
    # Direction and numbers
    direction = Column(Enum(CallDirection), nullable=False)
    from_number = Column(String(20), nullable=False)
    to_number = Column(String(20), nullable=False)
    
    # Status
    status = Column(Enum(CallStatus), default=CallStatus.INITIATED)
    
    # Timing
    started_at = Column(DateTime(timezone=True))
    answered_at = Column(DateTime(timezone=True))
    ended_at = Column(DateTime(timezone=True))
    duration_seconds = Column(Integer, default=0)
    
    # Usage tracking
    stt_seconds = Column(Float, default=0.0)
    tts_characters = Column(Integer, default=0)
    llm_tokens_in = Column(Integer, default=0)
    llm_tokens_out = Column(Integer, default=0)
    rag_queries = Column(Integer, default=0)
    
    # Credits
    credits_used = Column(Float, default=0.0)
    
    # Content
    transcript = Column(Text)
    summary = Column(Text)
    
    # Metadata
    caller_info = Column(JSON, default=dict)  # Customer info if known
    tools_used = Column(JSON, default=list)   # List of tools called
    sentiment = Column(String(20))            # positive, neutral, negative
    
    # Outcome
    outcome = Column(String(100))  # e.g., "appointment_booked", "ticket_created"
    escalated = Column(Boolean, default=False)
    escalation_reason = Column(String(255))
    
    # Relationship
    tenant = relationship("Tenant", back_populates="call_logs")
```

### 1.6 Credit Transaction Model

Create `models/credit.py`:

```python
# src/backend/app/models/credit.py
import uuid
from sqlalchemy import Column, String, Float, ForeignKey, Enum, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.db.base import Base


class TransactionType(str, enum.Enum):
    CREDIT_PURCHASE = "credit_purchase"      # Admin adds credits
    CREDIT_ADJUSTMENT = "credit_adjustment"  # Manual adjustment
    CALL_USAGE = "call_usage"               # Call charges
    STT_USAGE = "stt_usage"
    TTS_USAGE = "tts_usage"
    LLM_USAGE = "llm_usage"
    RAG_USAGE = "rag_usage"
    REFUND = "refund"


class CreditTransaction(Base):
    __tablename__ = "credit_transactions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    
    # Transaction details
    type = Column(Enum(TransactionType), nullable=False)
    amount = Column(Float, nullable=False)  # Positive for credits, negative for usage
    balance_after = Column(Float, nullable=False)
    
    # Reference
    call_id = Column(UUID(as_uuid=True), ForeignKey("call_logs.id", ondelete="SET NULL"), nullable=True)
    
    # Description
    description = Column(String(255))
    notes = Column(Text)
    
    # Who made this transaction
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Relationship
    tenant = relationship("Tenant", back_populates="credit_transactions")
```

### 1.7 Knowledge Base Model

Create `models/knowledge_base.py`:

```python
# src/backend/app/models/knowledge_base.py
import uuid
from sqlalchemy import Column, String, Integer, ForeignKey, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class KnowledgeBase(Base):
    __tablename__ = "knowledge_bases"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    
    # KB info
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # LightRAG integration
    lightrag_workspace_id = Column(String(100))  # If using separate workspaces
    
    # Stats
    document_count = Column(Integer, default=0)
    total_chunks = Column(Integer, default=0)
    last_updated_at = Column(DateTime(timezone=True))
    
    # Settings
    settings = Column(JSON, default=dict)
    
    # Relationship
    tenant = relationship("Tenant", back_populates="knowledge_bases")
    documents = relationship("KBDocument", back_populates="knowledge_base", cascade="all, delete-orphan")


class KBDocument(Base):
    __tablename__ = "kb_documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    knowledge_base_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_bases.id", ondelete="CASCADE"), nullable=False)
    
    # Document info
    filename = Column(String(255), nullable=False)
    file_type = Column(String(50))  # pdf, docx, txt, md
    file_size_bytes = Column(Integer)
    
    # Processing status
    status = Column(String(50), default="pending")  # pending, processing, completed, failed
    error_message = Column(Text)
    
    # Stats
    chunk_count = Column(Integer, default=0)
    
    # Storage
    storage_path = Column(String(500))  # S3/local path
    lightrag_doc_id = Column(String(100))
    
    # Metadata
    metadata = Column(JSON, default=dict)
    
    # Relationship
    knowledge_base = relationship("KnowledgeBase", back_populates="documents")
```

---

## Step 2: Create Models Init File

Create `models/__init__.py`:

```python
# src/backend/app/models/__init__.py
from app.db.base import Base
from app.models.tenant import Tenant, TenantConfig
from app.models.user import User, Role, user_roles
from app.models.api_key import APIKey
from app.models.call_log import CallLog, CallDirection, CallStatus
from app.models.credit import CreditTransaction, TransactionType
from app.models.knowledge_base import KnowledgeBase, KBDocument

__all__ = [
    "Base",
    "Tenant",
    "TenantConfig",
    "User",
    "Role",
    "user_roles",
    "APIKey",
    "CallLog",
    "CallDirection",
    "CallStatus",
    "CreditTransaction",
    "TransactionType",
    "KnowledgeBase",
    "KBDocument",
]
```

---

## Step 3: Database Connection

Create `db/session.py`:

```python
# src/backend/app/db/session.py
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
```

---

## Step 4: Alembic Setup for Migrations

```bash
cd ~/voice-ai-platform/src/backend

# Initialize Alembic
alembic init alembic

# Edit alembic.ini - set sqlalchemy.url
# Or better, use env.py to read from settings
```

Update `alembic/env.py`:

```python
# alembic/env.py
import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Import your models
from app.models import Base
from app.core.config import settings

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def get_url():
    return settings.DATABASE_URL


def run_migrations_offline() -> None:
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()
    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

---

## Step 5: Generate Initial Migration

```bash
cd ~/voice-ai-platform/src/backend

# Create initial migration
alembic revision --autogenerate -m "Initial schema"

# Run migration
alembic upgrade head
```

---

## Step 6: Seed Default Roles

Create `scripts/seed_roles.py`:

```python
# src/backend/scripts/seed_roles.py
import asyncio
from app.db.session import AsyncSessionLocal
from app.models.user import Role

DEFAULT_ROLES = [
    {
        "name": "super_admin",
        "description": "Platform super administrator",
        "permissions": ["*"],  # All permissions
        "is_system": True,
    },
    {
        "name": "tenant_admin",
        "description": "Tenant administrator",
        "permissions": [
            "tenant:read", "tenant:update",
            "users:read", "users:write", "users:delete",
            "calls:read", "calls:export",
            "kb:read", "kb:write", "kb:delete",
            "credits:read",
            "config:read", "config:write",
            "reports:read",
        ],
        "is_system": True,
    },
    {
        "name": "tenant_user",
        "description": "Standard tenant user",
        "permissions": [
            "calls:read",
            "kb:read",
            "reports:read",
        ],
        "is_system": True,
    },
    {
        "name": "api_only",
        "description": "API access only (for integrations)",
        "permissions": [
            "calls:read",
            "kb:query",
        ],
        "is_system": True,
    },
]


async def seed_roles():
    async with AsyncSessionLocal() as session:
        for role_data in DEFAULT_ROLES:
            existing = await session.execute(
                select(Role).where(Role.name == role_data["name"])
            )
            if not existing.scalar_one_or_none():
                role = Role(**role_data)
                session.add(role)
        
        await session.commit()
        print("✅ Default roles seeded")


if __name__ == "__main__":
    asyncio.run(seed_roles())
```

---

## Verification

Run these queries to verify your schema:

```sql
-- Check tables created
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public';

-- Check tenants table structure
\d tenants

-- Check foreign key relationships
SELECT
    tc.table_name, 
    kcu.column_name, 
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name 
FROM 
    information_schema.table_constraints AS tc 
    JOIN information_schema.key_column_usage AS kcu
      ON tc.constraint_name = kcu.constraint_name
    JOIN information_schema.constraint_column_usage AS ccu
      ON ccu.constraint_name = tc.constraint_name
WHERE constraint_type = 'FOREIGN KEY';
```

---

## Next Step

Proceed to: `.claude/skills/02-AUTH-RBAC.md`
