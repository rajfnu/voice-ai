# Skill 02: Authentication & RBAC

## Objective
Implement JWT-based authentication with multi-tenant RBAC (Role-Based Access Control) for the Voice AI Platform.

---

## Authentication Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Client    │────▶│  /auth/     │────▶│  Validate   │────▶│  Generate   │
│  (Login)    │     │   login     │     │  Password   │     │    JWT      │
└─────────────┘     └─────────────┘     └─────────────┘     └──────┬──────┘
                                                                   │
                                                                   ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Client    │────▶│  API Call   │────▶│  Verify     │────▶│   Check     │
│  (Request)  │     │  + Bearer   │     │    JWT      │     │   RBAC      │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

---

## Step 1: Configuration

Create `core/config.py`:

```python
# src/backend/app/core/config.py
from pydantic_settings import BaseSettings
from typing import Optional, List
import os


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Voice AI Platform"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    
    # Database
    DATABASE_URL: str
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # API Keys
    API_KEY_PREFIX: str = "vai_"
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
```

---

## Step 2: Password Hashing

Create `core/security.py`:

```python
# src/backend/app/core/security.py
from datetime import datetime, timedelta
from typing import Optional, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
import secrets
import hashlib

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ============== Password ==============

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


# ============== JWT Tokens ==============

def create_access_token(
    subject: str,
    tenant_id: Optional[str] = None,
    is_superadmin: bool = False,
    roles: list[str] = None,
    permissions: list[str] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create JWT access token with embedded claims."""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {
        "sub": subject,  # user_id
        "exp": expire,
        "type": "access",
        "tenant_id": tenant_id,
        "is_superadmin": is_superadmin,
        "roles": roles or [],
        "permissions": permissions or [],
    }
    
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(subject: str) -> str:
    """Create JWT refresh token."""
    expire = datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode = {
        "sub": subject,
        "exp": expire,
        "type": "refresh",
    }
    
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    """Decode and validate JWT token."""
    try:
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET_KEY, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        return None


# ============== API Keys ==============

def generate_api_key() -> tuple[str, str, str]:
    """
    Generate a new API key.
    Returns: (full_key, key_prefix, key_hash)
    """
    # Generate random key
    random_part = secrets.token_urlsafe(32)
    full_key = f"{settings.API_KEY_PREFIX}{random_part}"
    
    # Get prefix for identification
    key_prefix = full_key[:12]
    
    # Hash the full key for storage
    key_hash = hashlib.sha256(full_key.encode()).hexdigest()
    
    return full_key, key_prefix, key_hash


def verify_api_key(api_key: str, stored_hash: str) -> bool:
    """Verify an API key against its stored hash."""
    computed_hash = hashlib.sha256(api_key.encode()).hexdigest()
    return secrets.compare_digest(computed_hash, stored_hash)
```

---

## Step 3: Auth Schemas

Create `schemas/auth.py`:

```python
# src/backend/app/schemas/auth.py
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from uuid import UUID


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenPayload(BaseModel):
    sub: str  # user_id
    exp: int
    type: str
    tenant_id: Optional[str] = None
    is_superadmin: bool = False
    roles: List[str] = []
    permissions: List[str] = []


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class ResetPasswordRequest(BaseModel):
    email: EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    tenant_id: Optional[UUID] = None
    role_names: List[str] = ["tenant_user"]


class UserResponse(BaseModel):
    id: UUID
    email: str
    full_name: Optional[str]
    tenant_id: Optional[UUID]
    is_active: bool
    is_superadmin: bool
    roles: List[str]
    
    class Config:
        from_attributes = True


class APIKeyCreate(BaseModel):
    name: str
    scopes: List[str] = []
    expires_in_days: Optional[int] = None


class APIKeyResponse(BaseModel):
    id: UUID
    name: str
    key_prefix: str
    scopes: List[str]
    is_active: bool
    expires_at: Optional[str]
    
    class Config:
        from_attributes = True


class APIKeyCreated(APIKeyResponse):
    """Returned only on creation - includes the full key."""
    api_key: str  # Only shown once!
```

---

## Step 4: Auth Dependencies

Create `api/deps.py`:

```python
# src/backend/app/api/deps.py
from typing import Optional, List
from fastapi import Depends, HTTPException, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.core.security import decode_token, verify_api_key
from app.models.user import User, Role
from app.models.tenant import Tenant
from app.models.api_key import APIKey
from app.schemas.auth import TokenPayload

# Security schemes
bearer_scheme = HTTPBearer(auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


class CurrentUser:
    """Container for current user context."""
    def __init__(
        self,
        user: User,
        tenant: Optional[Tenant],
        permissions: List[str],
        is_api_key: bool = False,
    ):
        self.user = user
        self.tenant = tenant
        self.permissions = permissions
        self.is_api_key = is_api_key
        self.is_superadmin = user.is_superadmin if user else False
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has a specific permission."""
        if self.is_superadmin or "*" in self.permissions:
            return True
        return permission in self.permissions
    
    def require_permission(self, permission: str):
        """Raise 403 if user doesn't have permission."""
        if not self.has_permission(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {permission} required"
            )


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    bearer: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
    api_key: Optional[str] = Security(api_key_header),
) -> CurrentUser:
    """
    Get current authenticated user from JWT token or API key.
    """
    user = None
    tenant = None
    permissions = []
    is_api_key_auth = False
    
    # Try JWT token first
    if bearer and bearer.credentials:
        payload = decode_token(bearer.credentials)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        token_data = TokenPayload(**payload)
        
        if token_data.type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )
        
        # Get user from database
        result = await db.execute(
            select(User)
            .options(selectinload(User.roles), selectinload(User.tenant))
            .where(User.id == token_data.sub)
        )
        user = result.scalar_one_or_none()
        
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
            )
        
        tenant = user.tenant
        
        # Collect permissions from roles
        for role in user.roles:
            permissions.extend(role.permissions or [])
        permissions = list(set(permissions))  # Dedupe
    
    # Try API key if no JWT
    elif api_key:
        is_api_key_auth = True
        
        # Find API key by prefix
        key_prefix = api_key[:12] if len(api_key) >= 12 else api_key
        
        result = await db.execute(
            select(APIKey)
            .options(selectinload(APIKey.tenant), selectinload(APIKey.user))
            .where(APIKey.key_prefix == key_prefix)
            .where(APIKey.is_active == True)
        )
        api_key_record = result.scalar_one_or_none()
        
        if not api_key_record or not verify_api_key(api_key, api_key_record.key_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
            )
        
        # Check expiration
        if api_key_record.expires_at and api_key_record.expires_at < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key expired",
            )
        
        user = api_key_record.user
        tenant = api_key_record.tenant
        permissions = api_key_record.scopes or []
        
        # Update last used
        api_key_record.last_used_at = datetime.utcnow()
        await db.commit()
    
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return CurrentUser(
        user=user,
        tenant=tenant,
        permissions=permissions,
        is_api_key=is_api_key_auth,
    )


async def get_current_active_user(
    current_user: CurrentUser = Depends(get_current_user),
) -> CurrentUser:
    """Ensure user is active."""
    if not current_user.user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user


async def get_current_superadmin(
    current_user: CurrentUser = Depends(get_current_active_user),
) -> CurrentUser:
    """Require superadmin role."""
    if not current_user.is_superadmin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superadmin access required"
        )
    return current_user


def require_permission(permission: str):
    """Dependency factory to require specific permission."""
    async def check_permission(
        current_user: CurrentUser = Depends(get_current_active_user),
    ) -> CurrentUser:
        current_user.require_permission(permission)
        return current_user
    return check_permission


def require_tenant():
    """Require user to belong to a tenant."""
    async def check_tenant(
        current_user: CurrentUser = Depends(get_current_active_user),
    ) -> CurrentUser:
        if not current_user.tenant and not current_user.is_superadmin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tenant membership required"
            )
        return current_user
    return check_tenant
```

---

## Step 5: Auth Service

Create `services/auth_service.py`:

```python
# src/backend/app/services/auth_service.py
from typing import Optional, List, Tuple
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.user import User, Role
from app.models.tenant import Tenant
from app.models.api_key import APIKey
from app.schemas.auth import UserCreate, TokenResponse, APIKeyCreate
from app.core.security import (
    verify_password, 
    get_password_hash, 
    create_access_token, 
    create_refresh_token,
    generate_api_key,
)
from app.core.config import settings


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user by email and password."""
        result = await self.db.execute(
            select(User)
            .options(selectinload(User.roles), selectinload(User.tenant))
            .where(User.email == email)
        )
        user = result.scalar_one_or_none()
        
        if not user or not verify_password(password, user.password_hash):
            return None
        
        return user
    
    async def create_tokens(self, user: User) -> TokenResponse:
        """Create access and refresh tokens for user."""
        # Collect permissions
        permissions = []
        role_names = []
        for role in user.roles:
            permissions.extend(role.permissions or [])
            role_names.append(role.name)
        
        permissions = list(set(permissions))
        
        access_token = create_access_token(
            subject=str(user.id),
            tenant_id=str(user.tenant_id) if user.tenant_id else None,
            is_superadmin=user.is_superadmin,
            roles=role_names,
            permissions=permissions,
        )
        
        refresh_token = create_refresh_token(subject=str(user.id))
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
    
    async def create_user(
        self, 
        user_data: UserCreate,
        created_by_superadmin: bool = False,
    ) -> User:
        """Create a new user."""
        # Check if email exists
        existing = await self.db.execute(
            select(User).where(User.email == user_data.email)
        )
        if existing.scalar_one_or_none():
            raise ValueError("Email already registered")
        
        # Get roles
        roles = []
        for role_name in user_data.role_names:
            result = await self.db.execute(
                select(Role).where(Role.name == role_name)
            )
            role = result.scalar_one_or_none()
            if role:
                roles.append(role)
        
        # Create user
        user = User(
            email=user_data.email,
            password_hash=get_password_hash(user_data.password),
            full_name=user_data.full_name,
            tenant_id=user_data.tenant_id,
            is_superadmin=False,
            roles=roles,
        )
        
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        
        return user
    
    async def create_api_key(
        self,
        tenant_id: str,
        user_id: str,
        data: APIKeyCreate,
    ) -> Tuple[APIKey, str]:
        """Create a new API key. Returns (APIKey, full_key)."""
        full_key, key_prefix, key_hash = generate_api_key()
        
        expires_at = None
        if data.expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=data.expires_in_days)
        
        api_key = APIKey(
            tenant_id=tenant_id,
            user_id=user_id,
            name=data.name,
            key_prefix=key_prefix,
            key_hash=key_hash,
            scopes=data.scopes,
            expires_at=expires_at,
        )
        
        self.db.add(api_key)
        await self.db.commit()
        await self.db.refresh(api_key)
        
        return api_key, full_key
    
    async def change_password(
        self, 
        user: User, 
        current_password: str, 
        new_password: str
    ) -> bool:
        """Change user password."""
        if not verify_password(current_password, user.password_hash):
            return False
        
        user.password_hash = get_password_hash(new_password)
        await self.db.commit()
        return True
```

---

## Step 6: Auth API Routes

Create `api/routes/auth.py`:

```python
# src/backend/app/api/routes/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.auth_service import AuthService
from app.schemas.auth import (
    LoginRequest, 
    TokenResponse, 
    RefreshTokenRequest,
    ChangePasswordRequest,
    UserCreate,
    UserResponse,
    APIKeyCreate,
    APIKeyCreated,
)
from app.api.deps import get_current_user, get_current_active_user, CurrentUser
from app.core.security import decode_token, create_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate user and return tokens."""
    service = AuthService(db)
    user = await service.authenticate_user(request.email, request.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )
    
    return await service.create_tokens(user)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """Refresh access token using refresh token."""
    payload = decode_token(request.refresh_token)
    
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )
    
    # Get user and generate new tokens
    service = AuthService(db)
    user = await db.get(User, payload["sub"])
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    
    return await service.create_tokens(user)


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: CurrentUser = Depends(get_current_active_user),
):
    """Get current authenticated user info."""
    user = current_user.user
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        tenant_id=user.tenant_id,
        is_active=user.is_active,
        is_superadmin=user.is_superadmin,
        roles=[role.name for role in user.roles],
    )


@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    current_user: CurrentUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Change current user's password."""
    service = AuthService(db)
    success = await service.change_password(
        current_user.user,
        request.current_password,
        request.new_password,
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )
    
    return {"message": "Password changed successfully"}


@router.post("/api-keys", response_model=APIKeyCreated)
async def create_api_key(
    request: APIKeyCreate,
    current_user: CurrentUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new API key for the current tenant."""
    current_user.require_permission("api_keys:write")
    
    if not current_user.tenant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Must belong to a tenant to create API keys",
        )
    
    service = AuthService(db)
    api_key, full_key = await service.create_api_key(
        tenant_id=str(current_user.tenant.id),
        user_id=str(current_user.user.id),
        data=request,
    )
    
    return APIKeyCreated(
        id=api_key.id,
        name=api_key.name,
        key_prefix=api_key.key_prefix,
        scopes=api_key.scopes,
        is_active=api_key.is_active,
        expires_at=api_key.expires_at.isoformat() if api_key.expires_at else None,
        api_key=full_key,  # Only returned on creation!
    )
```

---

## Step 7: Create Superadmin Script

Create `scripts/create_superadmin.py`:

```python
# src/backend/scripts/create_superadmin.py
import asyncio
import sys
from getpass import getpass
from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.user import User, Role
from app.core.security import get_password_hash


async def create_superadmin():
    email = input("Enter superadmin email: ").strip()
    password = getpass("Enter password: ")
    password_confirm = getpass("Confirm password: ")
    
    if password != password_confirm:
        print("❌ Passwords do not match")
        sys.exit(1)
    
    full_name = input("Enter full name: ").strip()
    
    async with AsyncSessionLocal() as db:
        # Check if email exists
        existing = await db.execute(
            select(User).where(User.email == email)
        )
        if existing.scalar_one_or_none():
            print("❌ Email already registered")
            sys.exit(1)
        
        # Get super_admin role
        result = await db.execute(
            select(Role).where(Role.name == "super_admin")
        )
        role = result.scalar_one_or_none()
        
        if not role:
            print("❌ super_admin role not found. Run seed_roles.py first.")
            sys.exit(1)
        
        # Create user
        user = User(
            email=email,
            password_hash=get_password_hash(password),
            full_name=full_name,
            is_superadmin=True,
            is_active=True,
            roles=[role],
        )
        
        db.add(user)
        await db.commit()
        
        print(f"✅ Superadmin created: {email}")


if __name__ == "__main__":
    asyncio.run(create_superadmin())
```

---

## Permission Reference

| Permission | Description |
|------------|-------------|
| `*` | All permissions (superadmin only) |
| `tenants:read` | View tenant info |
| `tenants:write` | Create/update tenants |
| `tenants:delete` | Delete tenants |
| `users:read` | View users |
| `users:write` | Create/update users |
| `users:delete` | Delete users |
| `calls:read` | View call logs |
| `calls:export` | Export call data |
| `kb:read` | View knowledge base |
| `kb:write` | Add/update KB documents |
| `kb:delete` | Delete KB documents |
| `kb:query` | Query knowledge base (API) |
| `credits:read` | View credit balance |
| `credits:manage` | Add/remove credits |
| `config:read` | View tenant config |
| `config:write` | Update tenant config |
| `api_keys:write` | Create API keys |
| `reports:read` | View reports |

---

## Testing Auth

```bash
# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "password123"}'

# Use token
curl http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer <access_token>"

# Use API key
curl http://localhost:8000/api/calls \
  -H "X-API-Key: vai_xxxxxxxxxxxxx"
```

---

## Next Step

Proceed to: `.claude/skills/03-LIGHTRAG-SETUP.md`
