# Skill 03: LightRAG Setup (Knowledge Base)

## Objective
Set up LightRAG as the multi-tenant knowledge base system with graph-based RAG for voice agent queries.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      LightRAG Service                           │
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │   Web UI    │    │   REST API  │    │  Graph DB   │         │
│  │  (Upload)   │    │  /query     │    │ (Neo4j/     │         │
│  │             │    │  /documents │    │  NetworkX)  │         │
│  └─────────────┘    └──────┬──────┘    └─────────────┘         │
│                            │                                    │
│                            ▼                                    │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                  Embedding Engine                        │   │
│  │   ┌─────────┐   ┌─────────┐   ┌─────────┐              │   │
│  │   │ Ollama  │   │ OpenAI  │   │ Cohere  │              │   │
│  │   │ BGE-M3  │   │ ada-002 │   │ Embed   │              │   │
│  │   └─────────┘   └─────────┘   └─────────┘              │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                  LLM for Summarization                   │   │
│  │   ┌─────────┐   ┌─────────┐   ┌─────────┐              │   │
│  │   │ OpenAI  │   │ Gemini  │   │ Local   │              │   │
│  │   │ GPT-4o  │   │ Flash   │   │ Llama   │              │   │
│  │   └─────────┘   └─────────┘   └─────────┘              │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Deployment Options

LightRAG can be deployed locally (Docker) or in the cloud. Choose based on your needs:

| Option | Best For | Pros | Cons |
|--------|----------|------|------|
| **Local (Docker)** | Development, testing | Full control, no external costs | Requires local resources, no scaling |
| **Cloud (Managed)** | Production, scaling | High availability, managed infrastructure | Monthly costs, depends on provider |

---

## Option A: Local Deployment (Docker)

### A.1 Clone and Configure LightRAG

```bash
cd ~/voice-ai-platform

# Clone LightRAG
git clone https://github.com/HKUDS/LightRAG.git src/lightrag

cd src/lightrag
```

### A.2 Create Environment File

```bash
cat > .env << 'EOF'
# ===========================================
# LIGHTRAG CONFIGURATION
# ===========================================

# ----- Web UI -----
WEBUI_TITLE="Voice AI Knowledge Base"
WEBUI_DESCRIPTION="Multi-tenant RAG System"

# ----- Authentication -----
# Remove # to enable auth
AUTH_ACCOUNTS=admin:your-secure-password-here

# API Key for external access (n8n, agents)
LIGHTRAG_API_KEY=your-40-char-api-key-here

# ----- LLM Configuration -----
# Using OpenRouter for flexibility (supports many models)
LLM_BINDING=openai
LLM_MODEL=google/gemini-flash-1.5
LLM_BASE_URL=https://openrouter.ai/api/v1
LLM_API_KEY=your-openrouter-api-key

# Alternative: Direct OpenAI
# LLM_BINDING=openai
# LLM_MODEL=gpt-4o-mini
# LLM_API_KEY=your-openai-key

# Alternative: Local Ollama (slower but free)
# LLM_BINDING=ollama
# LLM_MODEL=llama3.2:latest
# LLM_BASE_URL=http://host.docker.internal:11434

# ----- Embedding Configuration -----
# Using local Ollama for embeddings (cost-effective)
EMBEDDING_BINDING=ollama
EMBEDDING_MODEL=bge-m3:latest
EMBEDDING_BASE_URL=http://host.docker.internal:11434

# Alternative: OpenAI embeddings
# EMBEDDING_BINDING=openai
# EMBEDDING_MODEL=text-embedding-3-small
# EMBEDDING_API_KEY=your-openai-key

# ----- Reranker Configuration -----
RERANK_BINDING=ollama
RERANK_MODEL=bge-reranker-v2-m3
RERANK_BASE_URL=http://host.docker.internal:11434
MIN_RERANK_SCORE=0.1

# ----- Summary Language -----
SUMMARY_LANGUAGE=English

# ----- Storage -----
# Default uses local file storage
# For production, consider PostgreSQL + vector storage
# POSTGRES_HOST=localhost
# POSTGRES_PORT=5432
# POSTGRES_DB=lightrag
# POSTGRES_USER=postgres
# POSTGRES_PASSWORD=postgres
EOF
```

---

### A.3 Pull Ollama Models

```bash
# Make sure Ollama is running
ollama serve &

# Pull embedding model
ollama pull bge-m3:latest

# Pull reranker model
ollama pull bge-reranker-v2-m3

# Verify models
ollama list
```

---

### A.4 Start LightRAG with Docker

```bash
cd ~/voice-ai-platform/src/lightrag

# Start LightRAG
docker compose up -d

# Check logs
docker compose logs -f

# Verify it's running
curl http://localhost:9621/health
```

---

### A.5 Access and Test Web UI

1. Open: http://localhost:9621
2. Login with credentials from `AUTH_ACCOUNTS`
3. Upload a test document (PDF, TXT, or MD)
4. Wait for processing to complete
5. Go to **Retrieval** tab and test a query
6. Check **Knowledge Graph** tab to see the generated graph

---

## Option B: Cloud Deployment

For production deployments, you can run LightRAG on cloud infrastructure with managed databases.

### B.1 Cloud Infrastructure Options

| Provider | Setup | Best For |
|----------|-------|----------|
| **AWS EC2 + RDS** | EC2 for LightRAG, RDS for PostgreSQL | Enterprise, high availability |
| **GCP Cloud Run** | Serverless container | Auto-scaling, pay-per-use |
| **Azure Container Apps** | Managed containers | Microsoft ecosystem |
| **DigitalOcean Droplet** | Simple VM | Small-medium deployments |

### B.2 AWS Deployment Example

```bash
# 1. Create EC2 instance (t3.medium or larger)
# 2. Install Docker on EC2
# 3. Set up RDS PostgreSQL instance

# SSH to EC2 and deploy
ssh -i your-key.pem ec2-user@your-ec2-ip

# Clone and configure
git clone https://github.com/HKUDS/LightRAG.git
cd LightRAG

# Create production .env
cat > .env << 'EOF'
# Production LightRAG Config
WEBUI_TITLE="Voice AI Knowledge Base"

# Use OpenAI for LLM (recommended for cloud)
LLM_BINDING=openai
LLM_MODEL=gpt-4o-mini
LLM_API_KEY=${OPENAI_API_KEY}

# Use OpenAI for embeddings (no local Ollama needed)
EMBEDDING_BINDING=openai
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_API_KEY=${OPENAI_API_KEY}

# PostgreSQL (RDS)
POSTGRES_HOST=${RDS_ENDPOINT}
POSTGRES_PORT=5432
POSTGRES_DB=lightrag
POSTGRES_USER=lightrag_user
POSTGRES_PASSWORD=${RDS_PASSWORD}

# API Security
LIGHTRAG_API_KEY=${LIGHTRAG_API_KEY}
AUTH_ACCOUNTS=admin:${ADMIN_PASSWORD}
EOF

# Run with Docker
docker compose up -d
```

### B.3 GCP Cloud Run Deployment

```bash
# Build and push container
gcloud builds submit --tag gcr.io/YOUR_PROJECT/lightrag

# Deploy to Cloud Run
gcloud run deploy lightrag \
  --image gcr.io/YOUR_PROJECT/lightrag \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "LLM_BINDING=openai,LLM_MODEL=gpt-4o-mini" \
  --set-secrets "LLM_API_KEY=openai-key:latest,LIGHTRAG_API_KEY=lightrag-key:latest"
```

### B.4 Environment Variables for Cloud

```bash
# Add to your cloud secrets/environment:
LIGHTRAG_URL=https://your-lightrag-domain.com  # Update in main app .env
LIGHTRAG_API_KEY=your-production-api-key
```

---

## Step 6: API Integration

### 6.1 Query Endpoint

```bash
# Test query endpoint
curl -X POST http://localhost:9621/query \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -H "X-API-Key: your-lightrag-api-key" \
  -d '{
    "query": "What are the main topics covered?",
    "mode": "mix"
  }'
```

### 6.2 Add Text Endpoint

```bash
# Add text to knowledge base
curl -X POST http://localhost:9621/documents/text \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -H "X-API-Key: your-lightrag-api-key" \
  -d '{
    "text": "The Voice AI Platform supports healthcare and hospitality verticals..."
  }'
```

### 6.3 Query Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| `local` | Only local context | Simple factual queries |
| `global` | High-level summaries | Overview questions |
| `hybrid` | Combination | General queries |
| `mix` | All modes combined | Best for voice agents |

---

## Step 7: Multi-Tenant Setup (Optional)

For multi-tenant isolation, you can run multiple LightRAG instances or use workspaces.

### Option A: Multiple Instances (Recommended)

```yaml
# docker-compose.multi-tenant.yml
version: '3.8'
services:
  lightrag-tenant-a:
    image: lightrag:latest
    ports:
      - "9621:9621"
    environment:
      - LIGHTRAG_API_KEY=${TENANT_A_API_KEY}
    volumes:
      - lightrag_tenant_a:/app/data

  lightrag-tenant-b:
    image: lightrag:latest
    ports:
      - "9622:9621"
    environment:
      - LIGHTRAG_API_KEY=${TENANT_B_API_KEY}
    volumes:
      - lightrag_tenant_b:/app/data

volumes:
  lightrag_tenant_a:
  lightrag_tenant_b:
```

### Option B: Workspace Prefixes

If using a single instance, prefix document IDs with tenant ID:

```python
# In n8n or backend, prefix queries
tenant_id = "tenant_abc"
query_with_filter = f"[{tenant_id}] What are the check-in hours?"
```

---

## Step 8: Backend Integration Service

Create `services/kb_service.py`:

```python
# src/backend/app/services/kb_service.py
import httpx
from typing import Optional, Dict, Any, List
from app.core.config import settings


class KnowledgeBaseService:
    """Service for interacting with LightRAG."""
    
    def __init__(self, base_url: str = None, api_key: str = None):
        self.base_url = base_url or settings.LIGHTRAG_URL
        self.api_key = api_key or settings.LIGHTRAG_API_KEY
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-API-Key": self.api_key,
        }
    
    async def query(
        self, 
        query: str, 
        mode: str = "mix",
        tenant_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Query the knowledge base.
        
        Args:
            query: The question to ask
            mode: Query mode (local, global, hybrid, mix)
            tenant_id: Optional tenant filter
        
        Returns:
            Dict with 'response' and optionally 'sources'
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/query",
                headers=self.headers,
                json={
                    "query": query,
                    "mode": mode,
                }
            )
            response.raise_for_status()
            return response.json()
    
    async def add_text(
        self, 
        text: str,
        metadata: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Add text content to the knowledge base."""
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/documents/text",
                headers=self.headers,
                json={
                    "text": text,
                    "metadata": metadata or {},
                }
            )
            response.raise_for_status()
            return response.json()
    
    async def get_documents(self) -> List[Dict[str, Any]]:
        """Get list of documents in the knowledge base."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.base_url}/documents",
                headers=self.headers,
            )
            response.raise_for_status()
            return response.json()
    
    async def health_check(self) -> bool:
        """Check if LightRAG is healthy."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except Exception:
            return False


# Singleton instance
kb_service = KnowledgeBaseService()
```

---

## Step 9: Create KB API Routes

Create `api/routes/knowledge_base.py`:

```python
# src/backend/app/api/routes/knowledge_base.py
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from typing import List, Optional
from pydantic import BaseModel

from app.api.deps import get_current_active_user, CurrentUser, require_permission
from app.services.kb_service import kb_service

router = APIRouter(prefix="/kb", tags=["Knowledge Base"])


class QueryRequest(BaseModel):
    query: str
    mode: str = "mix"


class QueryResponse(BaseModel):
    response: str
    sources: Optional[List[dict]] = None


class AddTextRequest(BaseModel):
    text: str
    metadata: Optional[dict] = None


@router.post("/query", response_model=QueryResponse)
async def query_knowledge_base(
    request: QueryRequest,
    current_user: CurrentUser = Depends(require_permission("kb:query")),
):
    """Query the knowledge base."""
    try:
        result = await kb_service.query(
            query=request.query,
            mode=request.mode,
            tenant_id=str(current_user.tenant.id) if current_user.tenant else None,
        )
        return QueryResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/documents/text")
async def add_text_to_kb(
    request: AddTextRequest,
    current_user: CurrentUser = Depends(require_permission("kb:write")),
):
    """Add text content to the knowledge base."""
    try:
        result = await kb_service.add_text(
            text=request.text,
            metadata=request.metadata,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents")
async def list_documents(
    current_user: CurrentUser = Depends(require_permission("kb:read")),
):
    """List all documents in the knowledge base."""
    try:
        return await kb_service.get_documents()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def kb_health():
    """Check knowledge base health."""
    healthy = await kb_service.health_check()
    if not healthy:
        raise HTTPException(status_code=503, detail="LightRAG not available")
    return {"status": "healthy"}
```

---

## Step 10: Document Types to Upload

### Healthcare Tenant
- Appointment booking procedures
- Insurance information
- Doctor specialties and availability
- FAQ about services
- Patient intake forms (as reference)

### Hospitality Tenant
- Check-in/check-out procedures
- Room types and amenities
- Restaurant menus and hours
- Spa services and booking
- Local attractions and recommendations
- Hotel policies (pets, smoking, etc.)

---

## Verification Checklist

- [ ] LightRAG container running (`docker ps`)
- [ ] Web UI accessible at http://localhost:9621
- [ ] Can upload documents
- [ ] Documents process successfully
- [ ] Knowledge graph shows connections
- [ ] API queries return results
- [ ] Backend service can connect

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| Ollama connection failed | Docker networking | Use `host.docker.internal:11434` |
| Slow processing | Using local LLM | Switch to OpenRouter/OpenAI |
| Empty results | Documents not processed | Wait for processing to complete |
| 401 Unauthorized | Wrong API key | Check `LIGHTRAG_API_KEY` in .env |
| Graph empty | No entities extracted | Check document content quality |

---

## Next Step

Proceed to: `.claude/skills/04-N8N-MCP-SERVER.md`
