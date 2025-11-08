# HLCS AGI System - Setup & Usage Guide

Sistema AGI completo basado en Phi-4-mini con RAG, memoria episódica y agentes.

## 🚀 Quick Start

### 1. Instalar Dependencias

```bash
# Básico (CPU)
pip install -r requirements-agi.txt

# Con CUDA (recomendado para producción)
CMAKE_ARGS="-DLLAMA_CUBLAS=on" pip install llama-cpp-python --force-reinstall --no-cache-dir
pip install -r requirements-agi.txt
```

### 2. Descargar Modelo Phi-4-mini

```bash
mkdir -p models
wget https://huggingface.co/microsoft/phi-4/resolve/main/phi-4-mini-q4.gguf -O models/phi4_mini_q4.gguf
```

**Alternativa**: Otros modelos GGUF compatibles:
- `phi-4-mini-q4.gguf` (2.3 GB, recomendado)
- `phi-4-mini-q8.gguf` (4.1 GB, más preciso)
- `phi-4-mini-fp16.gguf` (7.2 GB, máxima calidad)

### 3. Preparar Datos

```bash
# Crear directorios
mkdir -p data/memory

# RAG: Copiar tu codebase o documentos
cp -r /path/to/your/code data/codebase.py
# O usa un archivo concatenado con todo tu código
```

### 4. Configurar

Edita `config/hlcs.yaml`:

```yaml
agi:
  enabled: true
  
  model:
    path: "./models/phi4_mini_q4.gguf"
    n_ctx: 4096
    n_gpu_layers: -1  # -1 = todas en GPU, 0 = CPU only
  
  rag:
    enabled: true
    docs_path: "./data/codebase.py"
  
  memory:
    max_size: 1000
    persist_path: "./data/memory/episodes.json"
```

### 5. Ejecutar

```bash
# Opción A: REST Gateway (producción)
ENABLE_AGI=true python -m src.hlcs.rest_gateway.server

# Opción B: Demo standalone
python examples/agi_complete_demo.py

# Opción C: Usar desde código
python examples/agent_with_sarai_mcp.py
```

---

## 📚 Arquitectura

```
┌─────────────────────────────────────────────────────────┐
│                  Phi4MiniAGI System                     │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ Phi-4-mini   │  │ KnowledgeRAG │  │ CodeAgent    │ │
│  │ (llama.cpp)  │  │ (sentence-   │  │ (ReAct)      │ │
│  │              │  │ transformers)│  │              │ │
│  │ • n_ctx: 4K  │  │ • Chunks     │  │ • Tools      │ │
│  │ • GPU: -1    │  │ • Reranking  │  │ • Sandbox    │ │
│  │ • Q4 quant   │  │ • Top-K      │  │ • Web search │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │          MemoryBuffer (Episodic)                   │ │
│  │  • Circular buffer (1000 episodes)                 │ │
│  │  • JSON persistence                                │ │
│  │  • Session/user tracking                           │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### Estrategias de Decisión

El sistema **decide automáticamente** qué estrategia usar:

1. **Simple** (RAG + LLM directo, ~300ms):
   - Preguntas directas
   - Búsqueda de información
   - No requiere múltiples pasos

2. **Complex** (Agente ReAct, ~8s):
   - Keywords: "create", "implement", "build", etc.
   - Queries largos (>30 palabras)
   - Menciona "execute", "search", "tool"

---

## 💻 Uso desde Código

### Standalone

```python
from hlcs.agi_system import Phi4MiniAGI

# Inicializar
agi = Phi4MiniAGI(
    model_path="./models/phi4_mini_q4.gguf",
    rag_docs="./data/codebase.py",
    memory_path="./data/memory/episodes.json"
)

# Procesar query
result = await agi.process(
    query="¿Cómo implemento autenticación JWT?",
    user_id="user_123",
    session_id="session_456"
)

print(result["answer"])
# → Usa estrategia "simple" (RAG + LLM, ~300ms)

result = await agi.process(
    query="Create a REST API with JWT auth and logging to Datadog",
    user_id="user_123",
    session_id="session_456"
)

print(result["answer"])
# → Usa estrategia "complex" (agente, ~8s)
```

### Integrado con Orchestrator

```python
from hlcs.orchestrator import HLCSOrchestrator
from hlcs.mcp_client import SARAiMCPClient
from hlcs.agi_system import Phi4MiniAGI

# Setup
agi = Phi4MiniAGI(...)
sarai = SARAiMCPClient("http://localhost:3000")

orchestrator = HLCSOrchestrator(
    sarai_client=sarai,
    agi_system=agi,
    enable_agi=True
)

# El orchestrator decide automáticamente:
# - Complejidad < 0.5 → MCP SAUL
# - Complejidad 0.5-0.7 → MCP RAG+LLM
# - Complejidad >= 0.7 → AGI system
# - Keywords de código → AGI system

result = await orchestrator.process("Implementa una API REST")
# → Usa AGI (complexity >= 0.7 + keyword "implementa")
```

---

## 🔧 Troubleshooting

### Error: "llama-cpp-python not installed"

```bash
# CPU only
pip install llama-cpp-python

# Con CUDA
CMAKE_ARGS="-DLLAMA_CUBLAS=on" pip install llama-cpp-python --force-reinstall
```

### Error: "Model file not found"

Verifica que el path en `config/hlcs.yaml` sea correcto:
```bash
ls -lh models/phi4_mini_q4.gguf
```

### Latencia muy alta (>20s)

- Verifica que `n_gpu_layers=-1` esté configurado
- Reduce `n_ctx` a 2048 si tienes poca VRAM
- Usa modelo Q4 en vez de Q8/FP16

### "Out of memory" en GPU

```yaml
agi:
  model:
    n_gpu_layers: 20  # Reducir capas en GPU
    n_ctx: 2048  # Reducir contexto
```

### AGI siempre usa estrategia "simple"

Verifica keywords en `config/hlcs.yaml`:
```yaml
agi:
  complexity:
    keywords:
      - create
      - implement
      # ... agregar más
```

---

## 📊 Monitoreo

### Stats del Sistema

```python
# Obtener estadísticas
stats = agi.get_stats()
print(stats)
# {
#   "total_calls": 150,
#   "simple_calls": 120,
#   "complex_calls": 30,
#   "tool_uses": 45,
#   "errors": 2,
#   "avg_latency_ms": 1234.5,
#   "memory_episodes": 150,
#   ...
# }
```

### Memoria Episódica

```python
# Ver episodios recientes
recent = agi.get_recent_memory(n=10)
for ep in recent:
    print(f"{ep['timestamp']}: {ep['query']}")

# Ver stats de memoria
memory_stats = agi.memory.get_stats()
print(memory_stats)
# {
#   "current_episodes": 150,
#   "max_size": 1000,
#   "usage_percent": 15.0,
#   "saves": 15,
#   "loads": 1
# }
```

### Logs

```bash
# Ver logs en tiempo real
tail -f logs/hlcs.log | grep AGI

# Nivel de debug
export LOG_LEVEL=DEBUG
python -m src.hlcs.rest_gateway.server
```

---

## 🚀 Producción

### Optimizaciones

1. **GPU**: Usar CUDA con `n_gpu_layers=-1`
2. **Modelo**: Q4 para balance velocidad/calidad
3. **Contexto**: 4096 tokens es suficiente
4. **Cache**: Habilitar cache de embeddings

### Escalabilidad

```python
# Múltiples instancias con memoria compartida
agi_1 = Phi4MiniAGI(memory_path="./shared_memory.json")
agi_2 = Phi4MiniAGI(memory_path="./shared_memory.json")

# Ambas instancias comparten memoria
```

### Backup de Memoria

```bash
# Backup automático cada hora
0 * * * * cp data/memory/episodes.json backups/episodes_$(date +\%Y\%m\%d_\%H).json
```

---

## 📖 Referencias

- **Phi-4**: https://huggingface.co/microsoft/phi-4
- **llama.cpp**: https://github.com/ggerganov/llama.cpp
- **ReAct Pattern**: https://arxiv.org/abs/2210.03629
- **RAG**: https://arxiv.org/abs/2005.11401

---

## 🤝 Contribuir

Ver `CONTRIBUTING.md` para guías de contribución.

## 📄 Licencia

Ver `LICENSE` para detalles.
