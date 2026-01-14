# Skill 09: Credit System & Usage Tracking

## Objective
Implement a comprehensive credit system for tracking and billing usage across tenants, including call minutes, AI tokens, and RAG queries.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            CREDIT SYSTEM ARCHITECTURE                            │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                         Credit Flow                                      │    │
│  │                                                                          │    │
│  │  Admin Adds Credits ──▶ Tenant Balance ──▶ Real-time Deductions         │    │
│  │         │                     │                    │                     │    │
│  │         ▼                     ▼                    ▼                     │    │
│  │  ┌───────────┐        ┌───────────┐        ┌───────────────┐            │    │
│  │  │ Purchase  │        │  Balance  │        │ Usage Tracking│            │    │
│  │  │ Transaction│        │  Check    │        │ (Per Resource)│            │    │
│  │  └───────────┘        └───────────┘        └───────────────┘            │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                       Usage Meters                                       │    │
│  │                                                                          │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │    │
│  │  │ Call Minutes │  │  STT Usage   │  │  LLM Tokens  │  │  TTS Chars   │ │    │
│  │  │              │  │              │  │              │  │              │ │    │
│  │  │ Inbound: 1/m │  │ 0.5 cr/min   │  │ 0.1 cr/1K    │  │ 0.05 cr/1K   │ │    │
│  │  │ Outbound:2/m │  │              │  │              │  │              │ │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘ │    │
│  │                                                                          │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │    │
│  │  │  RAG Query   │  │ Storage GB   │  │ Action Tools │  │  Send Email  │ │    │
│  │  │              │  │              │  │  (Booking,   │  │              │ │    │
│  │  │ 0.02 cr/qry  │  │ 0.1 cr/GB/mo │  │   Tickets)   │  │ 0.10 cr/ea   │ │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘ │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Step 1: Credit Configuration

Create `core/credit_config.py`:

```python
# src/backend/app/core/credit_config.py
from pydantic_settings import BaseSettings
from decimal import Decimal


class CreditRates(BaseSettings):
    """Credit rates for different resources."""

    # Call rates (per minute)
    INBOUND_CALL_PER_MIN: Decimal = Decimal("1.0")
    OUTBOUND_CALL_PER_MIN: Decimal = Decimal("2.0")

    # AI service rates
    STT_PER_MIN: Decimal = Decimal("0.5")           # Speech-to-text
    TTS_PER_1K_CHARS: Decimal = Decimal("0.05")     # Text-to-speech
    LLM_INPUT_PER_1K_TOKENS: Decimal = Decimal("0.05")
    LLM_OUTPUT_PER_1K_TOKENS: Decimal = Decimal("0.15")

    # RAG rates
    RAG_QUERY: Decimal = Decimal("0.02")
    RAG_DOCUMENT_PROCESSING_PER_PAGE: Decimal = Decimal("0.01")

    # ============================================
    # ACTION TOOL RATES (Write Operations)
    # These are charged separately from AI usage
    # because they perform external integrations
    # ============================================
    ACTION_BOOK_APPOINTMENT: Decimal = Decimal("0.25")      # Calendar booking
    ACTION_SEND_EMAIL: Decimal = Decimal("0.10")            # Confirmation email
    ACTION_CREATE_TICKET: Decimal = Decimal("0.05")         # Support ticket
    ACTION_GUEST_CHECKIN: Decimal = Decimal("0.15")         # Hotel check-in

    # Storage rates (per GB per month)
    KB_STORAGE_PER_GB: Decimal = Decimal("0.1")

    # Minimum balance to make calls
    MIN_BALANCE_FOR_CALLS: Decimal = Decimal("1.0")

    # Minimum balance for action tools
    MIN_BALANCE_FOR_ACTIONS: Decimal = Decimal("0.50")

    # Low balance warning threshold
    LOW_BALANCE_WARNING: Decimal = Decimal("10.0")

    class Config:
        env_prefix = "CREDIT_RATE_"


credit_rates = CreditRates()
```

---

## Step 2: Credit Service

Create `services/credit_service.py`:

```python
# src/backend/app/services/credit_service.py
from decimal import Decimal
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
import logging

from app.models.tenant import Tenant
from app.models.credit import CreditTransaction, TransactionType
from app.models.call_log import CallLog, CallDirection
from app.core.credit_config import credit_rates

logger = logging.getLogger(__name__)


class CreditService:
    """Service for managing tenant credits."""
    
    async def get_balance(self, db: AsyncSession, tenant_id: str) -> Decimal:
        """Get current credit balance for a tenant."""
        tenant = await db.get(Tenant, tenant_id)
        if not tenant:
            raise ValueError("Tenant not found")
        return Decimal(str(tenant.credit_balance))
    
    async def check_credits(
        self, 
        db: AsyncSession, 
        tenant_id: str, 
        min_credits: Decimal = None,
    ) -> bool:
        """Check if tenant has sufficient credits."""
        balance = await self.get_balance(db, tenant_id)
        min_required = min_credits or credit_rates.MIN_BALANCE_FOR_CALLS
        return balance >= min_required
    
    async def add_credits(
        self,
        db: AsyncSession,
        tenant_id: str,
        amount: Decimal,
        description: str = "Credit purchase",
        created_by_user_id: Optional[str] = None,
        transaction_type: TransactionType = TransactionType.CREDIT_PURCHASE,
    ) -> CreditTransaction:
        """
        Add credits to a tenant's account.
        
        Args:
            db: Database session
            tenant_id: Tenant ID
            amount: Amount to add (positive)
            description: Transaction description
            created_by_user_id: User who initiated the transaction
            transaction_type: Type of transaction
        
        Returns:
            The created transaction
        """
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        tenant = await db.get(Tenant, tenant_id)
        if not tenant:
            raise ValueError("Tenant not found")
        
        # Update balance
        new_balance = Decimal(str(tenant.credit_balance)) + amount
        tenant.credit_balance = float(new_balance)
        
        # Create transaction record
        transaction = CreditTransaction(
            tenant_id=tenant_id,
            type=transaction_type,
            amount=float(amount),
            balance_after=float(new_balance),
            description=description,
            created_by_user_id=created_by_user_id,
        )
        
        db.add(transaction)
        await db.commit()
        await db.refresh(transaction)
        
        logger.info(f"Added {amount} credits to tenant {tenant_id}. New balance: {new_balance}")
        
        return transaction
    
    async def deduct_credits(
        self,
        db: AsyncSession,
        tenant_id: str,
        amount: Decimal,
        transaction_type: TransactionType,
        description: str,
        call_id: Optional[str] = None,
    ) -> CreditTransaction:
        """
        Deduct credits from a tenant's account.
        
        Args:
            db: Database session
            tenant_id: Tenant ID
            amount: Amount to deduct (positive number)
            transaction_type: Type of usage
            description: Transaction description
            call_id: Associated call ID if applicable
        
        Returns:
            The created transaction
        """
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        tenant = await db.get(Tenant, tenant_id)
        if not tenant:
            raise ValueError("Tenant not found")
        
        current_balance = Decimal(str(tenant.credit_balance))
        
        # Allow negative balance but log warning
        if current_balance < amount:
            logger.warning(
                f"Tenant {tenant_id} balance ({current_balance}) "
                f"insufficient for deduction ({amount})"
            )
        
        # Update balance
        new_balance = current_balance - amount
        tenant.credit_balance = float(new_balance)
        
        # Create transaction record
        transaction = CreditTransaction(
            tenant_id=tenant_id,
            type=transaction_type,
            amount=float(-amount),  # Negative for deductions
            balance_after=float(new_balance),
            description=description,
            call_id=call_id,
        )
        
        db.add(transaction)
        await db.commit()
        await db.refresh(transaction)
        
        logger.info(
            f"Deducted {amount} credits from tenant {tenant_id}. "
            f"Type: {transaction_type}. New balance: {new_balance}"
        )
        
        return transaction
    
    async def deduct_call_credits(
        self,
        db: AsyncSession,
        tenant_id: str,
        call_id: str,
        duration_seconds: int,
        direction: CallDirection,
    ) -> CreditTransaction:
        """Deduct credits for a call based on duration and direction."""
        minutes = Decimal(duration_seconds) / Decimal(60)
        
        if direction == CallDirection.INBOUND:
            rate = credit_rates.INBOUND_CALL_PER_MIN
        else:
            rate = credit_rates.OUTBOUND_CALL_PER_MIN
        
        amount = minutes * rate
        
        # Round up to 2 decimal places
        amount = amount.quantize(Decimal("0.01"))
        
        return await self.deduct_credits(
            db=db,
            tenant_id=tenant_id,
            amount=amount,
            transaction_type=TransactionType.CALL_USAGE,
            description=f"{direction.value} call - {duration_seconds}s",
            call_id=call_id,
        )
    
    async def deduct_ai_credits(
        self,
        db: AsyncSession,
        tenant_id: str,
        call_id: str,
        stt_seconds: float = 0,
        tts_characters: int = 0,
        llm_input_tokens: int = 0,
        llm_output_tokens: int = 0,
        rag_queries: int = 0,
    ) -> List[CreditTransaction]:
        """
        Deduct credits for AI services used during a call.
        Creates separate transactions for each service.
        """
        transactions = []
        
        # STT usage
        if stt_seconds > 0:
            stt_minutes = Decimal(str(stt_seconds)) / Decimal(60)
            stt_cost = stt_minutes * credit_rates.STT_PER_MIN
            if stt_cost > 0:
                txn = await self.deduct_credits(
                    db=db,
                    tenant_id=tenant_id,
                    amount=stt_cost.quantize(Decimal("0.01")),
                    transaction_type=TransactionType.STT_USAGE,
                    description=f"STT: {stt_seconds:.1f}s",
                    call_id=call_id,
                )
                transactions.append(txn)
        
        # TTS usage
        if tts_characters > 0:
            tts_cost = (Decimal(tts_characters) / Decimal(1000)) * credit_rates.TTS_PER_1K_CHARS
            if tts_cost > 0:
                txn = await self.deduct_credits(
                    db=db,
                    tenant_id=tenant_id,
                    amount=tts_cost.quantize(Decimal("0.01")),
                    transaction_type=TransactionType.TTS_USAGE,
                    description=f"TTS: {tts_characters} chars",
                    call_id=call_id,
                )
                transactions.append(txn)
        
        # LLM usage
        if llm_input_tokens > 0 or llm_output_tokens > 0:
            llm_input_cost = (Decimal(llm_input_tokens) / Decimal(1000)) * credit_rates.LLM_INPUT_PER_1K_TOKENS
            llm_output_cost = (Decimal(llm_output_tokens) / Decimal(1000)) * credit_rates.LLM_OUTPUT_PER_1K_TOKENS
            llm_cost = llm_input_cost + llm_output_cost
            if llm_cost > 0:
                txn = await self.deduct_credits(
                    db=db,
                    tenant_id=tenant_id,
                    amount=llm_cost.quantize(Decimal("0.01")),
                    transaction_type=TransactionType.LLM_USAGE,
                    description=f"LLM: {llm_input_tokens}in/{llm_output_tokens}out tokens",
                    call_id=call_id,
                )
                transactions.append(txn)
        
        # RAG usage
        if rag_queries > 0:
            rag_cost = Decimal(rag_queries) * credit_rates.RAG_QUERY
            if rag_cost > 0:
                txn = await self.deduct_credits(
                    db=db,
                    tenant_id=tenant_id,
                    amount=rag_cost.quantize(Decimal("0.01")),
                    transaction_type=TransactionType.RAG_USAGE,
                    description=f"RAG: {rag_queries} queries",
                    call_id=call_id,
                )
                transactions.append(txn)
        
        return transactions
    
    async def get_usage_summary(
        self,
        db: AsyncSession,
        tenant_id: str,
        start_date: datetime = None,
        end_date: datetime = None,
    ) -> Dict[str, Any]:
        """Get usage summary for a tenant."""
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()
        
        # Get transactions in date range
        result = await db.execute(
            select(CreditTransaction)
            .where(
                CreditTransaction.tenant_id == tenant_id,
                CreditTransaction.created_at >= start_date,
                CreditTransaction.created_at <= end_date,
            )
        )
        transactions = result.scalars().all()
        
        # Aggregate by type
        usage_by_type = {}
        for txn in transactions:
            if txn.type not in usage_by_type:
                usage_by_type[txn.type.value] = {
                    "count": 0,
                    "total_credits": Decimal(0),
                }
            usage_by_type[txn.type.value]["count"] += 1
            usage_by_type[txn.type.value]["total_credits"] += Decimal(str(abs(txn.amount)))
        
        # Get call stats
        call_result = await db.execute(
            select(
                func.count(CallLog.id).label("total_calls"),
                func.sum(CallLog.duration_seconds).label("total_duration"),
            )
            .where(
                CallLog.tenant_id == tenant_id,
                CallLog.created_at >= start_date,
                CallLog.created_at <= end_date,
            )
        )
        call_stats = call_result.one()
        
        # Get current balance
        tenant = await db.get(Tenant, tenant_id)
        
        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
            "current_balance": float(tenant.credit_balance) if tenant else 0,
            "usage_by_type": {
                k: {
                    "count": v["count"],
                    "total_credits": float(v["total_credits"]),
                }
                for k, v in usage_by_type.items()
            },
            "calls": {
                "total": call_stats.total_calls or 0,
                "total_duration_seconds": call_stats.total_duration or 0,
            },
            "total_credits_used": float(sum(
                v["total_credits"] 
                for k, v in usage_by_type.items() 
                if not k.startswith("credit_")
            )),
        }
    
    async def get_transactions(
        self,
        db: AsyncSession,
        tenant_id: str,
        limit: int = 50,
        offset: int = 0,
        transaction_type: Optional[TransactionType] = None,
    ) -> List[CreditTransaction]:
        """Get transaction history for a tenant."""
        query = select(CreditTransaction).where(
            CreditTransaction.tenant_id == tenant_id
        )
        
        if transaction_type:
            query = query.where(CreditTransaction.type == transaction_type)
        
        query = query.order_by(CreditTransaction.created_at.desc())
        query = query.limit(limit).offset(offset)
        
        result = await db.execute(query)
        return result.scalars().all()


# Singleton instance
credit_service = CreditService()
```

---

## Step 3: Credit API Routes

Create `api/routes/credits.py`:

```python
# src/backend/app/api/routes/credits.py
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.deps import (
    get_current_active_user, 
    get_current_superadmin,
    CurrentUser,
    require_permission,
)
from app.services.credit_service import credit_service
from app.models.credit import TransactionType

router = APIRouter(prefix="/credits", tags=["Credits"])


class AddCreditsRequest(BaseModel):
    tenant_id: str
    amount: float = Field(gt=0, description="Amount of credits to add")
    description: Optional[str] = "Credit purchase"


class AddCreditsResponse(BaseModel):
    transaction_id: str
    tenant_id: str
    amount: float
    new_balance: float
    description: str


class BalanceResponse(BaseModel):
    tenant_id: str
    balance: float
    credit_limit: float
    is_low: bool


class UsageSummaryResponse(BaseModel):
    period: dict
    current_balance: float
    usage_by_type: dict
    calls: dict
    total_credits_used: float


class TransactionResponse(BaseModel):
    id: str
    type: str
    amount: float
    balance_after: float
    description: Optional[str]
    call_id: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============== Admin Endpoints ==============

@router.post("/add", response_model=AddCreditsResponse)
async def add_credits(
    request: AddCreditsRequest,
    current_user: CurrentUser = Depends(get_current_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """
    Add credits to a tenant's account. (Superadmin only)
    """
    transaction = await credit_service.add_credits(
        db=db,
        tenant_id=request.tenant_id,
        amount=Decimal(str(request.amount)),
        description=request.description,
        created_by_user_id=str(current_user.user.id),
    )
    
    return AddCreditsResponse(
        transaction_id=str(transaction.id),
        tenant_id=request.tenant_id,
        amount=request.amount,
        new_balance=transaction.balance_after,
        description=request.description,
    )


@router.post("/adjust")
async def adjust_credits(
    request: AddCreditsRequest,
    current_user: CurrentUser = Depends(get_current_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """
    Adjust credits (add or remove) for a tenant. (Superadmin only)
    Use positive amount to add, handled by add_credits.
    """
    transaction = await credit_service.add_credits(
        db=db,
        tenant_id=request.tenant_id,
        amount=Decimal(str(request.amount)),
        description=request.description or "Credit adjustment",
        created_by_user_id=str(current_user.user.id),
        transaction_type=TransactionType.CREDIT_ADJUSTMENT,
    )
    
    return {
        "transaction_id": str(transaction.id),
        "new_balance": transaction.balance_after,
    }


# ============== Tenant Endpoints ==============

@router.get("/balance", response_model=BalanceResponse)
async def get_balance(
    current_user: CurrentUser = Depends(require_permission("credits:read")),
    db: AsyncSession = Depends(get_db),
):
    """Get credit balance for current tenant."""
    if not current_user.tenant:
        raise HTTPException(status_code=400, detail="No tenant associated")
    
    from app.core.credit_config import credit_rates
    
    balance = await credit_service.get_balance(db, str(current_user.tenant.id))
    
    return BalanceResponse(
        tenant_id=str(current_user.tenant.id),
        balance=float(balance),
        credit_limit=float(current_user.tenant.credit_limit),
        is_low=balance < credit_rates.LOW_BALANCE_WARNING,
    )


@router.get("/usage", response_model=UsageSummaryResponse)
async def get_usage_summary(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: CurrentUser = Depends(require_permission("credits:read")),
    db: AsyncSession = Depends(get_db),
):
    """Get usage summary for current tenant."""
    if not current_user.tenant:
        raise HTTPException(status_code=400, detail="No tenant associated")
    
    summary = await credit_service.get_usage_summary(
        db=db,
        tenant_id=str(current_user.tenant.id),
        start_date=start_date,
        end_date=end_date,
    )
    
    return UsageSummaryResponse(**summary)


@router.get("/transactions", response_model=List[TransactionResponse])
async def get_transactions(
    limit: int = Query(50, le=100),
    offset: int = Query(0),
    type: Optional[str] = Query(None),
    current_user: CurrentUser = Depends(require_permission("credits:read")),
    db: AsyncSession = Depends(get_db),
):
    """Get transaction history for current tenant."""
    if not current_user.tenant:
        raise HTTPException(status_code=400, detail="No tenant associated")
    
    transaction_type = None
    if type:
        try:
            transaction_type = TransactionType(type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid transaction type: {type}")
    
    transactions = await credit_service.get_transactions(
        db=db,
        tenant_id=str(current_user.tenant.id),
        limit=limit,
        offset=offset,
        transaction_type=transaction_type,
    )
    
    return [
        TransactionResponse(
            id=str(t.id),
            type=t.type.value,
            amount=t.amount,
            balance_after=t.balance_after,
            description=t.description,
            call_id=str(t.call_id) if t.call_id else None,
            created_at=t.created_at,
        )
        for t in transactions
    ]


@router.get("/check")
async def check_sufficient_credits(
    min_credits: float = Query(1.0),
    current_user: CurrentUser = Depends(require_permission("credits:read")),
    db: AsyncSession = Depends(get_db),
):
    """Check if tenant has sufficient credits for an operation."""
    if not current_user.tenant:
        raise HTTPException(status_code=400, detail="No tenant associated")
    
    has_credits = await credit_service.check_credits(
        db=db,
        tenant_id=str(current_user.tenant.id),
        min_credits=Decimal(str(min_credits)),
    )
    
    return {
        "has_sufficient_credits": has_credits,
        "min_required": min_credits,
    }


# ============== Admin Tenant Management ==============

@router.get("/tenant/{tenant_id}/balance", response_model=BalanceResponse)
async def get_tenant_balance(
    tenant_id: str,
    current_user: CurrentUser = Depends(get_current_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Get credit balance for a specific tenant. (Superadmin only)"""
    from app.models.tenant import Tenant
    from app.core.credit_config import credit_rates
    
    tenant = await db.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    balance = await credit_service.get_balance(db, tenant_id)
    
    return BalanceResponse(
        tenant_id=tenant_id,
        balance=float(balance),
        credit_limit=float(tenant.credit_limit),
        is_low=balance < credit_rates.LOW_BALANCE_WARNING,
    )


@router.get("/tenant/{tenant_id}/usage", response_model=UsageSummaryResponse)
async def get_tenant_usage(
    tenant_id: str,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: CurrentUser = Depends(get_current_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Get usage summary for a specific tenant. (Superadmin only)"""
    summary = await credit_service.get_usage_summary(
        db=db,
        tenant_id=tenant_id,
        start_date=start_date,
        end_date=end_date,
    )
    
    return UsageSummaryResponse(**summary)
```

---

## Step 4: Real-time Credit Tracking in Agent

Update the voice agent to track usage in real-time. Create `src/agent/utils/usage_tracker.py`:

```python
# src/agent/utils/usage_tracker.py
import asyncio
import httpx
from typing import Optional
from dataclasses import dataclass, field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class UsageMetrics:
    """Track usage metrics for a single call."""
    call_id: str
    tenant_id: str
    started_at: datetime = field(default_factory=datetime.utcnow)
    
    # STT metrics
    stt_seconds: float = 0.0
    
    # TTS metrics
    tts_characters: int = 0
    
    # LLM metrics
    llm_input_tokens: int = 0
    llm_output_tokens: int = 0
    
    # RAG metrics
    rag_queries: int = 0
    
    def add_stt(self, seconds: float):
        """Add STT usage."""
        self.stt_seconds += seconds
    
    def add_tts(self, text: str):
        """Add TTS usage."""
        self.tts_characters += len(text)
    
    def add_llm(self, input_tokens: int, output_tokens: int):
        """Add LLM usage."""
        self.llm_input_tokens += input_tokens
        self.llm_output_tokens += output_tokens
    
    def add_rag_query(self):
        """Add RAG query."""
        self.rag_queries += 1
    
    def to_dict(self):
        return {
            "call_id": self.call_id,
            "tenant_id": self.tenant_id,
            "stt_seconds": self.stt_seconds,
            "tts_characters": self.tts_characters,
            "llm_input_tokens": self.llm_input_tokens,
            "llm_output_tokens": self.llm_output_tokens,
            "rag_queries": self.rag_queries,
        }


class UsageTracker:
    """
    Tracks and reports usage for billing.
    Reports usage periodically and on call end.
    """
    
    def __init__(
        self, 
        backend_url: str,
        api_key: str,
        report_interval: float = 30.0,  # Report every 30 seconds
    ):
        self.backend_url = backend_url.rstrip("/")
        self.api_key = api_key
        self.report_interval = report_interval
        self._metrics: dict[str, UsageMetrics] = {}
        self._report_task: Optional[asyncio.Task] = None
    
    def start_tracking(self, call_id: str, tenant_id: str) -> UsageMetrics:
        """Start tracking a new call."""
        metrics = UsageMetrics(call_id=call_id, tenant_id=tenant_id)
        self._metrics[call_id] = metrics
        
        # Start periodic reporting if not already running
        if self._report_task is None:
            self._report_task = asyncio.create_task(self._periodic_report())
        
        logger.info(f"Started tracking call {call_id} for tenant {tenant_id}")
        return metrics
    
    def get_metrics(self, call_id: str) -> Optional[UsageMetrics]:
        """Get metrics for a call."""
        return self._metrics.get(call_id)
    
    async def stop_tracking(self, call_id: str) -> Optional[UsageMetrics]:
        """Stop tracking and report final metrics."""
        metrics = self._metrics.pop(call_id, None)
        if metrics:
            await self._report_metrics(metrics, final=True)
            logger.info(f"Stopped tracking call {call_id}. Final metrics: {metrics.to_dict()}")
        
        # Stop periodic reporting if no more calls
        if not self._metrics and self._report_task:
            self._report_task.cancel()
            self._report_task = None
        
        return metrics
    
    async def _periodic_report(self):
        """Periodically report usage to backend."""
        while True:
            try:
                await asyncio.sleep(self.report_interval)
                
                for call_id, metrics in list(self._metrics.items()):
                    await self._report_metrics(metrics, final=False)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic report: {e}")
    
    async def _report_metrics(self, metrics: UsageMetrics, final: bool = False):
        """Report metrics to backend."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.backend_url}/api/internal/usage/report",
                    json={
                        **metrics.to_dict(),
                        "final": final,
                    },
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                )
                response.raise_for_status()
        except Exception as e:
            logger.error(f"Failed to report metrics for call {metrics.call_id}: {e}")


# Global tracker instance
_tracker: Optional[UsageTracker] = None


def get_usage_tracker() -> UsageTracker:
    """Get the global usage tracker instance."""
    global _tracker
    if _tracker is None:
        from config import settings
        _tracker = UsageTracker(
            backend_url=settings.BACKEND_URL,
            api_key=settings.INTERNAL_API_KEY,
        )
    return _tracker
```

---

## Step 5: Internal Usage Endpoint

Create `api/routes/internal.py`:

```python
# src/backend/app/api/routes/internal.py
from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.credit_service import credit_service
from app.core.config import settings

router = APIRouter(prefix="/internal", tags=["Internal"])


class UsageReportRequest(BaseModel):
    call_id: str
    tenant_id: str
    stt_seconds: float = 0.0
    tts_characters: int = 0
    llm_input_tokens: int = 0
    llm_output_tokens: int = 0
    rag_queries: int = 0
    final: bool = False


async def verify_internal_auth(
    authorization: str = Header(...),
):
    """Verify internal API authentication."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    token = authorization[7:]
    if token != settings.INTERNAL_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid internal API key")


@router.post("/usage/report")
async def report_usage(
    request: UsageReportRequest,
    _auth: None = Depends(verify_internal_auth),
    db: AsyncSession = Depends(get_db),
):
    """
    Report usage from voice agent.
    Called periodically during calls and once at the end.
    """
    if request.final:
        # Deduct credits for AI usage
        await credit_service.deduct_ai_credits(
            db=db,
            tenant_id=request.tenant_id,
            call_id=request.call_id,
            stt_seconds=request.stt_seconds,
            tts_characters=request.tts_characters,
            llm_input_tokens=request.llm_input_tokens,
            llm_output_tokens=request.llm_output_tokens,
            rag_queries=request.rag_queries,
        )
        
        return {"status": "processed", "final": True}
    
    # For non-final reports, just acknowledge
    # (Could store intermediate usage if needed)
    return {"status": "acknowledged", "final": False}


@router.get("/credits/check/{tenant_id}")
async def check_tenant_credits(
    tenant_id: str,
    _auth: None = Depends(verify_internal_auth),
    db: AsyncSession = Depends(get_db),
):
    """
    Quick credit check for voice agent.
    Returns whether tenant can continue call.
    """
    has_credits = await credit_service.check_credits(db, tenant_id)
    balance = await credit_service.get_balance(db, tenant_id)
    
    return {
        "tenant_id": tenant_id,
        "has_credits": has_credits,
        "balance": float(balance),
        "can_continue": has_credits,
    }
```

---

## Step 6: Low Balance Alerts

Create `services/alert_service.py`:

```python
# src/backend/app/services/alert_service.py
import asyncio
import httpx
from typing import Optional
import logging
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.tenant import Tenant
from app.core.credit_config import credit_rates
from app.core.config import settings

logger = logging.getLogger(__name__)


class AlertService:
    """Service for sending alerts."""
    
    async def check_and_alert_low_balance(
        self,
        db: AsyncSession,
        tenant_id: str,
    ):
        """Check if tenant has low balance and send alert."""
        tenant = await db.get(Tenant, tenant_id)
        if not tenant:
            return
        
        balance = tenant.credit_balance
        
        if balance < float(credit_rates.LOW_BALANCE_WARNING):
            await self._send_low_balance_alert(tenant)
    
    async def _send_low_balance_alert(self, tenant: Tenant):
        """Send low balance alert to tenant admin."""
        logger.warning(
            f"Low balance alert for tenant {tenant.id}: "
            f"${tenant.credit_balance:.2f}"
        )
        
        # Send email notification
        if tenant.admin_email:
            await self._send_email(
                to=tenant.admin_email,
                subject=f"Low Credit Balance - {settings.PLATFORM_NAME}",
                body=f"""
                Hi,
                
                Your credit balance is running low: ${tenant.credit_balance:.2f}
                
                Please add more credits to ensure uninterrupted service.
                
                Log in to your dashboard to add credits:
                {settings.FRONTEND_URL}/dashboard/credits
                
                Regards,
                {settings.PLATFORM_NAME}
                """,
            )
    
    async def _send_email(self, to: str, subject: str, body: str):
        """Send email notification."""
        # Implement with your email provider (SendGrid, SES, etc.)
        # This is a placeholder
        logger.info(f"Would send email to {to}: {subject}")
    
    async def send_webhook(
        self,
        tenant: Tenant,
        event_type: str,
        data: dict,
    ):
        """Send webhook to tenant's configured URL."""
        if not tenant.configs or not tenant.configs.webhook_url:
            return
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                await client.post(
                    tenant.configs.webhook_url,
                    json={
                        "event": event_type,
                        "timestamp": datetime.utcnow().isoformat(),
                        "data": data,
                    },
                )
        except Exception as e:
            logger.error(f"Webhook failed for tenant {tenant.id}: {e}")


alert_service = AlertService()
```

---

## Verification Checklist

- [ ] Credit configuration loaded
- [ ] Add credits working (superadmin)
- [ ] Balance check working
- [ ] Usage tracking in agent
- [ ] Deductions calculated correctly
- [ ] Transaction history recorded
- [ ] Usage summary accurate
- [ ] Low balance alerts configured

---

## Credit Rate Reference

### Communication & AI Services

| Resource | Unit | Default Rate |
|----------|------|--------------|
| Inbound Call | Per minute | 1.0 credit |
| Outbound Call | Per minute | 2.0 credits |
| STT (Deepgram) | Per minute | 0.5 credits |
| TTS (Cartesia) | Per 1K chars | 0.05 credits |
| LLM Input | Per 1K tokens | 0.05 credits |
| LLM Output | Per 1K tokens | 0.15 credits |
| RAG Query | Per query | 0.02 credits |
| KB Storage | Per GB/month | 0.1 credits |

### Action Tools (Write Operations)

These are charged **in addition to** the AI/call usage because they perform external integrations and have higher operational costs.

| Action Tool | Per Execution | Description |
|------------|---------------|-------------|
| Book Appointment | 0.25 credits | Calendar booking (Google/Outlook) |
| Send Email | 0.10 credits | Confirmation or notification email |
| Create Ticket | 0.05 credits | ServiceNow or helpdesk ticket |
| Guest Check-in | 0.15 credits | Hotel PMS integration |

### Why Action Tools Cost More

1. **External API Costs**: Each action may involve paid APIs (calendar, email services)
2. **Liability**: Write operations have higher risk (can't be easily undone)
3. **Value Delivered**: These complete actual business transactions
4. **Operational Overhead**: Requires maintaining integrations and handling failures

### Credit Check Flow

Before executing any action tool, the system verifies credits:

```
Agent calls book_appointment
        │
        ▼
┌──────────────────────┐
│ Credit Verification  │
│ (check balance ≥     │
│  action cost)        │
└──────────┬───────────┘
           │
     ┌─────┴─────┐
     │           │
     ▼           ▼
 [Pass]      [Fail]
     │           │
     ▼           ▼
Execute     Return error
 tool       "Insufficient
            credits, transfer
            to human"
```

---

## Next Step

Proceed to: `.claude/skills/10-DEPLOYMENT.md`
