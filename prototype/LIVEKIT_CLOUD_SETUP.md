# LiveKit Cloud Setup Guide

Complete step-by-step guide to set up LiveKit Cloud with Twilio telephony.

## Step 1: Sign Up for LiveKit Cloud

1. Visit https://cloud.livekit.io
2. Click **Sign Up** (or Sign in if you have an account)
3. You can sign up with:
   - GitHub
   - Google
   - Email

4. Complete the signup process

## Step 2: Authenticate CLI

Once you have an account, authenticate the CLI:

```bash
lk cloud auth
```

This will:
1. Open a browser window
2. Ask you to authorize the CLI
3. Save credentials locally

## Step 3: Create a Project

After authentication, create a new project or use an existing one:

```bash
# List existing projects
lk cloud project list

# OR create a new project (if needed)
lk cloud project create voice-ai-prototype
```

## Step 4: Get Project Credentials

Get your project's credentials:

```bash
# Show project details
lk cloud project show <your-project-name>

# Get specific credentials
lk cloud project keys <your-project-name>
```

You'll see output like:
```
API Key: APIxxxxxxxxxxxxx
API Secret: your-secret-here
WebSocket URL: wss://your-project.livekit.cloud
```

## Step 5: Update Local .env File

Copy the credentials to your `.env` file:

```bash
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=APIxxxxxxxxxxxxx
LIVEKIT_API_SECRET=your-secret-here

# Keep your AI service keys
DEEPGRAM_API_KEY=your_deepgram_key
OPENAI_API_KEY=your_openai_key
CARTESIA_API_KEY=your_cartesia_key
```

## Step 6: Create SIP Inbound Trunk

Create a SIP trunk for Twilio to connect:

```bash
cd /Users/garimatyagi/work/voice-ai/prototype

# Generate secure credentials
export SIP_USERNAME="livekit_$(date +%s)"
export SIP_PASSWORD=$(openssl rand -base64 32 | tr -d '/+=' | head -c 24)

# Create trunk config
cat > config/cloud-inbound-trunk.json <<EOF
{
  "trunk": {
    "name": "Twilio Voice Trunk",
    "auth_username": "$SIP_USERNAME",
    "auth_password": "$SIP_PASSWORD"
  }
}
EOF

# Create the trunk
lk sip inbound create config/cloud-inbound-trunk.json

# Save the trunk ID shown in output (ST_xxxxx)
```

## Step 7: Create Dispatch Rule

Configure automatic agent dispatch for incoming calls:

```bash
# Create the dispatch rule
lk sip dispatch create config/dispatch-rule.json

# Verify it was created
lk sip dispatch list
```

## Step 8: Get SIP Endpoint

Find your SIP endpoint for Twilio configuration:

```bash
lk sip inbound list
```

Look for the **SIP URI** in the output. It will look like:
```
sip.livekit.cloud
```

## Step 9: Start Voice Agent Connected to Cloud

Update your agent to connect to LiveKit Cloud:

```bash
cd /Users/garimatyagi/work/voice-ai/prototype
source venv/bin/activate
python voice_agent_telephony.py start
```

The agent will now connect to LiveKit Cloud instead of localhost.

## Step 10: Configure Twilio

### A. Purchase Twilio Number (if you haven't)

1. Go to https://console.twilio.com
2. Navigate to **Phone Numbers** → **Buy a number**
3. Purchase a phone number

### B. Create TwiML Bin

1. Go to **Runtime** → **TwiML Bins**
2. Click **Create new TwiML Bin**
3. Name: `LiveKit Cloud Voice Agent`
4. Paste this TwiML (update with YOUR values):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Dial>
    <Sip username="YOUR_SIP_USERNAME" password="YOUR_SIP_PASSWORD">
      sip:YOUR_TWILIO_NUMBER@sip.livekit.cloud
    </Sip>
  </Dial>
</Response>
```

**Replace:**
- `YOUR_SIP_USERNAME` - from Step 6
- `YOUR_SIP_PASSWORD` - from Step 6
- `YOUR_TWILIO_NUMBER` - your Twilio number in E.164 format (e.g., +15551234567)

5. Click **Create**

### C. Configure Phone Number

1. Go to **Phone Numbers** → **Manage** → **Active Numbers**
2. Click your purchased number
3. Under **Voice Configuration**:
   - **A call comes in:** Select "TwiML Bin"
   - Choose "LiveKit Cloud Voice Agent"
4. Click **Save**

## Step 11: Test!

Call your Twilio number from any phone. The agent should:

1. Answer automatically
2. Greet you with a voice message
3. Listen and respond to your questions

## Monitoring and Debugging

### Check Agent Status

```bash
# List running agents
lk dispatch list

# List active rooms
lk room list

# View SIP trunks
lk sip inbound list

# View dispatch rules
lk sip dispatch list
```

### View Logs

Check the agent terminal for real-time logs showing:
- Connection to LiveKit Cloud
- Incoming SIP calls
- STT/LLM/TTS activity

### LiveKit Cloud Dashboard

Visit https://cloud.livekit.io to see:
- Active rooms
- Call analytics
- Usage metrics
- Logs

## Troubleshooting

### Agent Won't Connect to Cloud

**Error:** Connection refused or authentication failed

**Solution:**
- Verify credentials in `.env` match cloud project
- Check LIVEKIT_URL starts with `wss://` (not `http://`)
- Ensure API key/secret are correct

### No Calls Reaching Agent

**Check:**
1. Agent is running: `ps aux | grep voice_agent`
2. Dispatch rule exists: `lk sip dispatch list`
3. Agent name matches: `telephony-agent`
4. TwiML is correct in Twilio console

### Agent Answers But No Audio

**Check:**
1. All AI API keys are valid (Deepgram, OpenAI, Cartesia)
2. Agent logs show WebSocket connections
3. Check quotas/credits on AI services

### Twilio Errors

**"All circuits are busy"**
- SIP credentials in TwiML don't match trunk
- SIP endpoint is wrong

**"Cannot connect to SIP"**
- Check SIP URI: should be `sip.livekit.cloud`
- Verify trunk was created: `lk sip inbound list`

## Cost Management

### LiveKit Cloud Free Tier

- **50GB/month** bandwidth
- Unlimited rooms
- Unlimited participants
- Perfect for testing and small projects

### When You Exceed Free Tier

LiveKit will email you. Paid plans start at:
- **$0.30/GB** for bandwidth
- No minimum commitment

### AI Service Costs (Estimated per minute)

- Deepgram STT: ~$0.0043/min
- OpenAI GPT-4o: ~$0.005-0.015/min
- Cartesia TTS: ~$0.005/min
- **Total: ~$0.015-0.025/min**

### Twilio Costs

- Phone number: ~$1/month
- Inbound calls: ~$0.0085/min
- **Total per minute: ~$0.025-0.035/min** (AI + Twilio)

## Next Steps

Once telephony is working:

1. **Add Features:**
   - Call transfer
   - Voicemail detection
   - DTMF (keypad) support
   - Call recording

2. **Improve Agent:**
   - Custom prompts for different use cases
   - Function calling for actions
   - Knowledge base integration

3. **Production Deployment:**
   - Set up monitoring
   - Implement rate limiting
   - Add error handling
   - Configure auto-scaling

4. **Testing:**
   - Load testing with concurrent calls
   - Different phone number formats
   - International numbers

## Resources

- LiveKit Cloud Dashboard: https://cloud.livekit.io
- LiveKit Docs: https://docs.livekit.io
- LiveKit Agents Telephony: https://docs.livekit.io/agents/start/telephony/
- Twilio Console: https://console.twilio.com
- Support: https://livekit.io/support
