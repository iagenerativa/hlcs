# HLCS (High-Level Consciousness System) - AI Agent Instructions

## 🚨 IMPORTANT: Migration in Progress

**Status**: 🟡 sarai-agi component integration **AWAITING APPROVAL**

HLCS v3.0 is undergoing architectural analysis for integrating components from sarai-agi. Before making changes to core systems, review:

- **[docs/SARAI_AGI_MIGRATION_STATUS.md](../docs/SARAI_AGI_MIGRATION_STATUS.md)** - Current migration status
- **[docs/MIGRATION_CONFLICT_ANALYSIS.md](../docs/MIGRATION_CONFLICT_ANALYSIS.md)** - Collision analysis
- **[docs/ADR-001-MIGRATION-STRATEGY.md](../docs/ADR-001-MIGRATION-STRATEGY.md)** - Architecture decisions

**Components with Migration Conflicts** (DO NOT modify without reviewing ADR-001):
- ⚠️ `src/hlcs/metacognition/meta_consciousness.py` - Collision with IntegratedConsciousness v0.3
- ⚠️ `src/hlcs/planning/strategic_planner.py` - Collision with Meta-Reasoner v0.2
- ⚠️ `src/hlcs/memory/rag.py` - Partial collision with Active Learning v0.4

**Safe to Extend** (No conflicts):
- ✅ New emotion system (planned)
- ✅ Monitoring & observability (planned)
- ✅ REST API endpoints
- ✅ Tests and documentation

---

## Project Architecture

HLCS v3.0 is an **autonomous orchestration layer** for SARAi AGI with three-tier intelligence system:

1. **Meta-Consciousness Layer** (v0.2): Introspection engine that monitors decision-making, tracks uncertainty/ignorance, builds narrative understanding, and scores confidence in outputs
2. **Strategic Planning System** (v0.5): Goal-oriented planning with hierarchical goals, plan execution, progress tracking, scenario simulation, and hypothesis testing
3. **Multi-Stakeholder SCI** (v0.4): Consensus-based decision system with weighted voting (60% user, 30% admin, 10% agents)

The system acts as a **truly autonomous consciousness layer** that intelligently decides when to route queries to:
- **SARAi MCP Server** (external tools: SAUL, Vision, Audio, RAG, TRM)
- **Phi4MiniAGI System** (local LLM with memory, RAG, agent capabilities)
- **Ensemble Mode** (combines both approaches for critical decisions)

**Key Flow**: Client → REST/gRPC Gateway → Meta-Consciousness Analysis → SCI Consensus (if needed) → Component Routing → [SARAi MCP OR Phi4MiniAGI OR Ensemble] → Meta-Cognitive Quality Evaluation → Response

### Core Components

#### Meta-Consciousness Layer (v0.2)
- **`src/hlcs/metacognition/meta_consciousness.py`** (~800 LOC): Complete meta-cognitive system that:
  - **IgnoranceConsciousness**: Tracks what the system doesn't know (KNOWN_UNKNOWNS, UNKNOWN_UNKNOWNS, EPISTEMIC, ALEATORY)
  - **SelfDoubtScore**: Quantifies confidence in decisions with composite scoring (confidence, reasoning, evidence, uncertainty)
  - **NarrativeConsciousness**: Builds coherent narratives from episodic memories (learning, goals, patterns)
  - **TemporalContext**: Tracks context freshness and session duration
  - **MetaConsciousnessLayer**: Central coordination that analyzes context, decides component routing, and evaluates response quality
  - Supports 4 decision strategies: CONSERVATIVE, EXPLORATORY, BALANCED, ADAPTIVE

#### Strategic Planning System (v0.5)
- **`src/hlcs/planning/strategic_planner.py`** (~1000 LOC): Complete goal-oriented planning system:
  - **GoalManager**: Hierarchical goal tracking with priorities (CRITICAL/HIGH/MEDIUM/LOW) and dependencies
  - **PlanExecutor**: Decomposes goals into executable plans (sequential/parallel/hybrid strategies)
  - **ProgressTracker**: Milestone-based progress monitoring with achievement detection
  - **ScenarioSimulator**: What-if analysis for decision support before committing
  - **HypothesisTester**: Validates hypotheses through experimentation with Bayesian confidence updates
  - **StrategicPlanningSystem**: Central coordinator integrating all planning components

#### Multi-Stakeholder SCI (v0.4)
- **`src/hlcs/sci/multi_stakeholder.py`** (~600 LOC): Consensus-based decision system:
  - **MultiStakeholderSCI**: Central system coordinating weighted consensus (60% PRIMARY_USER, 30% ADMINISTRATOR, 10% AUTONOMOUS_AGENT)
  - **VotingStrategy**: Flexible voting mechanisms (WEIGHTED, SIMPLE_MAJORITY, SUPERMAJORITY, UNANIMOUS, ADAPTIVE)
  - **ConsensusBuilder**: Manages voting process and resolves conflicts (defer to primary user → admin → rejection)
  - **StakeholderContext**: Tracks stakeholder identity, preferences, agreement rates, and decision history
  - Auto-votes for autonomous agents based on system recommendations and risk assessment

#### Orchestration Layer
- **`src/hlcs/orchestrator.py`** (~900 LOC): Enhanced autonomous orchestration engine that:
  - Integrates Meta-Consciousness for intelligent routing decisions
  - Uses Strategic Planning for complex multi-step workflows
  - Employs Multi-Stakeholder SCI for consensus on critical decisions
  - Classifies complexity and detects modality (text/multimodal)
  - Routes to appropriate workflow: simple, complex, multimodal, agi_enhanced, or **ensemble**
  - Iteratively refines responses until quality threshold met (evaluated by meta-consciousness)
  - Decides between MCP tools, local AGI system, or ensemble based on meta-cognitive analysis
  - New workflows: `_ensemble_workflow()` combines AGI + SARAi, `_get_sci_consensus_routing()` for stakeholder approval

#### MCP Integration
- **`src/hlcs/mcp_client.py`** (~296 LOC): SARAi MCP Client v2.0 implementing Model Context Protocol standard (POST /tools/list, POST /tools/call, GET /health)
- **`src/hlcs/langchain_tools.py`**: Wrapper converting MCP tools to LangChain-compatible tools via `MCPToolWrapper` class

#### AGI System (NEW)
- **`src/hlcs/agi_system.py`** (~420 LOC): Phi4MiniAGI system that integrates:
  - **Phi-4-mini LLM** via llama-cpp-python (local inference)
  - **KnowledgeRAG v2.0** from `memory/rag.py` (ChromaDB + hierarchical memory)
  - **CodeAgent** from `planning/agentes.py` (ReAct pattern with tools)
  - **MemoryBuffer** from `memory/episodic_memory.py` (circular buffer with persistence)
  - Auto-decides between simple (RAG+LLM ~300ms) or complex (Agent+Tools ~8s) strategies

- **`src/hlcs/memory/rag.py`** (~650 LOC): **KnowledgeRAG v2.0** - Memoria externa persistente con:
  - **ChromaDB backend**: Persistencia en disco, no pierde memoria al reiniciar
  - **Embeddings**: all-MiniLM-L6-v2 (~50MB, queries rápidas)
  - **Memoria jerárquica**: Short-Term (24h TTL) ↔ Long-Term (permanente)
  - **Auto-consolidación**: STM → LTM basado en access_count y confidence
  - **Metadatos ricos**: knowledge_type (episodic/semantic/procedural), memory_tier, source, confidence_score, tags
  - **Filtros semánticos**: Búsqueda por metadata + semantic search
  - **LangChain integration**: Wrapper minimalista para orchestration
  - **Kubernetes-ready**: PersistentVolume, health checks, resource limits
  - Ver `docs/KNOWLEDGE_RAG_V2.md` para documentación completa

- **`src/hlcs/memory/episodic_memory.py`** (~370 LOC): Circular memory buffer with:
  - FIFO eviction when full
  - JSON persistence to disk
  - Session and user tracking
  - Optional semantic search via embeddings

- **`src/hlcs/memory/rag.py`** (~650 LOC): **KnowledgeRAG v2.0** - Complete RAG system with:
  - ChromaDB persistent backend (disk storage)
  - all-MiniLM-L6-v2 embeddings (~50MB, fast)
  - Hierarchical memory (STM 24h → LTM permanent)
  - Rich metadata (knowledge_type, memory_tier, confidence, tags)
  - Semantic + metadata filtering
  - Auto-consolidation every hour
  - Document loading utilities (function/paragraph/fixed chunking)
  - LangChain VectorStore integration
  
- **`src/hlcs/planning/agentes.py`**: ReAct agent with tools (codebase search, code execution, web search)

#### API Gateways
- **`src/hlcs/rest_gateway/server.py`** (~900 LOC): FastAPI gateway on port 4001 (production interface) with:
  - Core endpoints: `/api/v1/query`, `/api/v1/status`, `/api/v1/capabilities`
  - **NEW Strategic Planning endpoints**: `/api/v1/planning/goals`, `/api/v1/planning/plans`, `/api/v1/planning/plans/{id}/execute`
  - **NEW Multi-Stakeholder SCI endpoints**: `/api/v1/sci/stakeholders`, `/api/v1/sci/decisions`, `/api/v1/sci/votes`, `/api/v1/sci/decisions/{id}/consensus`
  - Automatic initialization of all autonomous systems (meta, planning, SCI) at startup
- **`src/hlcs/grpc_server/server.py`**: gRPC server on port 4000 (placeholder/future)

### Proto Definitions

Protocol buffers in `proto/` define gRPC contracts:
- **`hlcs.proto`**: Core HLCS API (ProcessQuery, ProcessQueryStream, GetStatus, ListCapabilities)
- **`sarai_mcp.proto`**: SARAi MCP integration types

Generate stubs: `bash scripts/generate_proto.sh` or `make proto`

## Development Workflows

### Running Locally (Recommended for Development)

```bash
# Start REST gateway only (no Docker)
make dev-rest
# Or: python -m src.hlcs.rest_gateway.server

# The server expects SARAi MCP at http://localhost:3000
# Configure via SARAI_MCP_URL env var or config/hlcs.yaml
```

**Why REST-first?** The REST gateway (`/api/v1/query`, `/api/v1/status`, `/health`) is the production-ready interface. gRPC is planned future expansion.

### Testing

```bash
# Run full test suite with coverage
make test
# Or: pytest tests/ -v --cov=src/hlcs

# Quick tests without coverage
make test-fast

# Test specific integration
pytest tests/test_mcp_client_integration.py -v
```

**Test Structure**: Tests use AsyncMock for `SARAiMCPClient` with side_effect to simulate tool call sequences. See `tests/test_orchestrator.py` for examples of mocking multi-step workflows (classify → search → synthesize).

### Docker

```bash
make build  # Build image
make up     # Start services (HLCS + SARAi)
make logs   # Follow logs
```

Docker expects SARAi MCP Server via `docker-compose.yml` service `sarai-core` on internal network.

## Critical Patterns

### Orchestrator Workflow Selection

The orchestrator (`HLCSOrchestrator.process()`) now has **four** workflow strategies:

1. **Simple** (complexity < 0.5): Direct SAUL response via MCP
2. **Complex** (complexity ≥ 0.5): RAG search → LLM synthesis via MCP
3. **Multimodal** (image_url/audio_url provided): Vision/audio analysis + synthesis
4. **AGI-Enhanced** (complexity ≥ 0.7 OR code keywords): Local Phi4MiniAGI system

**Selection logic** in `_should_use_agi()`:
- Uses AGI for: complexity ≥ 0.7, code-related queries ("create", "implement", "build", etc.)
- Skips AGI for: multimodal queries (uses specialized MCP tools instead)
- AGI system auto-decides between simple (RAG+LLM) or complex (ReAct agent) internally

State tracked in `HLCSState` dataclass with iterations, tool_calls, quality_score. Refinement loop continues until `quality_score >= quality_threshold` or `iterations >= max_iterations`.

### MCP Integration Pattern

All SARAi capabilities accessed via MCP protocol tools:

```python
async with SARAiMCPClient("http://localhost:3000") as client:
    # List available tools
    tools = await client.list_tools()  # Returns List[ToolDefinition]
    
    # Call a tool
    result = await client.call_tool("saul.respond", {"query": "hello"})
    # Returns: ToolCallResult(success=True, result={"text": "..."}, latency_ms=...)
```

**Available tools**: `saul.respond`, `saul.synthesize`, `vision.analyze`, `audio.transcribe`, `rag.search`, `trm.classify`

### AGI System Pattern (NEW)

Local AGI system for complex reasoning:

```python
from hlcs.agi_system import Phi4MiniAGI

# Initialize (typically once at startup)
agi = Phi4MiniAGI(
    model_path="./models/phi4_mini_q4.gguf",
    rag_docs="./data/codebase.py",
    memory_path="./data/memory/episodes.json"
)

# Process query
result = await agi.process(
    query="Create API endpoint with JWT auth",
    user_id="user_123",
    session_id="session_456"
)
# Returns: {"answer": "...", "strategy": "complex", "latency_ms": 8234, ...}
```

**AGI decides strategy automatically**:
- Simple queries → RAG retrieval + LLM direct (~300ms)
- Complex queries → ReAct agent with tools (~8s)

**Memory is automatic**: All interactions saved to `MemoryBuffer` with session/user context.

### Configuration Hierarchy

1. Environment variables (`.env` file, Docker env)
2. `config/hlcs.yaml` (structured config with sarai_mcp, agent, **agi**, langgraph sections)
3. Code defaults

Example AGI config in `hlcs.yaml`:
```yaml
agi:
  enabled: true
  model:
    path: "./models/phi4_mini_q4.gguf"
    n_ctx: 4096
    n_gpu_layers: -1
  rag:
    enabled: true
    docs_path: "./data/codebase.py"
  memory:
    max_size: 1000
    persist_path: "./data/memory/episodes.json"
```

## Project-Specific Conventions

### Async-First Design

All core operations are async. Use `asyncio` patterns:
- Client context managers: `async with SARAiMCPClient() as client`
- Test fixtures with `@pytest.mark.asyncio`
- AsyncMock for unit tests

### Logging Strategy

Use module-level loggers: `logger = logging.getLogger(__name__)`. Production logs via structured format (JSON in Docker, see `docker-compose.yml` LOG_FORMAT=json).

### Error Handling

Return errors in response structures rather than raising. See `QueryResponse` with `errors: list[str]` and `warnings: list[str]` fields. MCP client catches exceptions and returns `ToolCallResult(success=False, error=...)`

### Import Path Hack

Several scripts use: `sys.path.insert(0, ...)` to add `src/` to path. This is because package isn't installed in editable mode. For new scripts, follow pattern in `examples/agent_with_sarai_mcp.py`.

## Key Files for Understanding

- **`README.md`**: Architecture diagrams, API examples (gRPC + REST)
- **`docs/INTEGRACION_SARAI_MCP.md`**: Complete integration documentation (610 lines) with endpoints, examples, and architecture
- **`docs/RESUMEN_FINAL_INTEGRACION.md`**: Implementation summary, file inventory (~2900 LOC integration)
- **`QUICKSTART.md`**: Step-by-step local setup (REST-first approach)
- **`TESTING_REPORT.md`**: E2E test results with actual test scenarios

## External Dependencies

**SARAi MCP Server** (separate repo `sarai-agi`): Must be running on port 3000. Check health: `curl http://localhost:3000/health`

**Python 3.11+** required (3.12+ recommended for best performance). See `PYTHON_VERSION_STANDARD.md`

## Common Tasks

**Setup AGI system** (first time):
```bash
# Install AGI dependencies
pip install -r requirements-agi.txt

# Download Phi-4-mini model
mkdir -p models
wget https://huggingface.co/microsoft/phi-4/resolve/main/phi-4-mini-q4.gguf -O models/phi4_mini_q4.gguf

# Prepare directories
mkdir -p data/memory

# Configure in config/hlcs.yaml
# Set agi.enabled: true and paths
```

**Initialize orchestrator with AGI**:
```python
from hlcs.orchestrator import HLCSOrchestrator
from hlcs.mcp_client import SARAiMCPClient
from hlcs.agi_system import Phi4MiniAGI

# Create AGI system
agi = Phi4MiniAGI(
    model_path=config["agi"]["model"]["path"],
    rag_docs=config["agi"]["rag"]["docs_path"],
    memory_path=config["agi"]["memory"]["persist_path"]
)

# Create orchestrator with AGI
orchestrator = HLCSOrchestrator(
    sarai_client=sarai,
    agi_system=agi,
    enable_agi=True
)
```

**Add new orchestrator strategy**: Extend `HLCSOrchestrator._execute_*_workflow()` methods and update `process()` routing logic

**Add LangChain agent**: Use `create_sarai_tools()` from `langchain_tools.py` to get LangChain-compatible tools, see `examples/agent_with_sarai_mcp.py`

**Debug MCP issues**: Check `tests/mock_sarai_server.py` for mock server implementation showing expected request/response formats

**Debug AGI issues**: AGI runs in mock mode if llama-cpp-python not installed. Check logs for "Using mock LLM" warning.

**Update proto**: Edit `.proto` files → run `make proto` → regenerated stubs in `src/hlcs/grpc_server/generated/`

**Test memory persistence**: Check `data/memory/episodes.json` for saved episodes. Memory auto-saves every 10 episodes.

**Monitor AGI stats**: Call `agi.get_stats()` to see call counts, latencies, strategy usage (simple vs complex)
