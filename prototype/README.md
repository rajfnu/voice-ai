# LiveKit Voice AI Prototype

Simple prototype to test LiveKit and voice AI pipeline (STT→LLM→TTS) locally before building the full platform.

## Quick Start

### 1. Start LiveKit Server

```bash
docker compose up -d
```

Wait ~10 seconds for the server to start, then verify:

```bash
docker compose logs livekit
```

You should see: `"msg":"starting LiveKit server"`

### 2. Install Python Dependencies

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure API Keys

```bash
cp .env.example .env
# Edit .env and add your API keys:
# - DEEPGRAM_API_KEY (get from https://console.deepgram.com)
# - OPENAI_API_KEY (get from https://platform.openai.com/api-keys)
# - CARTESIA_API_KEY (get from https://cartesia.ai)
```

### 4. Run Basic Test

Test LiveKit server connectivity:

```bash
python test_livekit.py
```

Expected output:
```
🔗 Connecting to LiveKit at: http://localhost:7880
📦 Test 1: Creating a room...
✅ Room created: test-room-001
📋 Test 2: Listing all rooms...
✅ Found 1 room(s)
🎫 Test 3: Generating access token...
✅ Token generated
🎉 All tests passed!
```

### 5. Test Voice Agent (Optional)

If you have API keys configured, test the voice agent setup:

```bash
python test_voice_agent.py
```

Then start the voice agent:

```bash
python voice_agent.py dev
```

The agent will wait for participants to join. You can test it by:
- Using the LiveKit web client at https://meet.livekit.io/custom
- Using the token provided by `test_voice_agent.py`
- Speaking into your microphone to interact with the AI

## What This Tests

### Basic Infrastructure (`test_livekit.py`)
1. **Server Connection** - Verifies LiveKit is running and accessible
2. **Room Management** - Creates and lists rooms
3. **Token Generation** - Creates JWT tokens for client authentication
4. **API Functionality** - Tests the LiveKit API client

### Voice AI Pipeline (`voice_agent.py`)
1. **Speech-to-Text** - Deepgram transcribes your voice
2. **Large Language Model** - GPT-4o generates responses
3. **Text-to-Speech** - Cartesia converts responses to natural voice
4. **Real-time Audio** - LiveKit handles the audio streaming

## Configuration

All settings in `.env`:

**LiveKit Server:**
- `LIVEKIT_URL` - Server URL (default: http://localhost:7880)
- `LIVEKIT_API_KEY` - API key (default: devkey)
- `LIVEKIT_API_SECRET` - API secret (default: secret)

**AI Services (required for voice agent):**
- `DEEPGRAM_API_KEY` - Speech-to-Text API key
- `OPENAI_API_KEY` - GPT-4 API key
- `CARTESIA_API_KEY` - Text-to-Speech API key

⚠️ Development LiveKit credentials only! Change for production.

## Project Structure

```
prototype/
├── docker-compose.yml      # LiveKit server config
├── livekit.yaml           # Server settings
├── requirements.txt       # Python dependencies
├── .env.example          # Environment template
├── .env                  # Your API keys (not in git)
├── test_livekit.py       # Basic LiveKit connectivity test
├── test_voice_agent.py   # Voice agent setup test
├── voice_agent.py        # Full voice AI agent
└── README.md            # This file
```

## Troubleshooting

**"Connection refused"**
- Check if Docker container is running: `docker compose ps`
- Check logs: `docker compose logs livekit`

**"Authentication failed"**
- Verify API key/secret in `.env` match `livekit.yaml`

**Port already in use**
- Change port 7880 in both `docker-compose.yml` and `.env`

**"Missing required environment variables"**
- Copy `.env.example` to `.env`
- Add your API keys from Deepgram, OpenAI, and Cartesia

**Voice agent doesn't respond**
- Check that all API keys are valid
- Verify you have credits/quota on each service
- Check agent logs for errors

## Clean Up

Stop server:
```bash
docker compose down
```

Remove everything:
```bash
docker compose down -v
cd .. && rm -rf prototype
```
