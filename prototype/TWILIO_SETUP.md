# Twilio Integration Setup Guide

This guide shows you how to connect your LiveKit voice agent to Twilio so it can answer phone calls.

## Important: Public Server Required

**Your local LiveKit server won't work with Twilio.** Twilio needs to reach a publicly accessible endpoint.

### Options:
1. **LiveKit Cloud** (Recommended - easiest setup)
2. **Deploy your own server** (ngrok, AWS, GCP, etc.)

---

## Option 1: LiveKit Cloud (Recommended)

### Step 1: Install LiveKit CLI

```bash
# macOS
brew install livekit-cli

# Or download from:
# https://github.com/livekit/livekit-cli/releases
```

### Step 2: Sign Up for LiveKit Cloud

1. Visit https://cloud.livekit.io
2. Sign up for a free account
3. Create a new project

### Step 3: Authenticate CLI

```bash
lk cloud auth
```

Follow the prompts to login.

### Step 4: Get Your Cloud Credentials

```bash
lk cloud project list
lk cloud project show <project-name>
```

Update your `.env` file with LiveKit Cloud credentials:
```bash
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=APIxxxxxxxxxxxxx
LIVEKIT_API_SECRET=your-secret-here
```

### Step 5: Deploy Your Agent

```bash
# Start the telephony-enabled agent
python voice_agent_telephony.py start
```

The agent will connect to LiveKit Cloud.

---

## Twilio Configuration

### Step 1: Purchase a Twilio Phone Number

1. Log in to [Twilio Console](https://console.twilio.com)
2. Go to **Phone Numbers** → **Buy a number**
3. Choose a number and purchase it

### Step 2: Create SIP Inbound Trunk

Create `inbound-trunk.json`:

```json
{
  "trunk": {
    "name": "Twilio Inbound Trunk",
    "auth_username": "your_sip_username",
    "auth_password": "your_secure_password_here"
  }
}
```

**Important:** Choose a strong password for production!

Create the trunk using LiveKit CLI:

```bash
lk sip inbound create inbound-trunk.json
```

Save the trunk ID from the output (looks like `ST_xxxxxxxxxxxxx`).

### Step 3: Create Dispatch Rule

Create `dispatch-rule.json`:

```json
{
  "dispatch_rule": {
    "rule": {
      "dispatchRuleIndividual": {
        "roomPrefix": "call-"
      }
    },
    "roomConfig": {
      "agents": [{
        "agentName": "telephony-agent"
      }]
    }
  }
}
```

Create the dispatch rule:

```bash
lk sip dispatch create dispatch-rule.json
```

This tells LiveKit to:
- Create a room with prefix "call-" for each incoming call
- Automatically dispatch the "telephony-agent" to answer

### Step 4: Get Your SIP Endpoint

```bash
lk sip inbound list
```

Note your SIP endpoint (e.g., `sip.livekit.cloud` or similar).

### Step 5: Create TwiML Bin

1. Go to Twilio Console → **Runtime** → **TwiML Bins**
2. Click **Create new TwiML Bin**
3. Name it: `LiveKit Voice Agent`
4. Add this TwiML code:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Dial>
    <Sip username="your_sip_username" password="your_secure_password_here">
      sip:+1234567890@your-sip-endpoint.livekit.cloud
    </Sip>
  </Dial>
</Response>
```

Replace:
- `your_sip_username` - from your inbound-trunk.json
- `your_secure_password_here` - from your inbound-trunk.json
- `+1234567890` - your Twilio phone number (E.164 format)
- `your-sip-endpoint.livekit.cloud` - your SIP endpoint from Step 4

5. Click **Create**

### Step 6: Configure Phone Number

1. Go to **Phone Numbers** → **Manage** → **Active Numbers**
2. Click on your purchased number
3. Under **Voice Configuration**:
   - **A call comes in:** Select "TwiML Bin"
   - Choose your "LiveKit Voice Agent" bin
4. Click **Save**

---

## Testing

### Start Your Agent

```bash
cd prototype
source venv/bin/activate
python voice_agent_telephony.py start
```

### Make a Test Call

1. Call your Twilio phone number from any phone
2. The LiveKit agent should answer automatically
3. Start speaking - the agent will transcribe, process, and respond

### Monitor Logs

Watch agent logs for connection and conversation details:
```bash
# Check agent status
lk dispatch list

# View room details
lk room list

# Check SIP trunk status
lk sip inbound list
```

---

## Troubleshooting

### Agent doesn't answer calls

1. Verify agent is running:
   ```bash
   lk dispatch list
   ```

2. Check dispatch rule:
   ```bash
   lk sip dispatch list
   ```

3. Verify agent name matches: `telephony-agent`

### "All circuits are busy" error

- Check SIP credentials in TwiML Bin match inbound-trunk.json
- Verify SIP endpoint is correct
- Check trunk status: `lk sip inbound list`

### Call connects but no audio

- Verify all API keys in `.env` are valid:
  - DEEPGRAM_API_KEY
  - OPENAI_API_KEY
  - CARTESIA_API_KEY
- Check agent logs for WebSocket connection errors
- Ensure you have credits on all AI services

### TwiML/SIP errors

- Verify phone number format is E.164 (+1234567890)
- Check SIP username/password match exactly
- Ensure TwiML syntax is correct (no extra spaces)

---

## Alternative: Using ngrok for Local Testing

If you want to test with your local LiveKit server:

### Step 1: Install ngrok

```bash
brew install ngrok  # macOS
# or download from: https://ngrok.com
```

### Step 2: Expose Local LiveKit Server

```bash
ngrok tcp 7880
```

Note the forwarding address (e.g., `tcp://0.tcp.ngrok.io:12345`).

### Step 3: Update TwiML

Use ngrok address in your TwiML Bin:
```xml
<Sip username="username" password="password">
  sip:+1234567890@0.tcp.ngrok.io:12345
</Sip>
```

**Note:** Free ngrok URLs change on restart. Paid plans offer static addresses.

---

## Next Steps

### Advanced Features

1. **Call Transfer**: Transfer calls to other numbers
2. **Voicemail Detection**: Detect answering machines
3. **Call Recording**: Record conversations for quality/training
4. **DTMF Support**: Handle keypad input during calls
5. **Outbound Calls**: Have the agent initiate calls

See LiveKit telephony docs: https://docs.livekit.io/agents/start/telephony/

### Production Deployment

1. Use LiveKit Cloud or deploy self-hosted to AWS/GCP
2. Set up monitoring and logging
3. Implement rate limiting
4. Add error handling and fallbacks
5. Configure auto-scaling for high call volumes

---

## Cost Estimates

**Twilio:**
- Phone number: ~$1/month
- Inbound calls: ~$0.0085/minute
- Outbound calls: ~$0.013/minute

**LiveKit Cloud:**
- Free tier: 50GB/month bandwidth
- Paid: Usage-based pricing

**AI Services:**
- Deepgram STT: ~$0.0043/minute
- OpenAI GPT-4o: ~$0.005-0.015/minute (varies by usage)
- Cartesia TTS: ~$0.05/1000 chars (~$0.005/minute)

**Total per minute:** ~$0.03-0.05/minute

---

## Resources

- LiveKit Telephony Docs: https://docs.livekit.io/agents/start/telephony/
- Twilio Voice Docs: https://www.twilio.com/docs/voice
- LiveKit CLI: https://github.com/livekit/livekit-cli
- Example Code: https://github.com/livekit/agents
