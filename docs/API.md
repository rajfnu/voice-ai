# Voice AI Platform - API Reference

## Overview

Base URL: `https://your-domain.com/api`

All requests require authentication via JWT token or API key.

---

## Authentication

### Login
```http
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### Using Tokens
```http
GET /api/endpoint
Authorization: Bearer <access_token>
```

### Using API Keys
```http
GET /api/endpoint
X-API-Key: vai_xxxxxxxxxxxxx
```

---

## Tenants

### List Tenants (Superadmin)
```http
GET /tenants
```

### Create Tenant (Superadmin)
```http
POST /tenants
Content-Type: application/json

{
  "name": "Acme Healthcare",
  "slug": "acme-healthcare",
  "admin_email": "admin@acme.com",
  "inbound_calls_enabled": true,
  "outbound_calls_enabled": false,
  "credit_limit": 1000
}
```

### Get Tenant
```http
GET /tenants/{tenant_id}
```

### Update Tenant
```http
PUT /tenants/{tenant_id}
Content-Type: application/json

{
  "name": "Acme Healthcare Updated",
  "settings": {
    "timezone": "America/New_York"
  }
}
```

---

## Users

### List Users
```http
GET /users
```

### Create User
```http
POST /users
Content-Type: application/json

{
  "email": "newuser@example.com",
  "password": "securepassword",
  "full_name": "New User",
  "role_names": ["tenant_user"]
}
```

### Get Current User
```http
GET /auth/me
```

---

## Credits

### Get Balance
```http
GET /credits/balance
```

**Response:**
```json
{
  "tenant_id": "uuid",
  "balance": 850.50,
  "credit_limit": 1000,
  "is_low": false
}
```

### Add Credits (Superadmin)
```http
POST /credits/add
Content-Type: application/json

{
  "tenant_id": "uuid",
  "amount": 100,
  "description": "Monthly top-up"
}
```

### Get Usage Summary
```http
GET /credits/usage?start_date=2024-01-01&end_date=2024-01-31
```

**Response:**
```json
{
  "period": {
    "start": "2024-01-01T00:00:00Z",
    "end": "2024-01-31T23:59:59Z"
  },
  "current_balance": 850.50,
  "usage_by_type": {
    "call_usage": {"count": 150, "total_credits": 120.50},
    "stt_usage": {"count": 150, "total_credits": 15.25},
    "llm_usage": {"count": 150, "total_credits": 8.75},
    "tts_usage": {"count": 150, "total_credits": 3.50},
    "rag_usage": {"count": 45, "total_credits": 0.90}
  },
  "calls": {
    "total": 150,
    "total_duration_seconds": 7500
  },
  "total_credits_used": 148.90
}
```

### Get Transactions
```http
GET /credits/transactions?limit=50&offset=0&type=call_usage
```

---

## Call Logs

### List Calls
```http
GET /calls?limit=50&offset=0&direction=inbound&status=completed
```

**Response:**
```json
{
  "items": [
    {
      "id": "uuid",
      "direction": "inbound",
      "from_number": "+1234567890",
      "to_number": "+0987654321",
      "status": "completed",
      "duration_seconds": 180,
      "credits_used": 3.50,
      "started_at": "2024-01-15T10:30:00Z",
      "ended_at": "2024-01-15T10:33:00Z",
      "transcript": "...",
      "summary": "Patient called to schedule appointment...",
      "outcome": "appointment_booked"
    }
  ],
  "total": 150,
  "limit": 50,
  "offset": 0
}
```

### Get Call Details
```http
GET /calls/{call_id}
```

### Export Calls
```http
GET /calls/export?start_date=2024-01-01&end_date=2024-01-31&format=csv
```

---

## Knowledge Base

### Query KB
```http
POST /kb/query
Content-Type: application/json

{
  "query": "What are the check-in hours?",
  "mode": "mix"
}
```

**Response:**
```json
{
  "response": "Check-in is available from 3:00 PM. Early check-in may be available upon request.",
  "sources": [
    {
      "document": "hotel-policies.pdf",
      "chunk": "...",
      "score": 0.92
    }
  ]
}
```

### Add Text to KB
```http
POST /kb/documents/text
Content-Type: application/json

{
  "text": "New policy: All guests must present ID at check-in.",
  "metadata": {
    "source": "admin",
    "category": "policies"
  }
}
```

### List Documents
```http
GET /kb/documents
```

---

## Tenant Configuration

### Get Config
```http
GET /config
```

**Response:**
```json
{
  "agent_name": "Alex",
  "system_prompt": "You are Alex, a helpful...",
  "first_message": "Hi, this is Alex...",
  "voice_id": "a0e99841-438c-4a64-b679-ae501e7d6091",
  "language": "en-US",
  "llm_provider": "openai",
  "llm_model": "gpt-4o",
  "tools_enabled": ["query_kb", "book_appointment", "create_ticket"],
  "phone_numbers": ["+1234567890"],
  "business_hours": {
    "monday": {"start": "09:00", "end": "17:00"},
    "tuesday": {"start": "09:00", "end": "17:00"}
  }
}
```

### Update Config
```http
PUT /config
Content-Type: application/json

{
  "agent_name": "Sam",
  "system_prompt": "You are Sam, a concierge...",
  "tools_enabled": ["query_kb", "guest_checkin", "create_ticket"]
}
```

---

## LiveKit Integration

### Get Room Token
```http
POST /livekit/token
Content-Type: application/json

{
  "room_name": "test-room",
  "participant_name": "John Doe"
}
```

**Response:**
```json
{
  "token": "eyJ...",
  "room_name": "test-room",
  "url": "wss://livekit.yourdomain.com"
}
```

### List Rooms
```http
GET /livekit/rooms
```

---

## Phone Numbers

### List Numbers
```http
GET /phone-numbers
```

**Response:**
```json
{
  "items": [
    {
      "id": "uuid",
      "number": "+1234567890",
      "display_name": "Main Line",
      "status": "warm",
      "max_calls_per_day": 100,
      "calls_today": 45,
      "is_active": true,
      "can_receive_calls": true,
      "can_make_calls": true
    }
  ]
}
```

### Get Number Stats
```http
GET /phone-numbers/stats
```

---

## Outbound Campaigns

### Start Campaign
```http
POST /campaigns
Content-Type: application/json

{
  "name": "Follow-up Calls",
  "leads": [
    {"phone": "+1111111111", "name": "John Doe", "company": "Acme"},
    {"phone": "+2222222222", "name": "Jane Smith", "company": "Beta"}
  ],
  "agent_config": {
    "caller_id": "+1234567890",
    "script": "appointment_followup"
  },
  "max_concurrent_calls": 3,
  "schedule": {
    "start_time": "09:00",
    "end_time": "17:00",
    "timezone": "America/New_York"
  }
}
```

### Get Campaign Status
```http
GET /campaigns/{campaign_id}
```

### Stop Campaign
```http
POST /campaigns/{campaign_id}/stop
```

---

## Webhooks

### Configure Webhook
```http
PUT /config/webhook
Content-Type: application/json

{
  "url": "https://your-app.com/webhooks/voice-ai",
  "events": ["call.started", "call.ended", "credit.low"],
  "secret": "your-webhook-secret"
}
```

### Webhook Events

#### call.started
```json
{
  "event": "call.started",
  "timestamp": "2024-01-15T10:30:00Z",
  "data": {
    "call_id": "uuid",
    "direction": "inbound",
    "from_number": "+1234567890",
    "to_number": "+0987654321"
  }
}
```

#### call.ended
```json
{
  "event": "call.ended",
  "timestamp": "2024-01-15T10:33:00Z",
  "data": {
    "call_id": "uuid",
    "duration_seconds": 180,
    "outcome": "appointment_booked",
    "summary": "Patient booked appointment for..."
  }
}
```

#### credit.low
```json
{
  "event": "credit.low",
  "timestamp": "2024-01-15T10:33:00Z",
  "data": {
    "balance": 8.50,
    "threshold": 10.00
  }
}
```

---

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Invalid request body"
}
```

### 401 Unauthorized
```json
{
  "detail": "Invalid or expired token"
}
```

### 403 Forbidden
```json
{
  "detail": "Permission denied: credits:manage required"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 422 Validation Error
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error.email"
    }
  ]
}
```

### 429 Rate Limited
```json
{
  "detail": "Rate limit exceeded. Try again in 60 seconds."
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

---

## Rate Limits

| Endpoint | Limit |
|----------|-------|
| `/auth/login` | 5 requests/minute |
| `/auth/*` | 30 requests/minute |
| `/api/*` | 60 requests/minute |
| `/kb/query` | 30 requests/minute |
| `/campaigns` | 10 requests/minute |

---

## SDKs

### Python
```python
from voice_ai_sdk import VoiceAIClient

client = VoiceAIClient(
    api_url="https://your-domain.com/api",
    api_key="vai_xxxxx"
)

# Query knowledge base
result = client.kb.query("What are the business hours?")
print(result.response)

# Get credit balance
balance = client.credits.get_balance()
print(f"Balance: {balance.balance}")
```

### JavaScript
```javascript
import { VoiceAIClient } from '@voice-ai/sdk';

const client = new VoiceAIClient({
  apiUrl: 'https://your-domain.com/api',
  apiKey: 'vai_xxxxx'
});

// Query knowledge base
const result = await client.kb.query('What are the business hours?');
console.log(result.response);

// Get credit balance
const balance = await client.credits.getBalance();
console.log(`Balance: ${balance.balance}`);
```
