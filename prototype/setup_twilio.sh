#!/bin/bash
# Quick setup script for LiveKit + Twilio integration

set -e

echo "🔧 LiveKit + Twilio Setup Helper"
echo "================================="
echo ""

# Check if LiveKit CLI is installed
if ! command -v lk &> /dev/null; then
    echo "❌ LiveKit CLI is not installed"
    echo ""
    echo "Install it with:"
    echo "  macOS:  brew install livekit-cli"
    echo "  Linux:  Download from https://github.com/livekit/livekit-cli/releases"
    echo ""
    exit 1
fi

echo "✅ LiveKit CLI found"
echo ""

# Check authentication
echo "🔐 Checking LiveKit Cloud authentication..."
if lk cloud project list &> /dev/null; then
    echo "✅ Already authenticated to LiveKit Cloud"
    echo ""

    # Show projects
    echo "📋 Your LiveKit Cloud projects:"
    lk cloud project list
    echo ""
else
    echo "❌ Not authenticated to LiveKit Cloud"
    echo ""
    echo "Please run: lk cloud auth"
    echo "Then re-run this script."
    exit 1
fi

# Get project details
echo "Enter your LiveKit Cloud project name:"
read -p "> " PROJECT_NAME

if [ -z "$PROJECT_NAME" ]; then
    echo "❌ Project name cannot be empty"
    exit 1
fi

echo ""
echo "📡 Fetching project details..."
PROJECT_INFO=$(lk cloud project show "$PROJECT_NAME" 2>/dev/null || echo "")

if [ -z "$PROJECT_INFO" ]; then
    echo "❌ Project '$PROJECT_NAME' not found"
    echo ""
    echo "Available projects:"
    lk cloud project list
    exit 1
fi

echo "✅ Project found: $PROJECT_NAME"
echo ""

# Generate SIP credentials
echo "🔑 Generate SIP Trunk credentials:"
echo ""
SIP_USERNAME="livekit_sip_$(date +%s)"
SIP_PASSWORD=$(openssl rand -base64 32 | tr -d '/+=' | head -c 24)

echo "Generated credentials:"
echo "  Username: $SIP_USERNAME"
echo "  Password: $SIP_PASSWORD"
echo ""

# Update config files
echo "📝 Updating configuration files..."

# Update inbound-trunk.json
cat > config/inbound-trunk.json <<EOF
{
  "trunk": {
    "name": "Twilio Inbound Trunk",
    "auth_username": "$SIP_USERNAME",
    "auth_password": "$SIP_PASSWORD"
  }
}
EOF

echo "✅ Updated config/inbound-trunk.json"
echo ""

# Create inbound trunk
echo "🚀 Creating SIP inbound trunk..."
TRUNK_OUTPUT=$(lk sip inbound create config/inbound-trunk.json 2>&1)
TRUNK_ID=$(echo "$TRUNK_OUTPUT" | grep -o 'ST_[a-zA-Z0-9]*' | head -1)

if [ -z "$TRUNK_ID" ]; then
    echo "❌ Failed to create inbound trunk"
    echo "$TRUNK_OUTPUT"
    exit 1
fi

echo "✅ Created trunk: $TRUNK_ID"
echo ""

# Get SIP endpoint
echo "🌐 Getting SIP endpoint..."
SIP_ENDPOINT=$(lk sip inbound list | grep -o '[a-z0-9.-]*\.livekit\.cloud' | head -1)

if [ -z "$SIP_ENDPOINT" ]; then
    SIP_ENDPOINT="sip.livekit.cloud"
fi

echo "✅ SIP Endpoint: $SIP_ENDPOINT"
echo ""

# Create dispatch rule
echo "📞 Creating dispatch rule..."
lk sip dispatch create config/dispatch-rule.json
echo "✅ Dispatch rule created"
echo ""

# Get Twilio phone number
echo "Enter your Twilio phone number (E.164 format, e.g., +15551234567):"
read -p "> " TWILIO_NUMBER

if [ -z "$TWILIO_NUMBER" ]; then
    echo "⚠️  Phone number not provided - you'll need to update TwiML manually"
    TWILIO_NUMBER="+1234567890"
fi

# Generate TwiML
cat > config/twiml-configured.xml <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Dial>
    <Sip username="$SIP_USERNAME" password="$SIP_PASSWORD">
      sip:$TWILIO_NUMBER@$SIP_ENDPOINT
    </Sip>
  </Dial>
</Response>
EOF

echo ""
echo "✅ Configuration complete!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 Next Steps:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1. Copy the TwiML configuration:"
echo "   cat config/twiml-configured.xml"
echo ""
echo "2. In Twilio Console (https://console.twilio.com):"
echo "   a. Go to Runtime → TwiML Bins"
echo "   b. Create new TwiML Bin"
echo "   c. Paste the XML content above"
echo "   d. Save it"
echo ""
echo "3. Configure your Twilio phone number:"
echo "   a. Go to Phone Numbers → Manage → Active Numbers"
echo "   b. Click your number: $TWILIO_NUMBER"
echo "   c. Under Voice Configuration:"
echo "      - A call comes in: Select 'TwiML Bin'"
echo "      - Choose the bin you just created"
echo "   d. Save"
echo ""
echo "4. Start your voice agent:"
echo "   python voice_agent_telephony.py start"
echo ""
echo "5. Call your Twilio number to test!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📚 For detailed instructions, see: TWILIO_SETUP.md"
echo ""
