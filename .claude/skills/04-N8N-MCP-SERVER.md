# Skill 04: n8n MCP Server (Tool Layer)

## Objective
Set up n8n as the MCP (Model Context Protocol) server that provides tools for the voice agent to call during conversations.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              n8n MCP Server                                      │
│                                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────┐     │
│  │                       MCP Server Trigger                                │     │
│  │                   URL: /webhook/voice-agent-mcp                         │     │
│  └────────────────────────────────┬───────────────────────────────────────┘     │
│                                   │                                              │
│                    ┌──────────────┼──────────────┐                              │
│                    │              │              │                              │
│                    ▼              ▼              ▼                              │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐                   │
│  │   query_kb      │ │  book_appt      │ │ create_ticket   │                   │
│  │   (LightRAG)    │ │  (Calendar)     │ │ (ServiceNow)    │                   │
│  └────────┬────────┘ └────────┬────────┘ └────────┬────────┘                   │
│           │                   │                   │                            │
│           ▼                   ▼                   ▼                            │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐                   │
│  │   LightRAG      │ │ Google Calendar │ │   ServiceNow    │                   │
│  │   /query        │ │ Create Event    │ │   REST API      │                   │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘                   │
│                                                                                  │
│  Additional Tools:                                                               │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ ┌───────────────┐ │
│  │ check_avail     │ │ get_customer    │ │ escalate_human  │ │ log_call      │ │
│  │ (Calendar)      │ │ (CRM/PMS)       │ │ (Transfer)      │ │ (Analytics)   │ │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘ └───────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Deployment Options

n8n can be deployed locally (Docker) or in the cloud. Choose based on your needs:

| Option | Best For | Pros | Cons |
|--------|----------|------|------|
| **Local (Docker)** | Development, testing | Full control, easy debugging | Requires local resources |
| **n8n Cloud** | Production, teams | Managed infrastructure, updates, support | Monthly subscription |
| **Self-hosted Cloud** | Production, custom needs | Control + scaling | Requires DevOps |

---

## Option A: Local Deployment (Docker)

### A.1 Start n8n Locally

```bash
cd ~/voice-ai-platform

# Create n8n directory
mkdir -p src/n8n-workflows

# Create docker-compose for n8n
cat > docker-compose.n8n.yml << 'EOF'
version: '3.8'
services:
  n8n:
    image: n8nio/n8n:latest
    container_name: voice-ai-n8n
    ports:
      - "5678:5678"
    environment:
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=admin
      - N8N_BASIC_AUTH_PASSWORD=your-n8n-password
      - N8N_HOST=localhost
      - N8N_PORT=5678
      - N8N_PROTOCOL=http
      - WEBHOOK_URL=http://localhost:5678/
      - NODE_ENV=production
      - GENERIC_TIMEZONE=Australia/Sydney
      # Environment variables for workflows
      - LIGHTRAG_URL=http://host.docker.internal:9621
      - LIGHTRAG_API_KEY=${LIGHTRAG_API_KEY}
    volumes:
      - n8n_data:/home/node/.n8n
    extra_hosts:
      - "host.docker.internal:host-gateway"
    restart: unless-stopped

volumes:
  n8n_data:
EOF

# Start n8n
docker compose -f docker-compose.n8n.yml up -d

# Check logs
docker compose -f docker-compose.n8n.yml logs -f
```

---

## Option B: n8n Cloud (Recommended for Production)

### B.1 Sign Up for n8n Cloud

1. Go to https://n8n.io/cloud
2. Create an account (free trial available)
3. Create a new workspace

### B.2 Get Your Cloud URL

After setup, your n8n instance will be available at:
```
https://your-workspace.app.n8n.cloud
```

### B.3 Configure Environment Variables

```bash
# Add to your .env
N8N_URL=https://your-workspace.app.n8n.cloud
N8N_API_KEY=your-n8n-api-key  # From Settings > API
```

### B.4 Advantages of n8n Cloud

- Automatic updates and security patches
- Built-in monitoring and logging
- Team collaboration features
- SSO and advanced security
- No infrastructure management

---

## Option C: Self-Hosted Cloud (AWS/GCP)

### C.1 AWS Deployment

```bash
# Deploy n8n on AWS ECS or EC2

# Using AWS ECS with Fargate
aws ecs create-cluster --cluster-name n8n-cluster

# Create task definition for n8n
# See: https://docs.n8n.io/hosting/server-setups/aws/

# Environment variables for production
N8N_BASIC_AUTH_ACTIVE=true
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=${SECURE_PASSWORD}
WEBHOOK_URL=https://n8n.yourdomain.com/
DB_TYPE=postgresdb
DB_POSTGRESDB_HOST=${RDS_ENDPOINT}
DB_POSTGRESDB_DATABASE=n8n
DB_POSTGRESDB_USER=n8n_user
DB_POSTGRESDB_PASSWORD=${DB_PASSWORD}
```

### C.2 GCP Cloud Run Deployment

```bash
# Deploy n8n on Cloud Run
gcloud run deploy n8n \
  --image n8nio/n8n \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "N8N_BASIC_AUTH_ACTIVE=true"
```

---

## Step 2: Access n8n

**Local:** http://localhost:5678
**Cloud:** https://your-workspace.app.n8n.cloud

1. Login with your credentials
2. Create a new workflow: **Voice Agent MCP**

---

## Step 3: Create MCP Server Trigger

In n8n:

1. Click **+** to add a node
2. Search for **"MCP Server Trigger"**
3. Add it to your workflow
4. Configure the trigger (leave defaults)
5. Note the **Production URL** (will be like `http://localhost:5678/webhook/xxx`)

---

## Step 4: Tool 1 - Query Knowledge Base

### 4.1 Add HTTP Request Node

Connect to MCP Server Trigger:

```yaml
Node: HTTP Request
Name: query_kb

# Configuration
Method: POST
URL: {{ $env.LIGHTRAG_URL }}/query

# Headers (Add manually)
Headers:
  - Name: Accept
    Value: application/json
  - Name: X-API-Key
    Value: {{ $env.LIGHTRAG_API_KEY }}

# Body
Body Content Type: JSON
Body Parameters:
  - Name: query
    Value: {{ $json.query }}  # From MCP input
  - Name: mode
    Value: mix  # Fixed value, NOT from AI
```

### 4.2 Define Tool in MCP Trigger

In the MCP Server Trigger node, add tool definition:

```json
{
  "name": "query_kb",
  "description": "Search the knowledge base to answer questions about the organization, services, policies, or any uploaded documents. Always use this tool when the user asks factual questions.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "The question to search for in the knowledge base"
      }
    },
    "required": ["query"]
  }
}
```

---

## Step 5: Tool 2 - Get Current DateTime

### 5.1 Add Code Node

```yaml
Node: Code
Name: get_datetime

# JavaScript Code
```

```javascript
const now = new Date();
const timezone = $input.first().json.timezone || 'Australia/Sydney';

// Format with timezone
const options = {
  timeZone: timezone,
  year: 'numeric',
  month: 'long',
  day: 'numeric',
  weekday: 'long',
  hour: '2-digit',
  minute: '2-digit',
  hour12: true
};

const formatted = now.toLocaleString('en-AU', options);

return {
  current_datetime: formatted,
  timezone: timezone,
  iso: now.toISOString(),
  unix: Math.floor(now.getTime() / 1000)
};
```

### 5.2 Tool Definition

```json
{
  "name": "get_datetime",
  "description": "Get the current date and time. Use when user asks about the current time or when scheduling appointments.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "timezone": {
        "type": "string",
        "description": "Timezone (e.g., 'Australia/Sydney', 'America/New_York')"
      }
    },
    "required": []
  }
}
```

---

## Step 6: Tool 3 - Book Appointment (Healthcare)

### 6.1 Add Google Calendar Node

```yaml
Node: Google Calendar
Name: book_appointment

# Configuration
Resource: Event
Operation: Create
Calendar: (Select your calendar)

# Event Details
Title: {{ $json.title || 'Appointment' }}
Description: |
  Patient: {{ $json.patient_name }}
  Phone: {{ $json.patient_phone }}
  Reason: {{ $json.reason }}
  
  Booked via Voice AI
Start Time: {{ $json.start_time }}
End Time: {{ $json.end_time }}
```

### 6.2 Tool Definition

```json
{
  "name": "book_appointment",
  "description": "Book a new appointment for the patient. Use after confirming availability and getting patient consent.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "patient_name": {
        "type": "string",
        "description": "Patient's full name"
      },
      "patient_phone": {
        "type": "string",
        "description": "Patient's phone number"
      },
      "reason": {
        "type": "string",
        "description": "Reason for the appointment"
      },
      "start_time": {
        "type": "string",
        "description": "Appointment start time in ISO format (e.g., 2024-01-15T09:00:00)"
      },
      "end_time": {
        "type": "string",
        "description": "Appointment end time in ISO format"
      },
      "doctor_name": {
        "type": "string",
        "description": "Name of the doctor (optional)"
      }
    },
    "required": ["patient_name", "start_time", "end_time"]
  }
}
```

---

## Step 7: Tool 4 - Check Availability

### 7.1 Create Sub-Workflow

Create a separate workflow `Check Availability`:

```yaml
# Trigger: Execute Workflow Trigger (accepts parameters)

# Step 1: Google Calendar - Get Events
Resource: Event
Operation: Get Many
Calendar: (Select calendar)
Return All: true
Time Min: {{ $json.start_date }}
Time Max: {{ $json.end_date }}

# Step 2: Code Node - Calculate Available Slots
```

```javascript
// Configuration
const config = {
  startHour: 9,        // 9 AM
  endHour: 17,         // 5 PM
  slotDuration: 30,    // 30 minutes
  bufferMinutes: 15,   // Buffer between appointments
};

const busySlots = $input.all().map(item => ({
  start: new Date(item.json.start.dateTime),
  end: new Date(item.json.end.dateTime)
}));

// Generate available slots
const startDate = new Date($json.start_date);
const endDate = new Date($json.end_date);
const availableSlots = [];

for (let d = new Date(startDate); d <= endDate; d.setDate(d.getDate() + 1)) {
  // Skip weekends
  if (d.getDay() === 0 || d.getDay() === 6) continue;
  
  for (let hour = config.startHour; hour < config.endHour; hour++) {
    for (let minute = 0; minute < 60; minute += config.slotDuration) {
      const slotStart = new Date(d);
      slotStart.setHours(hour, minute, 0, 0);
      
      const slotEnd = new Date(slotStart);
      slotEnd.setMinutes(slotEnd.getMinutes() + config.slotDuration);
      
      // Check if slot conflicts with busy times
      const isAvailable = !busySlots.some(busy => 
        (slotStart >= busy.start && slotStart < busy.end) ||
        (slotEnd > busy.start && slotEnd <= busy.end)
      );
      
      if (isAvailable) {
        availableSlots.push({
          start: slotStart.toISOString(),
          end: slotEnd.toISOString(),
          display: slotStart.toLocaleString('en-AU', {
            weekday: 'short',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
          })
        });
      }
    }
  }
}

// Return next 10 available slots
return { 
  available_slots: availableSlots.slice(0, 10),
  total_available: availableSlots.length
};
```

### 7.2 Tool Definition

```json
{
  "name": "check_availability",
  "description": "Check available appointment slots. Use when user wants to know available times before booking.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "start_date": {
        "type": "string",
        "description": "Start date for availability search (ISO format)"
      },
      "end_date": {
        "type": "string",
        "description": "End date for availability search (ISO format)"
      },
      "doctor_name": {
        "type": "string",
        "description": "Specific doctor to check availability for (optional)"
      }
    },
    "required": ["start_date", "end_date"]
  }
}
```

---

## Step 8: Tool 5 - Create Support Ticket (ServiceNow)

### 8.1 Add HTTP Request Node

```yaml
Node: HTTP Request
Name: create_ticket

# Configuration
Method: POST
URL: https://your-instance.service-now.com/api/now/table/incident

# Authentication
Authentication: Generic Credential Type
Generic Auth Type: Basic Auth
# Set credentials in n8n credentials

# Headers
Headers:
  - Name: Content-Type
    Value: application/json
  - Name: Accept
    Value: application/json

# Body
Body Content Type: JSON
JSON:
{
  "short_description": "{{ $json.title }}",
  "description": "{{ $json.description }}\n\nReported via Voice AI\nCaller: {{ $json.caller_name }}\nPhone: {{ $json.caller_phone }}",
  "caller_id": "{{ $json.caller_id }}",
  "category": "{{ $json.category }}",
  "urgency": "{{ $json.urgency || '3' }}",
  "impact": "{{ $json.impact || '3' }}"
}
```

### 8.2 Tool Definition

```json
{
  "name": "create_ticket",
  "description": "Create a support ticket in ServiceNow for issues that need follow-up or cannot be resolved immediately.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "title": {
        "type": "string",
        "description": "Brief title of the issue"
      },
      "description": {
        "type": "string",
        "description": "Detailed description of the problem"
      },
      "caller_name": {
        "type": "string",
        "description": "Name of the person reporting"
      },
      "caller_phone": {
        "type": "string",
        "description": "Phone number for callback"
      },
      "category": {
        "type": "string",
        "description": "Category (e.g., 'Hardware', 'Software', 'Network', 'Other')"
      },
      "urgency": {
        "type": "string",
        "description": "Urgency level: 1 (High), 2 (Medium), 3 (Low)"
      }
    },
    "required": ["title", "description"]
  }
}
```

---

## Step 9: Tool 6 - Hotel Check-In (Hospitality)

### 9.1 HTTP Request to PMS

```yaml
Node: HTTP Request
Name: guest_checkin

# Configuration
Method: POST
URL: {{ $env.PMS_URL }}/api/v1/reservations/{{ $json.reservation_id }}/checkin

# Headers
Headers:
  - Name: Authorization
    Value: Bearer {{ $env.PMS_API_KEY }}
  - Name: Content-Type
    Value: application/json

# Body
Body:
{
  "guest_name": "{{ $json.guest_name }}",
  "id_verified": true,
  "room_preferences": "{{ $json.preferences }}",
  "special_requests": "{{ $json.special_requests }}"
}
```

### 9.2 Tool Definition

```json
{
  "name": "guest_checkin",
  "description": "Check in a hotel guest. Requires reservation ID and guest verification.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "reservation_id": {
        "type": "string",
        "description": "The reservation or confirmation number"
      },
      "guest_name": {
        "type": "string",
        "description": "Guest's full name as on reservation"
      },
      "preferences": {
        "type": "string",
        "description": "Room preferences (high floor, quiet room, etc.)"
      },
      "special_requests": {
        "type": "string",
        "description": "Any special requests (extra pillows, late checkout, etc.)"
      }
    },
    "required": ["reservation_id", "guest_name"]
  }
}
```

---

## Step 10: Tool 7 - Escalate to Human

### 10.1 Code Node

```javascript
// This tool signals that the agent should transfer to a human
return {
  action: "escalate",
  reason: $json.reason,
  department: $json.department || "general",
  priority: $json.priority || "normal",
  context: {
    caller_name: $json.caller_name,
    caller_phone: $json.caller_phone,
    conversation_summary: $json.summary
  },
  instructions: "Transfer the call to a human agent. Say: 'I'll connect you with a team member who can better assist you. Please hold for a moment.'"
};
```

### 10.2 Tool Definition

```json
{
  "name": "escalate_to_human",
  "description": "Transfer the call to a human agent when the AI cannot resolve the issue, the customer explicitly requests a human, or the situation requires human judgment.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "reason": {
        "type": "string",
        "description": "Why the call is being escalated"
      },
      "department": {
        "type": "string",
        "description": "Department to transfer to (e.g., 'billing', 'technical', 'manager')"
      },
      "priority": {
        "type": "string",
        "description": "Priority level: 'urgent', 'normal', 'low'"
      },
      "summary": {
        "type": "string",
        "description": "Brief summary of the conversation so far"
      }
    },
    "required": ["reason"]
  }
}
```

---

## Step 11: Tool 8 - Log Call Notes

### 11.1 Google Sheets Node

```yaml
Node: Google Sheets
Name: log_call

# Configuration
Resource: Sheet
Operation: Append
Document: Voice AI Call Logs
Sheet: Calls

# Data to Append
Values:
  - Column: Timestamp
    Value: {{ $now }}
  - Column: Direction
    Value: {{ $json.direction }}
  - Column: From
    Value: {{ $json.from_number }}
  - Column: To
    Value: {{ $json.to_number }}
  - Column: Duration
    Value: {{ $json.duration }}
  - Column: Topic
    Value: {{ $json.topic }}
  - Column: Summary
    Value: {{ $json.summary }}
  - Column: Outcome
    Value: {{ $json.outcome }}
  - Column: Tools Used
    Value: {{ $json.tools_used }}
```

### 11.2 Tool Definition

```json
{
  "name": "log_call_notes",
  "description": "Log notes about the current call for record-keeping. Call this at the end of every conversation.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "direction": {
        "type": "string",
        "description": "'inbound' or 'outbound'"
      },
      "from_number": {
        "type": "string",
        "description": "Caller's phone number"
      },
      "to_number": {
        "type": "string",
        "description": "Number that was called"
      },
      "topic": {
        "type": "string",
        "description": "Main topic of the call"
      },
      "summary": {
        "type": "string",
        "description": "Brief summary of what was discussed"
      },
      "outcome": {
        "type": "string",
        "description": "Outcome (e.g., 'appointment_booked', 'ticket_created', 'resolved', 'escalated')"
      }
    },
    "required": ["topic", "summary", "outcome"]
  }
}
```

---

## Step 12: Tool 9 - Send Confirmation Email (Multi-Tenant)

This tool sends confirmation emails using tenant-specific SMTP settings fetched from your PostgreSQL backend.

### 12.1 Create Sub-Workflow: Get Tenant SMTP Config

First, create a sub-workflow to fetch tenant SMTP credentials:

```yaml
# Sub-Workflow: Get Tenant SMTP Config
# Trigger: Execute Workflow Trigger

# Step 1: HTTP Request - Fetch from Backend
Node: HTTP Request
Name: fetch_tenant_smtp
Method: GET
URL: {{ $env.BACKEND_URL }}/api/internal/tenant/{{ $json.tenant_id }}/smtp
Headers:
  - Name: Authorization
    Value: Bearer {{ $env.INTERNAL_API_KEY }}

# Step 2: Return SMTP Config
Node: Set
Output:
  smtp_host: {{ $json.smtp_host }}
  smtp_port: {{ $json.smtp_port }}
  smtp_user: {{ $json.smtp_user }}
  smtp_password: {{ $json.smtp_password }}
  from_name: {{ $json.from_name }}
  from_email: {{ $json.from_email }}
```

### 12.2 Main Email Tool Workflow

```yaml
# In main MCP workflow, add branch for send_confirmation_email

# Step 1: Credit Verification (REQUIRED before action tools)
Node: HTTP Request
Name: verify_credits
Method: POST
URL: {{ $env.BACKEND_URL }}/api/internal/credits/verify
Headers:
  - Name: Authorization
    Value: Bearer {{ $env.INTERNAL_API_KEY }}
Body:
{
  "tenant_id": "{{ $json.tenant_id }}",
  "action": "send_email",
  "estimated_cost": 0.10
}

# Step 2: Check Credit Response
Node: IF
Condition: {{ $json.has_sufficient_credits }} = true
True Branch → Continue
False Branch → Return Error: "Insufficient credits for this action"

# Step 3: Get Tenant SMTP Config
Node: Execute Workflow
Workflow: Get Tenant SMTP Config
Input: { "tenant_id": "{{ $json.tenant_id }}" }

# Step 4: Send Email
Node: Send Email
SMTP Credentials: (Use values from Step 3)
From: {{ $json.from_name }} <{{ $json.from_email }}>
To: {{ $input.first().json.recipient_email }}
Subject: {{ $input.first().json.subject || 'Confirmation' }}
Body: {{ $input.first().json.body }}

# Step 5: Deduct Credits
Node: HTTP Request
Name: deduct_credits
Method: POST
URL: {{ $env.BACKEND_URL }}/api/internal/credits/deduct
Headers:
  - Name: Authorization
    Value: Bearer {{ $env.INTERNAL_API_KEY }}
Body:
{
  "tenant_id": "{{ $json.tenant_id }}",
  "amount": 0.10,
  "type": "action_email",
  "description": "Confirmation email sent"
}
```

### 12.3 Tool Definition

```json
{
  "name": "send_confirmation_email",
  "description": "Send a confirmation email to the customer. Use after booking appointments or completing important actions. The email will use the tenant's configured branding.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "tenant_id": {
        "type": "string",
        "description": "The tenant ID (passed from agent context)"
      },
      "recipient_email": {
        "type": "string",
        "description": "Email address to send confirmation to"
      },
      "subject": {
        "type": "string",
        "description": "Email subject line"
      },
      "body": {
        "type": "string",
        "description": "Email body content"
      },
      "email_type": {
        "type": "string",
        "enum": ["appointment_confirmation", "ticket_confirmation", "general"],
        "description": "Type of confirmation email"
      }
    },
    "required": ["tenant_id", "recipient_email", "body"]
  }
}
```

---

## Step 13: Tool 10 - Enhanced Book Calendar Event

This enhanced calendar booking tool:
1. Verifies credit balance before booking
2. Checks availability first
3. Creates the calendar event
4. Optionally sends confirmation email

### 13.1 Create Integrated Booking Workflow

```yaml
# In main MCP workflow, REPLACE the simple book_appointment with this:

# Step 1: Credit Verification
Node: HTTP Request
Name: verify_credits_booking
Method: POST
URL: {{ $env.BACKEND_URL }}/api/internal/credits/verify
Headers:
  - Name: Authorization
    Value: Bearer {{ $env.INTERNAL_API_KEY }}
Body:
{
  "tenant_id": "{{ $json.tenant_id }}",
  "action": "book_appointment",
  "estimated_cost": 0.25
}

# Step 2: Check Credit Response
Node: IF
Name: has_credits
Condition: {{ $json.has_sufficient_credits }} = true
True Branch → Continue to availability check
False Branch → Return: { "error": "Insufficient credits", "balance": "{{ $json.current_balance }}" }

# Step 3: Check Availability First
Node: Execute Workflow
Name: check_availability_sub
Workflow: Check Availability
Input:
{
  "start_date": "{{ $json.start_time }}",
  "end_date": "{{ $json.end_time }}",
  "tenant_id": "{{ $json.tenant_id }}"
}

# Step 4: Verify Slot is Available
Node: IF
Name: slot_available
Condition: {{ $json.available_slots.length }} > 0
True Branch → Continue to booking
False Branch → Return: { "error": "Time slot not available", "suggestion": "Please choose another time" }

# Step 5: Get Tenant Calendar Config
Node: HTTP Request
Name: get_calendar_config
Method: GET
URL: {{ $env.BACKEND_URL }}/api/internal/tenant/{{ $json.tenant_id }}/calendar
Headers:
  - Name: Authorization
    Value: Bearer {{ $env.INTERNAL_API_KEY }}
# Returns: { "provider": "google|outlook", "calendar_id": "...", "credentials": {...} }

# Step 6: Branch by Calendar Provider
Node: Switch
Property: provider
Cases:
  - "google" → Google Calendar Node
  - "outlook" → Microsoft Outlook Node
```

### 13.2 Google Calendar Branch

```yaml
Node: Google Calendar
Name: book_google_calendar
Resource: Event
Operation: Create
Calendar: {{ $json.calendar_id }}

# Event Details
Title: {{ $input.first().json.title || 'Appointment' }}
Description: |
  Patient/Guest: {{ $input.first().json.patient_name }}
  Phone: {{ $input.first().json.patient_phone }}
  Reason: {{ $input.first().json.reason }}

  Booked via Voice AI Agent
Start Time: {{ $input.first().json.start_time }}
End Time: {{ $input.first().json.end_time }}
```

### 13.3 Microsoft Outlook Branch

```yaml
Node: Microsoft Outlook
Name: book_outlook_calendar
Resource: Event
Operation: Create

# Event Details
Subject: {{ $input.first().json.title || 'Appointment' }}
Body: |
  Patient/Guest: {{ $input.first().json.patient_name }}
  Phone: {{ $input.first().json.patient_phone }}
  Reason: {{ $input.first().json.reason }}

  Booked via Voice AI Agent
Start: {{ $input.first().json.start_time }}
End: {{ $input.first().json.end_time }}
```

### 13.4 Post-Booking Actions

```yaml
# After successful booking (either provider)

# Step 7: Deduct Credits
Node: HTTP Request
Name: deduct_booking_credits
Method: POST
URL: {{ $env.BACKEND_URL }}/api/internal/credits/deduct
Body:
{
  "tenant_id": "{{ $json.tenant_id }}",
  "amount": 0.25,
  "type": "action_booking",
  "description": "Calendar booking"
}

# Step 8: Optional - Send Confirmation Email
Node: IF
Name: should_send_email
Condition: {{ $input.first().json.send_confirmation }} = true
True Branch → Execute send_confirmation_email workflow
False Branch → Skip

# Step 9: Return Success
Node: Set
Output:
{
  "success": true,
  "event_id": "{{ $json.id }}",
  "start_time": "{{ $json.start.dateTime }}",
  "confirmation_sent": {{ $json.email_sent || false }}
}
```

### 13.5 Updated Tool Definition

```json
{
  "name": "book_calendar_event",
  "description": "Book an appointment on the calendar. This tool automatically checks availability and verifies credits before booking. Use after confirming details with the caller.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "tenant_id": {
        "type": "string",
        "description": "The tenant ID (from agent context)"
      },
      "patient_name": {
        "type": "string",
        "description": "Full name of the patient/guest"
      },
      "patient_phone": {
        "type": "string",
        "description": "Phone number"
      },
      "patient_email": {
        "type": "string",
        "description": "Email address for confirmation"
      },
      "reason": {
        "type": "string",
        "description": "Reason for the appointment"
      },
      "start_time": {
        "type": "string",
        "description": "Start time in ISO format (e.g., 2024-01-15T09:00:00)"
      },
      "end_time": {
        "type": "string",
        "description": "End time in ISO format"
      },
      "send_confirmation": {
        "type": "boolean",
        "description": "Whether to send a confirmation email",
        "default": true
      }
    },
    "required": ["tenant_id", "patient_name", "start_time", "end_time"]
  }
}
```

---

## Step 14: Backend Endpoints for n8n

Add these internal endpoints to your FastAPI backend to support multi-tenant n8n workflows:

```python
# src/backend/app/api/routes/internal.py (additions)

@router.get("/tenant/{tenant_id}/smtp")
async def get_tenant_smtp_config(
    tenant_id: str,
    _auth: None = Depends(verify_internal_auth),
    db: AsyncSession = Depends(get_db),
):
    """Get SMTP configuration for a tenant."""
    config = await db.execute(
        select(TenantConfig).where(TenantConfig.tenant_id == tenant_id)
    )
    tenant_config = config.scalar_one_or_none()

    if not tenant_config or not tenant_config.smtp_host:
        raise HTTPException(404, "SMTP not configured for tenant")

    return {
        "smtp_host": tenant_config.smtp_host,
        "smtp_port": tenant_config.smtp_port,
        "smtp_user": tenant_config.smtp_user,
        "smtp_password": tenant_config.smtp_password,  # Decrypt in production
        "from_name": tenant_config.from_name,
        "from_email": tenant_config.from_email,
    }


@router.get("/tenant/{tenant_id}/calendar")
async def get_tenant_calendar_config(
    tenant_id: str,
    _auth: None = Depends(verify_internal_auth),
    db: AsyncSession = Depends(get_db),
):
    """Get calendar configuration for a tenant."""
    config = await db.execute(
        select(TenantConfig).where(TenantConfig.tenant_id == tenant_id)
    )
    tenant_config = config.scalar_one_or_none()

    if not tenant_config:
        raise HTTPException(404, "Calendar not configured for tenant")

    return {
        "provider": tenant_config.calendar_provider,  # "google" or "outlook"
        "calendar_id": tenant_config.calendar_id,
        "credentials": tenant_config.calendar_credentials,  # OAuth tokens
    }


@router.post("/credits/verify")
async def verify_credits_for_action(
    request: VerifyCreditsRequest,
    _auth: None = Depends(verify_internal_auth),
    db: AsyncSession = Depends(get_db),
):
    """Verify tenant has sufficient credits for an action."""
    from app.services.credit_service import credit_service

    balance = await credit_service.get_balance(db, request.tenant_id)
    has_credits = balance >= Decimal(str(request.estimated_cost))

    return {
        "has_sufficient_credits": has_credits,
        "current_balance": float(balance),
        "estimated_cost": request.estimated_cost,
        "action": request.action,
    }
```

---

## Step 15: Complete MCP Workflow Structure

```
[MCP Server Trigger]
        │
        ├──▶ [Switch: Tool Name]
        │           │
        │           ├── query_kb ──▶ [HTTP: LightRAG]
        │           │
        │           ├── get_datetime ──▶ [Code: DateTime]
        │           │
        │           ├── book_calendar_event ──▶ [Credit Check] ──▶ [Check Avail] ──▶ [Calendar API]
        │           │                                    └── [Deduct Credits] ──▶ [Send Email]
        │           │
        │           ├── check_availability ──▶ [Sub-Workflow]
        │           │
        │           ├── send_confirmation_email ──▶ [Credit Check] ──▶ [Get SMTP] ──▶ [Send Email]
        │           │                                       └── [Deduct Credits]
        │           │
        │           ├── create_ticket ──▶ [HTTP: ServiceNow]
        │           │
        │           ├── guest_checkin ──▶ [HTTP: PMS]
        │           │
        │           ├── escalate_to_human ──▶ [Code: Return Signal]
        │           │
        │           └── log_call_notes ──▶ [Google Sheets]
        │
        └──▶ [Respond to MCP Client]
```

---

## Step 16: Activate and Test

1. Click **Save** in n8n
2. Toggle workflow to **Active**
3. Copy the **Production URL** from MCP Server Trigger
4. Test with curl:

```bash
# Test query_kb tool
curl -X POST "http://localhost:5678/webhook/your-mcp-id" \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "query_kb",
    "arguments": {
      "query": "What are the check-in hours?"
    }
  }'
```

---

## Step 17: Export Workflow

```bash
# Export workflow from n8n UI
# Save to: src/n8n-workflows/voice-agent-mcp.json
```

---

## MCP URL for Agent

Save this URL - you'll need it in the Voice Agent configuration:

```
MCP_SERVER_URL=http://localhost:5678/webhook/your-mcp-webhook-id
```

---

## Next Step

Proceed to: `.claude/skills/05-LIVEKIT-SETUP.md`
