# Tenant Onboarding Guide

## Overview

This guide walks through the process of onboarding a new tenant to the Voice AI Platform.

---

## Pre-Onboarding Checklist

Before onboarding a tenant, gather:

- [ ] Company name and billing email
- [ ] Primary contact information
- [ ] Use case (Healthcare, Hospitality, Other)
- [ ] Phone number requirements (quantity, area codes)
- [ ] Call type needs (inbound only, outbound only, or both)
- [ ] Expected call volume
- [ ] Initial credit purchase amount
- [ ] Integration requirements (CRM, PMS, Calendar, etc.)

---

## Step 1: Create Tenant Account

### 1.1 Via Admin Dashboard

1. Log in to Admin Dashboard as Superadmin
2. Navigate to **Tenants** → **Create New**
3. Fill in:
   - **Name**: Company display name
   - **Slug**: URL-safe identifier (auto-generated)
   - **Admin Email**: Primary admin contact
   - **Billing Email**: For invoices/alerts

### 1.2 Via API

```bash
curl -X POST https://api.yourdomain.com/tenants \
  -H "Authorization: Bearer <superadmin_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Sunshine Medical Clinic",
    "slug": "sunshine-medical",
    "admin_email": "admin@sunshinemedical.com",
    "billing_email": "billing@sunshinemedical.com",
    "inbound_calls_enabled": true,
    "outbound_calls_enabled": false,
    "credit_limit": 1000
  }'
```

---

## Step 2: Add Initial Credits

### 2.1 Via Admin Dashboard

1. Navigate to **Tenants** → Select tenant
2. Click **Add Credits**
3. Enter amount and description
4. Confirm

### 2.2 Via API

```bash
curl -X POST https://api.yourdomain.com/credits/add \
  -H "Authorization: Bearer <superadmin_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "uuid-here",
    "amount": 500,
    "description": "Initial setup credits"
  }'
```

---

## Step 3: Create Tenant Admin User

### 3.1 Via Admin Dashboard

1. Navigate to **Tenants** → Select tenant → **Users**
2. Click **Create User**
3. Fill in:
   - Email
   - Temporary password
   - Full name
   - Role: **Tenant Admin**
4. Send welcome email with credentials

### 3.2 Via API

```bash
curl -X POST https://api.yourdomain.com/users \
  -H "Authorization: Bearer <superadmin_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@sunshinemedical.com",
    "password": "TempPassword123!",
    "full_name": "John Smith",
    "tenant_id": "uuid-here",
    "role_names": ["tenant_admin"]
  }'
```

---

## Step 4: Configure Phone Numbers

### 4.1 Purchase Numbers in Telnyx

1. Log in to Telnyx Portal
2. Navigate to **Numbers** → **Buy Numbers**
3. Search by area code or features
4. Purchase required numbers
5. Note the E.164 formatted numbers

### 4.2 Add to Platform

```bash
curl -X POST https://api.yourdomain.com/phone-numbers \
  -H "Authorization: Bearer <superadmin_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "uuid-here",
    "number": "+14155551234",
    "display_name": "Main Reception",
    "provider": "telnyx",
    "can_receive_calls": true,
    "can_make_calls": true,
    "max_calls_per_day": 10
  }'
```

Note: New numbers start with low daily limits (warming period).

---

## Step 5: Upload Knowledge Base Documents

### 5.1 Gather Documents

Request from tenant:
- FAQ documents
- Service/product information
- Policies and procedures
- Pricing information
- Contact details
- Hours of operation

### 5.2 Upload to LightRAG

1. Log in to LightRAG UI (as tenant)
2. Navigate to **Documents**
3. Upload PDFs, TXT, or MD files
4. Wait for processing
5. Test queries in **Retrieval** tab

### 5.3 Via API

```bash
# Add text content
curl -X POST https://api.yourdomain.com/kb/documents/text \
  -H "Authorization: Bearer <tenant_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Sunshine Medical Clinic is open Monday through Friday, 8:00 AM to 6:00 PM. We accept all major insurance plans including Blue Cross, Aetna, and Medicare.",
    "metadata": {
      "category": "general_info",
      "source": "admin"
    }
  }'
```

---

## Step 6: Configure Voice Agent

### 6.1 Choose Agent Template

Available templates:
- **Healthcare** - Appointment booking, insurance questions
- **Hospitality** - Check-in, room service, concierge
- **Generic** - General customer support

### 6.2 Customize System Prompt

Navigate to **Configuration** → **Agent Settings**

Example customization for healthcare:

```
Agent Name: Sarah
Organization: Sunshine Medical Clinic

Key Information:
- Hours: Monday-Friday 8am-6pm
- Address: 123 Health Street, Suite 100
- Phone: (415) 555-1234
- Services: Primary care, pediatrics, women's health
- Insurance: Blue Cross, Aetna, Medicare, Medicaid

Special Instructions:
- Always verify patient DOB before discussing appointments
- For emergencies, advise calling 911
- Appointment slots are 30 minutes
- Offer callback if wait times exceed 2 minutes
```

### 6.3 Select Voice

Choose Cartesia voice that matches brand:
- Professional male
- Professional female
- Friendly/casual
- Formal/authoritative

### 6.4 Enable Tools

Select which tools the agent can use:
- [x] query_kb - Search knowledge base
- [x] check_availability - View open slots
- [x] book_appointment - Schedule appointments
- [x] create_ticket - Log issues
- [ ] escalate_to_human - Transfer calls
- [x] log_call_notes - Record call summaries

---

## Step 7: Configure Integrations

### 7.1 Google Calendar (for appointments)

1. Tenant creates Google service account
2. Shares calendar with service account
3. Provides credentials to platform

### 7.2 ServiceNow (for tickets)

1. Tenant provides API credentials
2. Configure in n8n workflow
3. Test ticket creation

### 7.3 PMS Integration (hospitality)

1. Obtain API access from PMS vendor
2. Configure endpoints in n8n
3. Map guest data fields

---

## Step 8: Test the System

### 8.1 Browser Test

1. Generate test token
2. Join via meet.livekit.io
3. Test conversations:
   - "What are your hours?"
   - "I'd like to book an appointment"
   - "Do you accept Blue Cross insurance?"

### 8.2 Phone Test (if inbound enabled)

1. Call tenant's phone number
2. Verify:
   - Agent answers
   - Greeting is correct
   - KB queries work
   - Appointments can be booked

### 8.3 Checklist

- [ ] Agent responds conversationally
- [ ] Knowledge base queries return accurate info
- [ ] Appointment booking works end-to-end
- [ ] Call logging is working
- [ ] Credits are being deducted

---

## Step 9: Training & Handoff

### 9.1 Admin Training

Cover with tenant admin:
- Dashboard navigation
- Viewing call logs
- Monitoring credit balance
- Adding users
- Updating KB content
- Viewing usage reports

### 9.2 Documentation Provided

Share with tenant:
- Quick start guide
- API documentation (if needed)
- Support contact information
- Credit rates and billing info

### 9.3 Go-Live Checklist

- [ ] All tests passed
- [ ] Tenant admin trained
- [ ] Initial credits loaded
- [ ] Phone numbers active
- [ ] KB content complete
- [ ] Integrations working
- [ ] Support contact established

---

## Post-Onboarding

### Week 1 Check-in

- Review call logs for issues
- Check KB query accuracy
- Verify credit usage is reasonable
- Address any agent behavior issues

### Month 1 Review

- Usage report review
- KB content updates needed?
- Adjust agent prompts if needed
- Credit top-up reminder

### Ongoing Support

- Monitor for low credits
- Regular KB updates
- Agent performance optimization
- Feature requests

---

## Troubleshooting Common Issues

### Agent Gives Wrong Information

1. Check KB content accuracy
2. Review query mode (use "mix")
3. Update/add relevant documents
4. Adjust system prompt

### Calls Not Connecting

1. Verify SIP trunk configuration
2. Check dispatch rules
3. Confirm phone number is active
4. Review firewall settings

### Credits Depleting Too Fast

1. Review usage breakdown
2. Check for long calls
3. Optimize LLM usage
4. Consider adjusting rates

### Appointment Booking Fails

1. Verify calendar integration
2. Check calendar permissions
3. Test with shorter time slots
4. Review error logs

---

## Templates

### Welcome Email Template

```
Subject: Welcome to Voice AI Platform - Your Account is Ready

Hi [Name],

Welcome to Voice AI Platform! Your account has been set up for [Company Name].

Your login credentials:
- URL: https://dashboard.yourdomain.com
- Email: [email]
- Temporary Password: [password]

Please change your password upon first login.

Your initial setup includes:
- [X] credits to get started
- [X] phone number(s): [numbers]
- Pre-configured voice agent for [Healthcare/Hospitality]

Next Steps:
1. Log in and explore the dashboard
2. Review your agent configuration
3. Upload additional knowledge base content
4. Test by calling your number

Need help? Reply to this email or call (555) 123-4567.

Best regards,
Voice AI Platform Team
```

### Handoff Checklist Document

```
## Voice AI Platform - Tenant Handoff

Tenant: [Company Name]
Setup Date: [Date]
Setup By: [Your Name]

### Account Details
- Tenant ID: [uuid]
- Admin Email: [email]
- Initial Credits: [amount]

### Phone Numbers
- [+1234567890] - Main Reception

### Configuration
- Agent Type: [Healthcare/Hospitality]
- Agent Name: [Name]
- Voice: [Voice ID/Name]
- Tools Enabled: [List]

### Integrations
- Calendar: [Yes/No] - [Details]
- CRM: [Yes/No] - [Details]
- PMS: [Yes/No] - [Details]

### Testing
- Browser test: [Pass/Fail]
- Phone test: [Pass/Fail]
- KB queries: [Pass/Fail]
- Booking: [Pass/Fail]

### Training Completed
- [ ] Dashboard overview
- [ ] Call log review
- [ ] KB management
- [ ] User management
- [ ] Credit monitoring

### Notes
[Any special configuration or considerations]

### Sign-off
Tenant Admin: _________________ Date: _______
Platform Admin: ________________ Date: _______
```
