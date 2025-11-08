#!/usr/bin/env python3
"""
Demo del sistema KnowledgeRAG v2.0

Muestra características principales:
- Persistencia con ChromaDB
- Memoria jerárquica (STM/LTM)
- Metadatos ricos y filtros semánticos
- Consolidación automática
- Carga de documentos

Run:
    python examples/rag_demo.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from hlcs.memory.rag import (
    KnowledgeRAG,
    MemoryMetadata,
    load_documents_from_file,
    CHROMADB_AVAILABLE,
    EMBEDDINGS_AVAILABLE
)

print("=" * 60)
print("KnowledgeRAG v2.0 Demo")
print("=" * 60)

# Check dependencies
print(f"\nDependencies:")
print(f"  ChromaDB: {'✅' if CHROMADB_AVAILABLE else '❌ (pip install chromadb)'}")
print(f"  Embeddings: {'✅' if EMBEDDINGS_AVAILABLE else '❌ (pip install sentence-transformers)'}")

if not (CHROMADB_AVAILABLE and EMBEDDINGS_AVAILABLE):
    print("\n⚠️  Running in MOCK mode. Install dependencies for full functionality:")
    print("    pip install chromadb sentence-transformers langchain langchain-community")
    print()

# Initialize RAG
print("\n" + "=" * 60)
print("1. Inicialización")
print("=" * 60)

rag = KnowledgeRAG(
    persist_dir="./data/chroma_db_demo",
    collection_name="demo_collection",
    stm_ttl_hours=24,
    ltm_promotion_threshold=3
)

print(f"✅ RAG initialized: {rag}")
print(f"   Current memories: {len(rag)}")

# Add memories with different types
print("\n" + "=" * 60)
print("2. Agregar memorias con metadatos")
print("=" * 60)

# Short-term episodic (user interaction)
rag.add_memory(
    "Usuario prefiere Python sobre JavaScript para backend",
    metadata=MemoryMetadata(
        knowledge_type="episodic",
        memory_tier="short_term",
        source="user_conversation",
        confidence_score=0.95,
        tags=["preferences", "languages", "python"]
    )
)
print("✅ Added STM episodic memory (user preference)")

# Long-term semantic (documentation)
rag.add_memory(
    "FastAPI es un framework web moderno de Python con soporte async y documentación OpenAPI automática",
    metadata=MemoryMetadata(
        knowledge_type="semantic",
        memory_tier="long_term",
        source="documentation",
        confidence_score=0.98,
        tags=["fastapi", "python", "web", "framework"]
    )
)
print("✅ Added LTM semantic memory (documentation)")

# Procedural (code knowledge)
rag.add_memory(
    """def create_fastapi_endpoint(path: str):
    @app.get(path)
    async def endpoint():
        return {'message': 'Hello'}
""",
    metadata=MemoryMetadata(
        knowledge_type="procedural",
        memory_tier="long_term",
        source="code_example",
        confidence_score=0.90,
        tags=["fastapi", "code", "example"]
    )
)
print("✅ Added LTM procedural memory (code example)")

# Bulk add
contents = [
    "ChromaDB es una base de datos vectorial para embeddings",
    "all-MiniLM-L6-v2 es un modelo de embeddings ligero y rápido",
    "LangChain facilita la orquestación de LLMs y herramientas"
]
metadatas = [
    MemoryMetadata(
        knowledge_type="semantic",
        memory_tier="long_term",
        source="technical_docs",
        confidence_score=0.95,
        tags=["technical", "tools"]
    )
    for _ in contents
]
ids = rag.add_memories_bulk(contents, metadatas)
print(f"✅ Added {len(ids)} bulk memories")

# Retrieve with semantic search
print("\n" + "=" * 60)
print("3. Búsqueda semántica")
print("=" * 60)

query = "¿Qué framework web debería usar para Python?"
print(f"Query: {query}\n")

results = rag.retrieve(query, top_k=3)
print(f"Found {len(results)} results:\n")

for i, res in enumerate(results, 1):
    print(f"{i}. Score: {res.score:.3f} | Tier: {res.metadata.memory_tier} | Type: {res.metadata.knowledge_type}")
    print(f"   Content: {res.content[:80]}...")
    print(f"   Source: {res.metadata.source}")
    print(f"   Tags: {res.metadata.tags[:3]}")
    print()

# Retrieve with filters
print("\n" + "=" * 60)
print("4. Búsqueda con filtros de metadata")
print("=" * 60)

filtered_query = "preferencias del usuario"
print(f"Query: {filtered_query}")
print(f"Filters: knowledge_type=episodic, memory_tier=short_term\n")

filtered_results = rag.retrieve(
    filtered_query,
    top_k=5,
    knowledge_type="episodic",
    memory_tier="short_term"
)

print(f"Found {len(filtered_results)} filtered results:\n")
for i, res in enumerate(filtered_results, 1):
    print(f"{i}. {res.content}")
    print(f"   Confidence: {res.metadata.confidence_score}")
    print()

# Search by metadata only
print("\n" + "=" * 60)
print("5. Búsqueda solo por metadata (no semántica)")
print("=" * 60)

metadata_only = rag.search_by_metadata(
    knowledge_type="procedural",
    limit=10
)

print(f"Found {len(metadata_only)} procedural memories:\n")
for i, res in enumerate(metadata_only, 1):
    print(f"{i}. {res.content[:60]}...")
    print()

# Statistics
print("\n" + "=" * 60)
print("6. Estadísticas del sistema")
print("=" * 60)

stats = rag.get_stats()
print(f"\nRAG Statistics:")
print(f"  Total memories: {stats.get('total_memories', 0)}")
print(f"  Short-term: {stats.get('short_term', 0)}")
print(f"  Long-term: {stats.get('long_term', 0)}")
print(f"  Episodic: {stats.get('episodic', 0)}")
print(f"  Semantic: {stats.get('semantic', 0)}")
print(f"  Procedural: {stats.get('procedural', 0)}")
print(f"  Backend: {stats.get('backend', 'unknown')}")
print(f"  Embedding model: {stats.get('embedding_model', 'N/A')}")

# Consolidation
print("\n" + "=" * 60)
print("7. Consolidación de memoria")
print("=" * 60)

consolidation = rag.consolidate_memories()
print(f"\nConsolidation results:")
print(f"  Promoted to LTM: {consolidation['promoted']}")
print(f"  Expired from STM: {consolidation['expired']}")

# Load documents (if available)
print("\n" + "=" * 60)
print("8. Carga de documentos (opcional)")
print("=" * 60)

codebase_path = "./src/hlcs/orchestrator.py"
if Path(codebase_path).exists():
    print(f"Loading code from {codebase_path}...")
    
    doc_memories = load_documents_from_file(
        codebase_path,
        chunk_by="function",
        knowledge_type="procedural"
    )
    
    if doc_memories:
        # Take first 5 chunks as example
        sample_contents = [m[0] for m in doc_memories[:5]]
        sample_metadatas = [m[1] for m in doc_memories[:5]]
        
        sample_ids = rag.add_memories_bulk(sample_contents, sample_metadatas)
        print(f"✅ Loaded {len(sample_ids)} code chunks (sample)")
        
        # Query against code
        code_query = "How does the orchestrator work?"
        code_results = rag.retrieve(code_query, knowledge_type="procedural", top_k=2)
        
        print(f"\nQuery: {code_query}")
        print(f"Found {len(code_results)} code chunks:\n")
        
        for i, res in enumerate(code_results, 1):
            print(f"{i}. {res.content[:100]}...")
            print()
else:
    print(f"⚠️  Codebase not found at {codebase_path}")

# Final stats
print("\n" + "=" * 60)
print("9. Estadísticas finales")
print("=" * 60)

final_stats = rag.get_stats()
print(f"\nFinal memory count: {final_stats.get('total_memories', 0)}")
print(f"Final representation: {rag}")

# Cleanup option
print("\n" + "=" * 60)
print("Demo completado!")
print("=" * 60)
print("\nPara limpiar datos de prueba:")
print("  rm -rf ./data/chroma_db_demo/")
print("\nPara ver documentación completa:")
print("  docs/KNOWLEDGE_RAG_V2.md")
print("\nPara ejecutar tests:")
print("  pytest tests/test_knowledge_rag.py -v")
print()
