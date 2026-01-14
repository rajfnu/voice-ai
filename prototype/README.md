# LiveKit Prototype

Simple prototype to test LiveKit locally before building the full Voice AI platform.

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

### 3. Run Test

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

## What This Tests

1. **Server Connection** - Verifies LiveKit is running and accessible
2. **Room Management** - Creates and lists rooms
3. **Token Generation** - Creates JWT tokens for client authentication
4. **API Functionality** - Tests the LiveKit API client

## Next Steps

Once this works, you can:
- Add voice agent functionality (see skill 06)
- Connect Deepgram for STT
- Add Cartesia for TTS
- Integrate with telephony (SIP trunk)

## Configuration

All settings in `.env`:
- `LIVEKIT_URL` - Server URL (default: http://localhost:7880)
- `LIVEKIT_API_KEY` - API key (default: devkey)
- `LIVEKIT_API_SECRET` - API secret (default: secret)

⚠️ These are development credentials only! Change for production.

## Troubleshooting

**"Connection refused"**
- Check if Docker container is running: `docker compose ps`
- Check logs: `docker compose logs livekit`

**"Authentication failed"**
- Verify API key/secret in `.env` match `livekit.yaml`

**Port already in use**
- Change port 7880 in both `docker-compose.yml` and `.env`

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
