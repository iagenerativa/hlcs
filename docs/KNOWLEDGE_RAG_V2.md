# Knowledge RAG v2.0 - Memoria Externa para HLCS AGI

## 🧠 Resumen Ejecutivo

El sistema KnowledgeRAG v2.0 implementa **memoria externa persistente** para HLCS AGI, actuando como "cerebro externo" que almacena, recupera y consolida conocimiento de forma inteligente. Usa ChromaDB como backend de vectores, all-MiniLM-L6-v2 para embeddings rápidos (~50MB), y LangChain para orquestación ligera.

**Características clave**:
- ✅ **Persistencia en disco** (ChromaDB) - No pierde memoria al reiniciar
- ✅ **Memoria jerárquica** (corto/largo plazo) - Simula memoria humana
- ✅ **Auto-consolidación** - STM → LTM basado en acceso/relevancia
- ✅ **Metadatos ricos** - Filtros semánticos por tipo, fuente, confianza
- ✅ **Kubernetes-ready** - Pods minimalistas con persistent volumes
- ✅ **Sin dependencias cloud** - 100% local y escalable

---

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                    Query/Store Request                      │
└──────────────────┬──────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────────┐
│           KnowledgeRAG (Orchestrator)                       │
│  • Query routing                                            │
│  • Metadata filtering                                       │
│  • Reranking (score × confidence × recency)                 │
└──────────────┬────────────────────────┬─────────────────────┘
               │                        │
      ┌────────▼────────┐      ┌───────▼────────┐
      │  Embedding Layer│      │ ChromaDB Client│
      │  (MiniLM-L6-v2) │      │  (Persistent)  │
      │  ~50MB, fast    │      │  Vector Store  │
      └────────┬────────┘      └───────┬────────┘
               │                        │
               └────────────┬───────────┘
                            │
              ┌─────────────▼────────────────┐
              │   ChromaDB Backend           │
              │   (Disk-based Storage)       │
              │   /data/chroma_db/           │
              │                              │
              │   Collections:               │
              │   • hlcs_knowledge           │
              │     - Vectors (384-dim)      │
              │     - Documents (text)       │
              │     - Metadata (rich)        │
              └──────────────────────────────┘
```

### Flujo de Datos

**Almacenamiento (Add Memory)**:
```
Text Input → Embedding (MiniLM) → [Vector, Text, Metadata] → ChromaDB → Disk
```

**Recuperación (Retrieve)**:
```
Query → Embedding → ChromaDB Search (cosine) → Metadata Filters → 
Reranking → Update Access Counts → Results
```

**Consolidación (Background)**:
```
[Every Hour] → Check STM access counts → Promote to LTM (>= threshold) →
Delete expired STM (> TTL) → Stats
```

---

## 📊 Memoria Jerárquica

Inspirada en memoria humana, el sistema implementa dos niveles:

### Short-Term Memory (STM)
- **Duración**: TTL configurable (default 24 horas)
- **Uso**: Interacciones recientes, preferencias temporales
- **Promoción**: Auto-promoción a LTM basada en:
  - Access count >= threshold (default 3)
  - Confidence score >= 0.9
- **Expiración**: Auto-eliminación después de TTL sin acceso
- **Ejemplo**: "Usuario prefiere modo oscuro" (conversación actual)

### Long-Term Memory (LTM)
- **Duración**: Permanente (hasta eliminación manual)
- **Uso**: Conocimiento consolidado, hechos establecidos
- **Fuentes**: Documentación, código, conocimiento verificado
- **Ejemplo**: "Python 3.11+ usa sintaxis moderna de tipos"

### Flujo de Consolidación

```python
# Automático cada hora (configurable)
stats = rag.consolidate_memories()
# {'promoted': 5, 'expired': 12}

# STM → LTM cuando:
# 1. access_count >= ltm_promotion_threshold (default 3)
# 2. confidence_score >= 0.9 (alta confianza)
# 3. Manual via update_metadata()

# STM → [Deleted] cuando:
# 1. timestamp > stm_ttl_hours Y access_count < threshold
```

---

## 🏷️ Sistema de Metadatos

Cada vector incluye metadatos enriquecidos para filtrado semántico:

```python
@dataclass
class MemoryMetadata:
    # Tipo de conocimiento
    knowledge_type: "episodic" | "semantic" | "procedural"
    
    # Nivel de memoria
    memory_tier: "short_term" | "long_term"
    
    # Timestamp ISO (para recency)
    timestamp: str
    
    # Origen del conocimiento
    source: str  # e.g., "user_conversation", "documentation", "code"
    
    # Confianza (0-1)
    confidence_score: float
    
    # Contador de accesos (para consolidación)
    access_count: int
    
    # Etiquetas para filtrado
    tags: List[str]
```

### Tipos de Conocimiento

**Episodic (Episódico)**: Eventos específicos, interacciones
- "Usuario solicitó API REST el 2025-11-07"
- "Conversación sobre arquitectura Kubernetes"

**Semantic (Semántico)**: Hechos generales, conceptos
- "FastAPI usa decoradores para routing"
- "ChromaDB es una base de datos vectorial"

**Procedural (Procedimental)**: Cómo hacer cosas, código
- Fragmentos de funciones/clases
- Algoritmos y patrones

---

## 🚀 Uso Básico

### Inicialización

```python
from hlcs.memory.rag import KnowledgeRAG, MemoryMetadata

# Inicializar con persistencia local
rag = KnowledgeRAG(
    persist_dir="./data/chroma_db",
    collection_name="hlcs_knowledge",
    embedding_model="all-MiniLM-L6-v2",
    stm_ttl_hours=24,
    ltm_promotion_threshold=3
)

print(f"RAG initialized: {rag}")
# KnowledgeRAG(memories=0, backend=chromadb, embedding=all-MiniLM-L6-v2)
```

### Agregar Memorias

```python
# Memoria simple (auto-genera metadatos)
mem_id = rag.add_memory("Python 3.11+ requerido para sintaxis moderna")

# Memoria con metadatos completos
rag.add_memory(
    "Usuario prefiere async/await sobre threads",
    metadata=MemoryMetadata(
        knowledge_type="episodic",
        memory_tier="short_term",
        source="user_conversation",
        confidence_score=0.95,
        tags=["preferences", "async", "concurrency"]
    )
)

# Bulk load (eficiente para muchas memorias)
contents = [
    "FastAPI usa Pydantic para validación",
    "Uvicorn es ASGI server para FastAPI",
    "Starlette es el framework base de FastAPI"
]
metadatas = [
    MemoryMetadata(
        knowledge_type="semantic",
        memory_tier="long_term",
        source="documentation",
        confidence_score=0.9,
        tags=["fastapi", "web"]
    )
    for _ in contents
]
ids = rag.add_memories_bulk(contents, metadatas)
print(f"Added {len(ids)} memories")
```

### Recuperar Memorias

```python
# Búsqueda semántica básica
results = rag.retrieve("¿Qué framework web usar para Python?", top_k=3)

for res in results:
    print(f"Score: {res.score:.3f}")
    print(f"Content: {res.content[:100]}...")
    print(f"Tier: {res.metadata.memory_tier}")
    print(f"Type: {res.metadata.knowledge_type}")
    print()

# Con filtros de metadata
results = rag.retrieve(
    query="preferencias del usuario",
    top_k=5,
    knowledge_type="episodic",  # Solo episódicas
    memory_tier="short_term",   # Solo STM
    min_confidence=0.8,         # Alta confianza
    tags=["preferences"]        # Con tag "preferences"
)

# Búsqueda solo por metadata (sin semántica)
episodic_memories = rag.search_by_metadata(
    knowledge_type="episodic",
    source="user_conversation",
    limit=10
)
```

### Cargar Documentos

```python
from hlcs.memory.rag import load_documents_from_file

# Cargar código fuente (chunking inteligente por función)
doc_memories = load_documents_from_file(
    "./src/hlcs/orchestrator.py",
    chunk_by="function",  # o "paragraph", "fixed"
    knowledge_type="procedural"
)

# Agregar a RAG
contents = [m[0] for m in doc_memories]
metadatas = [m[1] for m in doc_memories]
ids = rag.add_memories_bulk(contents, metadatas)
print(f"Loaded {len(ids)} code chunks")
```

### Consolidación y Estadísticas

```python
# Estadísticas actuales
stats = rag.get_stats()
print(stats)
# {
#   'total_memories': 156,
#   'short_term': 23,
#   'long_term': 133,
#   'episodic': 45,
#   'semantic': 89,
#   'procedural': 22,
#   'backend': 'chromadb',
#   'persist_dir': './data/chroma_db',
#   'embedding_model': 'all-MiniLM-L6-v2'
# }

# Consolidación manual (normalmente automática)
consolidation = rag.consolidate_memories()
print(consolidation)
# {'promoted': 5, 'expired': 12}

# Limpiar todo (¡CUIDADO!)
# rag.clear_all()
```

---

## 🐍 Integración con LangChain

El sistema incluye wrapper minimalista para LangChain:

```python
from langchain.chains import RetrievalQA
from langchain_community.llms import LlamaCpp

# KnowledgeRAG incluye langchain_vectorstore
if rag.langchain_vectorstore:
    # Usar como retriever en chains
    retriever = rag.langchain_vectorstore.as_retriever(
        search_kwargs={"k": 3}
    )
    
    # Crear QA chain
    llm = LlamaCpp(model_path="./models/phi4_mini_q4.gguf")
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        return_source_documents=True
    )
    
    # Query
    result = qa_chain({"query": "¿Cómo funciona el orchestrator?"})
    print(result["result"])
```

---

## ☸️ Deployment en Kubernetes

### Requisitos
- Persistent Volume (10Gi recomendado)
- 256Mi-512Mi RAM (ChromaDB + embeddings)
- 100m-500m CPU

### Deployment

```bash
# Aplicar deployment
kubectl apply -f k8s/rag-deployment.yaml

# Verificar pod
kubectl get pods -n hlcs -l component=rag

# Logs
kubectl logs -n hlcs -l component=rag -f

# Port-forward para testing
kubectl port-forward -n hlcs svc/hlcs-rag-service 4001:4001
```

### Configuración

Ver `k8s/rag-deployment.yaml` para:
- PersistentVolumeClaim (10Gi)
- ConfigMap (configuración RAG)
- Deployment (single replica, read-write)
- Service (ClusterIP)
- Health checks (liveness, readiness, startup)

**IMPORTANTE**: ChromaDB no soporta multi-writer. Mantener `replicas: 1` o usar arquitectura read-replica.

### Persistent Volume

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: hlcs-chroma-pv
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
```

### Resource Limits

```yaml
resources:
  limits:
    memory: "512Mi"  # ChromaDB + embeddings + overhead
    cpu: "500m"
  requests:
    memory: "256Mi"
    cpu: "100m"
```

---

## 🧪 Testing

### Ejecutar Tests

```bash
# Tests completos
pytest tests/test_knowledge_rag.py -v

# Solo tests básicos (sin ChromaDB)
pytest tests/test_knowledge_rag.py::TestMemoryMetadata -v

# Tests de integración (requiere ChromaDB + sentence-transformers)
pytest tests/test_knowledge_rag.py::TestIntegrationWithDependencies -v

# Con coverage
pytest tests/test_knowledge_rag.py --cov=src/hlcs/memory/rag --cov-report=html
```

### Instalar Dependencias de Testing

```bash
# Instalar ChromaDB + embeddings
pip install chromadb sentence-transformers langchain langchain-community

# O desde requirements.txt (ya actualizado)
pip install -r requirements.txt
```

---

## 📈 Performance

### Benchmarks (MacBook M1 Pro)

| Operation | Latency | Notes |
|-----------|---------|-------|
| Embedding (single) | ~5ms | all-MiniLM-L6-v2 |
| Embedding (batch 100) | ~200ms | Amortized 2ms/doc |
| ChromaDB insert | ~10ms | Single document |
| ChromaDB bulk insert (100) | ~500ms | Amortized 5ms/doc |
| Semantic search (top-3) | ~15ms | Cosine similarity |
| Search + reranking | ~20ms | With confidence boost |

### Escalabilidad

- **Vectores**: 1M+ vectores en ~2GB disk
- **Queries**: ~1000 QPS single pod (I/O bound)
- **Horizontal scaling**: Read replicas (no multi-writer)

### Optimizaciones

1. **Precomputar embeddings** al startup para docs estáticos
2. **Batch inserts** para carga inicial (100-1000 docs/batch)
3. **LRU cache** para queries frecuentes (futuro)
4. **Quantization** de embeddings para reducir tamaño (futuro)

---

## 🔧 Configuración Avanzada

### config/hlcs.yaml

```yaml
agi:
  rag:
    enabled: true
    
    chromadb:
      persist_dir: "./data/chroma_db"
      collection_name: "hlcs_knowledge"
    
    embedding_model: "all-MiniLM-L6-v2"
    
    memory:
      stm_ttl_hours: 24
      ltm_promotion_threshold: 3
      consolidation_interval: 3600  # 1 hora
    
    retrieval:
      top_k: 3
      min_confidence: 0.0
      enable_reranking: true
    
    docs:
      codebase_path: "./data/codebase.py"
      chunk_strategy: "function"
      chunk_size: 500
      auto_load: false
    
    kubernetes:
      persistent_volume: true
      pv_claim: "hlcs-chroma-pv"
      precompute_embeddings: true
      health_check_interval: 30
```

### Variables de Entorno

```bash
# Override persist dir
export CHROMADB_PERSIST_DIR="/mnt/chroma_db"

# Override embedding model
export RAG_EMBEDDING_MODEL="all-mpnet-base-v2"  # Más preciso, más lento

# Enable debug logging
export LOG_LEVEL="DEBUG"
```

---

## 🚨 Troubleshooting

### ChromaDB no se conecta

```python
# Check if ChromaDB is available
from hlcs.memory.rag import CHROMADB_AVAILABLE
print(f"ChromaDB available: {CHROMADB_AVAILABLE}")

# Install if missing
# pip install chromadb
```

### Embeddings lentos

```python
# Check embedding model
print(f"Embedding model: {rag.embedding_model}")

# Consider faster model (trade-off: menor precisión)
rag = KnowledgeRAG(embedding_model="all-MiniLM-L6-v2")  # 384-dim, fast
# vs
# rag = KnowledgeRAG(embedding_model="all-mpnet-base-v2")  # 768-dim, better
```

### Disk space issues

```bash
# Check ChromaDB size
du -sh ./data/chroma_db/

# Clear old memories
python -c "from hlcs.memory.rag import KnowledgeRAG; rag = KnowledgeRAG(); rag.clear_all()"

# Or consolidate more aggressively
# Set stm_ttl_hours=1 en config
```

### Memory leak en Kubernetes

```yaml
# Add resource limits
resources:
  limits:
    memory: "512Mi"
  requests:
    memory: "256Mi"

# Enable OOMKilled restart
restartPolicy: Always
```

---

## 🔮 Roadmap

### v2.1 (Q1 2026)
- [ ] LRU cache para queries frecuentes
- [ ] Reranking con cross-encoder (mejor precisión)
- [ ] Async operations (no-blocking)

### v2.2 (Q2 2026)
- [ ] Multi-collection support (namespaces)
- [ ] Vector quantization (reducir tamaño 4x)
- [ ] Incremental updates (sin re-embedding)

### v3.0 (Q3 2026)
- [ ] Distributed ChromaDB (multi-node)
- [ ] Graph-augmented retrieval (knowledge graph)
- [ ] Automatic chunking optimization (ML-based)

---

## 📚 Referencias

- **ChromaDB**: https://docs.trychroma.com/
- **Sentence Transformers**: https://www.sbert.net/
- **LangChain**: https://python.langchain.com/docs/integrations/vectorstores/chroma
- **all-MiniLM-L6-v2**: https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2
- **HLCS AGI**: `docs/AUTONOMOUS_HLCS.md`

---

## 💬 Support

Para issues, preguntas o contribuciones:
- **GitHub Issues**: https://github.com/iagenerativa/hlcs/issues
- **Docs**: `docs/INTEGRACION_SARAI_MCP.md`
- **Tests**: `tests/test_knowledge_rag.py`
