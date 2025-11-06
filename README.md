# HLCS - High-Level Consciousness System

**Version**: 1.0.0  
**API Protocol**: gRPC + REST (dual)  
**Integration**: SARAi MCP Server

---

## 🎯 Overview

HLCS is the **strategic orchestration layer** for SARAi AGI. It provides:

- **API-first design** with gRPC as primary protocol
- **Custom orchestrator** (no LangGraph/CrewAI bloat)
- **Multi-modal intelligence** (text, vision, audio)
- **Iterative refinement** until quality threshold
- **MCP integration** with SARAi tools

**Architecture**:
```
┌─────────────────────────────────────┐
│         HLCS (Port 4000/4001)       │
│  ┌───────────────────────────────┐  │
│  │  gRPC Server (4000)           │  │  ← Production
│  │  REST Gateway (4001)          │  │  ← Debug/Web
│  └───────────────────────────────┘  │
│  ┌───────────────────────────────┐  │
│  │  Custom Orchestrator          │  │
│  │  - Classify complexity        │  │
│  │  - Route (simple/complex)     │  │
│  │  - Refine iteratively         │  │
│  └───────────────────────────────┘  │
│  ┌───────────────────────────────┐  │
│  │  SARAi MCP Client (gRPC)      │  │
│  │  → saul.respond               │  │
│  │  → vision.analyze             │  │
│  │  → rag.search                 │  │
│  │  → memory.store               │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
                │
                ▼
      ┌─────────────────┐
      │  SARAi MCP      │
      │  Server (3000)  │
      └─────────────────┘
```

---

## 🚀 Quick Start

### 1. Prerequisites

```bash
# Python 3.12+
python --version

# Install gRPC tools
pip install grpcio grpcio-tools

# Clone repo
git clone https://github.com/iagenerativa/hlcs.git
cd hlcs
```

### 2. Generate gRPC Code from Proto

```bash
# Generate Python stubs
python -m grpc_tools.protoc \
  -I./proto \
  --python_out=./src/hlcs/grpc_server \
  --grpc_python_out=./src/hlcs/grpc_server \
  ./proto/hlcs.proto ./proto/sarai_mcp.proto
```

### 3. Configure Environment

```bash
cp .env.example .env

# Edit .env
SARAI_MCP_URL=http://localhost:3000
HLCS_GRPC_PORT=4000
HLCS_REST_PORT=4001
COMPLEXITY_THRESHOLD=0.5
QUALITY_THRESHOLD=0.7
MAX_ITERATIONS=3
```

### 4. Run with Docker

```bash
# Build
docker-compose build

# Run HLCS + SARAi
docker-compose up
```

**Or run locally**:
```bash
# Install dependencies
pip install -r requirements.txt

# Run gRPC server
python -m src.hlcs.grpc_server.server

# In another terminal, run REST gateway
python -m src.hlcs.rest_gateway.server
```

---

## 📡 API Usage

### gRPC (Production)

```python
import grpc
from hlcs_pb2 import QueryRequest, ProcessingOptions
from hlcs_pb2_grpc import HLCSStub

# Connect
channel = grpc.insecure_channel('localhost:4000')
client = HLCSStub(channel)

# Simple query
request = QueryRequest(
    query="¿Qué tiempo hace hoy?",
    options=ProcessingOptions(quality_threshold=0.8)
)

response = client.ProcessQuery(request)
print(f"Result: {response.result}")
print(f"Quality: {response.quality_score}")
print(f"Time: {response.processing_time_ms}ms")
```

### REST (Debug/Web)

```bash
# Simple query
curl -X POST http://localhost:4001/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Explica qué es un agujero negro",
    "options": {
      "quality_threshold": 0.8,
      "max_iterations": 3
    }
  }'

# Multimodal query (with image)
curl -X POST http://localhost:4001/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "¿Qué hay en esta imagen?",
    "image_url": "https://example.com/image.jpg",
    "options": {"strategy": "multimodal"}
  }'

# Status
curl http://localhost:4001/api/v1/status

# Capabilities
curl http://localhost:4001/api/v1/capabilities
```

### Streaming (gRPC)

```python
# Long-running query with streaming
request = QueryRequest(
    query="Analiza este paper de 50 páginas...",
    options=ProcessingOptions(enable_streaming=True)
)

for chunk in client.ProcessQueryStream(request):
    if chunk.type == QueryStreamChunk.STATUS:
        print(f"Status: {chunk.content}")
    elif chunk.type == QueryStreamChunk.PARTIAL_RESULT:
        print(f"Partial: {chunk.content}")
    elif chunk.type == QueryStreamChunk.FINAL_RESULT:
        print(f"Final: {chunk.content}")
        break
```

---

## 🧠 Orchestration Logic

### 1. Complexity Classification

```
Query → TRM Classifier (SARAi) → Complexity Score (0.0-1.0)

< 0.5: Simple  → SAUL direct response
≥ 0.5: Complex → RAG research + synthesis
```

### 2. Modality Detection

```
has_image OR has_audio → Multimodal workflow
  → Vision analysis / Audio transcription
  → Research (if complex)
  → Synthesis
```

### 3. Refinement Loop

```
While quality_score < threshold AND iterations < max:
  1. Evaluate quality (LLM-as-judge)
  2. Identify issues
  3. Refine response
  4. Re-evaluate
```

**Example flow**:
```
Query: "Explica agujeros negros"
  ↓
Complexity: 0.75 (complex)
  ↓
RAG Search → 5 results
  ↓
LLM Synthesis → Quality: 0.65 (below 0.7)
  ↓
Refinement Iteration 1 → Quality: 0.78 ✓
  ↓
Return result (2 iterations, 8.2s)
```

---

## 🏗️ Project Structure

```
hlcs/
├── proto/
│   ├── hlcs.proto              # Main API (gRPC)
│   └── sarai_mcp.proto         # SARAi client protocol
│
├── src/hlcs/
│   ├── __init__.py
│   ├── orchestrator.py         # Core logic (~250 LOC)
│   ├── mcp_client.py           # SARAi MCP client (gRPC)
│   │
│   ├── grpc_server/
│   │   ├── __init__.py
│   │   ├── server.py           # gRPC server
│   │   ├── hlcs_pb2.py         # Generated
│   │   └── hlcs_pb2_grpc.py    # Generated
│   │
│   ├── rest_gateway/
│   │   ├── __init__.py
│   │   └── server.py           # FastAPI gateway
│   │
│   ├── reasoning/
│   │   └── __init__.py         # Future: reasoning modules
│   │
│   ├── planning/
│   │   └── __init__.py         # Future: planning logic
│   │
│   └── metacognition/
│       └── __init__.py         # Future: self-reflection
│
├── tests/
│   ├── test_orchestrator.py
│   ├── test_grpc_api.py
│   ├── test_mcp_client.py
│   └── test_e2e.py
│
├── config/
│   └── hlcs.yaml
│
├── scripts/
│   ├── generate_proto.sh       # Generate gRPC stubs
│   └── test_grpc.sh            # gRPC health check
│
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🐳 Docker Deployment

**docker-compose.yml**:
```yaml
version: '3.8'

services:
  # SARAi MCP Server (prerequisite)
  sarai-core:
    image: sarai:core
    ports:
      - "3000:3000"
    environment:
      - MCP_ENABLED=true
    networks:
      - sarai-network

  # HLCS (High-Level Consciousness)
  hlcs:
    build: .
    ports:
      - "4000:4000"  # gRPC
      - "4001:4001"  # REST
    environment:
      - SARAI_MCP_URL=http://sarai-core:3000
      - HLCS_GRPC_PORT=4000
      - HLCS_REST_PORT=4001
      - COMPLEXITY_THRESHOLD=0.5
      - QUALITY_THRESHOLD=0.7
      - MAX_ITERATIONS=3
    depends_on:
      - sarai-core
    networks:
      - sarai-network
    healthcheck:
      test: ["CMD", "grpcurl", "-plaintext", "localhost:4000", "hlcs.HLCS/HealthCheck"]
      interval: 30s
      timeout: 10s
      retries: 3

networks:
  sarai-network:
    driver: bridge
```

---

## 📊 Performance Metrics

| Metric | Target | Actual (estimated) |
|--------|--------|-------------------|
| **gRPC Latency** | < 100ms | ~50ms (routing only) |
| **REST Latency** | < 150ms | ~80ms (+ transcoding) |
| **Simple Query E2E** | < 500ms | ~300ms (SAUL direct) |
| **Complex Query E2E** | < 10s | ~8s (RAG + synthesis) |
| **Multimodal E2E** | < 15s | ~12s (vision + research) |
| **Quality Score** | ≥ 0.7 | ~0.78 (avg) |
| **Throughput** | 100 req/s | ~80 req/s (single instance) |

---

## 🔒 Security

- **gRPC TLS**: Production deployment uses TLS certificates
- **API Keys**: Optional authentication via metadata
- **Rate Limiting**: 100 req/min per client (configurable)
- **Input Validation**: Pydantic models for all inputs
- **Timeout Protection**: Default 30s per query

---

## 🧪 Testing

```bash
## Testing

### Unit Tests
```bash
# Run all tests
pytest

# With coverage
pytest --cov=hlcs --cov-report=html

# Specific test file
pytest tests/test_orchestrator.py -v
```

### E2E Integration Tests

**Automated E2E Test** (recommended):
```bash
# Runs mock SARAi server + full integration tests
bash scripts/test_e2e.sh
```

This script:
1. Starts a mock SARAi MCP Server
2. Runs 10 comprehensive E2E tests
3. Validates HLCS ↔ SARAi integration
4. Cleans up automatically

**Manual E2E Test**:
```bash
# Terminal 1: Start mock SARAi server
python tests/mock_sarai_server.py

# Terminal 2: Run E2E tests
export SARAI_MCP_URL="http://localhost:3100"
pytest tests/test_e2e_integration.py -v -s
```

**Test Coverage**:
- ✅ Connectivity HLCS ↔ SARAi
- ✅ Direct tool calls (SAUL, TRM, RAG, Vision)
- ✅ Workflows (simple, complex, multimodal)
- ✅ Quality refinement loop
- ✅ Error handling and fallbacks
- ✅ Multi-turn conversations
- ✅ Performance benchmarks

**Results**: 10/10 tests passing ✅ (see `TESTING_REPORT.md` for details)

---


```

---

## 📈 Roadmap

### v1.0 (Current) ✅
- [x] API-first gRPC design
- [x] Custom orchestrator
- [x] SARAi MCP integration
- [x] Dual gRPC/REST servers
- [x] Docker deployment

### v1.1 (Next)
- [ ] Reasoning modules (causal, analogical)
- [ ] Planning engine (goal decomposition)
- [ ] Metacognition (self-monitoring)
- [ ] LangGraph integration (optional, for complex workflows)
- [ ] CrewAI integration (optional, for multi-agent)

### v1.2 (Future)
- [ ] Autonomous learning loop
- [ ] Fine-tuning pipeline integration
- [ ] Multi-tenancy support
- [ ] Distributed tracing (OpenTelemetry)

---

## 🤝 Contributing

See `CONTRIBUTING.md` for development guidelines.

**Key principles**:
- **API-first**: Proto changes before implementation
- **Tests required**: >80% coverage
- **No heavy frameworks**: Keep orchestrator custom
- **gRPC primary**: REST is a gateway, not core

---

## 📄 License

MIT License - See `LICENSE`

---

## 🙏 Credits

- **SARAi Team**: Core AGI platform
- **gRPC**: High-performance RPC framework
- **FastAPI**: REST gateway

---

**Questions?** Open an issue or contact: team@iagenerativa.com
