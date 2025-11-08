# HLCS AGI System - Usage Examples

Ejemplos prácticos de uso del sistema AGI.

---

## 🎯 Ejemplo 1: AGI Standalone

Usar el sistema AGI directamente sin MCP.

```python
import asyncio
from hlcs.agi_system import Phi4MiniAGI

async def main():
    # Inicializar AGI
    agi = Phi4MiniAGI(
        model_path="./models/phi4_mini_q4.gguf",
        rag_docs="./data/codebase.py",
        memory_path="./data/memory/episodes.json"
    )
    
    # Query simple (usa RAG + LLM)
    result = await agi.process(
        query="¿Qué es HLCS?",
        user_id="user_123",
        session_id="session_1"
    )
    
    print(f"Answer: {result['answer']}")
    print(f"Strategy: {result['strategy']}")  # → "simple"
    print(f"Latency: {result['latency_ms']}ms")  # → ~300ms
    
    # Query complejo (usa agente)
    result = await agi.process(
        query="Create a REST API endpoint with JWT authentication",
        user_id="user_123",
        session_id="session_1"
    )
    
    print(f"Answer: {result['answer']}")
    print(f"Strategy: {result['strategy']}")  # → "complex"
    print(f"Latency: {result['latency_ms']}ms")  # → ~8s
    
    # Ver memoria
    memory = agi.get_recent_memory(5)
    print(f"\nRecent memory: {len(memory)} episodes")

asyncio.run(main())
```

---

## 🔗 Ejemplo 2: Integrado con Orchestrator

Usar AGI dentro del orchestrator completo.

```python
import asyncio
from hlcs.orchestrator import HLCSOrchestrator
from hlcs.mcp_client import SARAiMCPClient
from hlcs.agi_system import Phi4MiniAGI

async def main():
    # Setup
    agi = Phi4MiniAGI(
        model_path="./models/phi4_mini_q4.gguf",
        rag_docs="./data/codebase.py",
        memory_path="./data/memory/episodes.json"
    )
    
    sarai = SARAiMCPClient("http://localhost:3000")
    await sarai.__aenter__()
    
    orchestrator = HLCSOrchestrator(
        sarai_client=sarai,
        agi_system=agi,
        enable_agi=True
    )
    
    # Test diferentes tipos de queries
    
    # 1. Simple → Usa MCP SAUL
    result = await orchestrator.process("Hola, ¿cómo estás?")
    print(f"Strategy: {result['strategy']}")  # → "simple"
    
    # 2. Complex → Usa MCP RAG+LLM
    result = await orchestrator.process("Explica qué son los agujeros negros")
    print(f"Strategy: {result['strategy']}")  # → "complex"
    
    # 3. AGI-Enhanced → Usa AGI local
    result = await orchestrator.process(
        "Implement a Python class for JWT token validation"
    )
    print(f"Strategy: {result['strategy']}")  # → "agi_enhanced"
    
    # Cleanup
    await sarai.close()

asyncio.run(main())
```

---

## 🌐 Ejemplo 3: Via REST API

Usar el sistema desde cualquier lenguaje via HTTP.

### Python (requests)

```python
import requests

# Simple query
response = requests.post(
    "http://localhost:4001/api/v1/query",
    json={
        "query": "¿Qué es HLCS?",
        "user_id": "user_123",
        "session_id": "session_1"
    }
)

data = response.json()
print(f"Result: {data['result']}")
print(f"Strategy: {data['strategy']}")
print(f"Quality: {data['quality_score']}")

# Complex query con AGI
response = requests.post(
    "http://localhost:4001/api/v1/query",
    json={
        "query": "Create a Python function to validate email addresses",
        "user_id": "user_123",
        "session_id": "session_1",
        "options": {
            "quality_threshold": 0.8
        }
    }
)

data = response.json()
print(f"Result: {data['result']}")
print(f"Strategy: {data['strategy']}")  # → "agi_enhanced"
```

### cURL

```bash
# Simple
curl -X POST http://localhost:4001/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "¿Qué es HLCS?"}'

# Complex con AGI
curl -X POST http://localhost:4001/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Implement a REST API with JWT authentication",
    "user_id": "dev_001",
    "session_id": "dev_session"
  }'
```

### JavaScript (fetch)

```javascript
// Simple query
const response = await fetch('http://localhost:4001/api/v1/query', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    query: '¿Qué es HLCS?',
    user_id: 'user_123',
    session_id: 'session_1'
  })
});

const data = await response.json();
console.log('Result:', data.result);
console.log('Strategy:', data.strategy);
```

---

## 💾 Ejemplo 4: Memoria Episódica

Trabajar directamente con memoria.

```python
from hlcs.memory.episodic_memory import MemoryBuffer

# Crear buffer
memory = MemoryBuffer(
    max_size=1000,
    persist_path="./data/memory/custom.json",
    auto_save=True
)

# Agregar episodios
memory.add(
    query="¿Cómo implemento JWT?",
    answer="JWT se implementa con PyJWT...",
    session_id="session_1",
    user_id="user_123",
    metadata={"project": "auth_system"}
)

# Obtener recientes
recent = memory.get_recent(10)
for ep in recent:
    print(f"{ep.timestamp}: {ep.query}")

# Filtrar por sesión
session_eps = memory.get_by_session("session_1")
print(f"Session has {len(session_eps)} episodes")

# Filtrar por usuario
user_eps = memory.get_by_user("user_123")
print(f"User has {len(user_eps)} episodes")

# Stats
stats = memory.get_stats()
print(f"Memory usage: {stats['usage_percent']}%")

# Guardar explícitamente
memory.save()
```

---

## 🔍 Ejemplo 5: RAG Retrieval

Usar RAG directamente.

```python
from hlcs.memory.rag import KnowledgeRAG

# Inicializar RAG
rag = KnowledgeRAG("./data/codebase.py")

print(f"Loaded {len(rag)} chunks")

# Buscar contexto relevante
results = rag.retrieve(
    query="How to implement JWT authentication?",
    top_k=3
)

print(f"\nTop {len(results)} results:")
for i, chunk in enumerate(results, 1):
    print(f"\n=== Chunk {i} ===")
    print(chunk[:200] + "...")
```

---

## 🤖 Ejemplo 6: CodeAgent

Usar el agente directamente.

```python
from hlcs.planning.agentes import CodeAgent
from hlcs.memory.rag import KnowledgeRAG
from llama_cpp import Llama

# Setup
llm = Llama(model_path="./models/phi4_mini_q4.gguf", n_ctx=4096)
rag = KnowledgeRAG("./data/codebase.py")

# Crear agente (sin sandbox por seguridad)
agent = CodeAgent(llm, rag, enable_sandbox=False)

# Ejecutar tarea
result = agent.run(
    task="Search the codebase for JWT authentication examples",
    max_steps=5
)

print(f"Agent result:\n{result}")
```

---

## 🎛️ Ejemplo 7: Configuración Avanzada

Configurar el sistema para casos específicos.

### High Performance (GPU)

```yaml
# config/hlcs.yaml
agi:
  enabled: true
  
  model:
    path: "./models/phi4_mini_q4.gguf"
    n_ctx: 4096
    n_gpu_layers: -1  # Todas en GPU
    n_threads: 8
  
  rag:
    enabled: true
    docs_path: "./data/large_codebase.py"
    top_k: 5
  
  memory:
    max_size: 5000  # Buffer grande
    persist_path: "./data/memory/production.json"
```

### Low Memory (CPU only)

```yaml
# config/hlcs.yaml
agi:
  enabled: true
  
  model:
    path: "./models/phi4_mini_q4.gguf"
    n_ctx: 2048  # Contexto reducido
    n_gpu_layers: 0  # CPU only
    n_threads: 4
  
  rag:
    enabled: false  # Deshabilitado para ahorrar memoria
  
  memory:
    max_size: 500  # Buffer pequeño
```

### Development (Mock mode)

```yaml
# config/hlcs.yaml
agi:
  enabled: false  # Deshabilitado para dev sin modelo
  
development:
  mock_agi: true  # Usar mock
```

---

## 📊 Ejemplo 8: Monitoring

Monitorear el sistema en producción.

```python
import asyncio
import time
from hlcs.agi_system import Phi4MiniAGI

async def monitor_agi():
    agi = Phi4MiniAGI(...)
    
    while True:
        # Stats cada 60 segundos
        await asyncio.sleep(60)
        
        stats = agi.get_stats()
        memory_stats = agi.memory.get_stats()
        
        print(f"""
        === AGI Stats ===
        Total calls: {stats['total_calls']}
        Simple: {stats['simple_calls']} ({stats['simple_calls']/max(stats['total_calls'],1)*100:.1f}%)
        Complex: {stats['complex_calls']} ({stats['complex_calls']/max(stats['total_calls'],1)*100:.1f}%)
        Avg latency: {stats['avg_latency_ms']:.1f}ms
        Errors: {stats['errors']}
        
        === Memory Stats ===
        Episodes: {memory_stats['current_episodes']}/{memory_stats['max_size']}
        Usage: {memory_stats['usage_percent']:.1f}%
        Saves: {memory_stats['saves']}
        """)

asyncio.run(monitor_agi())
```

---

## 🚨 Ejemplo 9: Error Handling

Manejar errores gracefully.

```python
import asyncio
from hlcs.agi_system import Phi4MiniAGI

async def safe_query(agi, query):
    try:
        result = await agi.process(query)
        
        if result['status'] == 'success':
            return result['answer']
        else:
            print(f"Error: {result.get('error_details')}")
            return None
    
    except Exception as e:
        print(f"Exception: {e}")
        return None

async def main():
    agi = Phi4MiniAGI(...)
    
    # Queries with error handling
    queries = [
        "¿Qué es HLCS?",
        "Implement a complex system",  # Puede fallar
        "Search for authentication examples"
    ]
    
    for query in queries:
        result = await safe_query(agi, query)
        if result:
            print(f"✅ {query}: {result[:100]}...")
        else:
            print(f"❌ {query}: Failed")

asyncio.run(main())
```

---

## 🔄 Ejemplo 10: Batch Processing

Procesar múltiples queries eficientemente.

```python
import asyncio
from hlcs.agi_system import Phi4MiniAGI

async def process_batch(agi, queries):
    tasks = [
        agi.process(query, user_id="batch", session_id=f"batch_{i}")
        for i, query in enumerate(queries)
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    successful = sum(1 for r in results if isinstance(r, dict) and r['status'] == 'success')
    print(f"Processed {len(queries)} queries, {successful} successful")
    
    return results

async def main():
    agi = Phi4MiniAGI(...)
    
    queries = [
        "¿Qué es HLCS?",
        "Explica JWT",
        "Cómo usar FastAPI",
        # ... más queries
    ]
    
    results = await process_batch(agi, queries)
    
    for query, result in zip(queries, results):
        if isinstance(result, dict):
            print(f"✅ {query}: {result['strategy']}")
        else:
            print(f"❌ {query}: Error")

asyncio.run(main())
```

---

## 📖 Referencias

- **Documentación completa**: `docs/AGI_SETUP.md`
- **API Reference**: `.github/copilot-instructions.md`
- **Tests**: `examples/agi_complete_demo.py`

---

**¿Más ejemplos?** Contribuye en el repositorio! 🚀
