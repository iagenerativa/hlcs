#!/usr/bin/env python3
"""
Ejemplo completo de HLCS con AGI System

Demuestra cómo usar el sistema AGI completo con:
- Phi-4-mini local
- RAG para contexto
- Agente con tools
- Memoria episódica

Version: 1.0.0
"""

import asyncio
import logging
import sys
from pathlib import Path

# Agregar src/ al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from hlcs.agi_system import Phi4MiniAGI
from hlcs.orchestrator import HLCSOrchestrator
from hlcs.mcp_client import SARAiMCPClient

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

logger = logging.getLogger(__name__)


async def demo_agi_standalone():
    """Demo 1: Usar AGI system standalone (sin MCP)."""
    logger.info("=" * 60)
    logger.info("DEMO 1: AGI System Standalone")
    logger.info("=" * 60)
    
    # Crear sistema AGI
    agi = Phi4MiniAGI(
        model_path="./models/phi4_mini_q4.gguf",
        rag_docs="./data/codebase.py",
        memory_path="./data/memory/episodes.json"
    )
    
    # Query simple (usa RAG + LLM directo)
    logger.info("\n1. Query SIMPLE:")
    result = await agi.process(
        query="¿Qué es HLCS y cómo funciona?",
        user_id="demo_user",
        session_id="demo_session_1"
    )
    
    print(f"\n📝 Answer:\n{result['answer']}")
    print(f"\n📊 Stats: strategy={result['strategy']}, latency={result['latency_ms']}ms")
    
    # Query complejo (usa agente con tools)
    logger.info("\n2. Query COMPLEX:")
    result = await agi.process(
        query="Create a Python function that fetches data from an API and saves to JSON",
        user_id="demo_user",
        session_id="demo_session_1"
    )
    
    print(f"\n📝 Answer:\n{result['answer']}")
    print(f"\n📊 Stats: strategy={result['strategy']}, latency={result['latency_ms']}ms")
    
    # Ver memoria
    logger.info("\n3. Checking memory:")
    memory = agi.get_recent_memory(n=5)
    print(f"\n💾 Recent memory ({len(memory)} episodes):")
    for ep in memory:
        print(f"  - {ep['timestamp']}: {ep['query'][:60]}...")
    
    # Stats globales
    stats = agi.get_stats()
    print(f"\n📈 AGI Stats:\n{stats}")


async def demo_agi_integrated():
    """Demo 2: AGI integrado en orchestrator (con MCP fallback)."""
    logger.info("\n" + "=" * 60)
    logger.info("DEMO 2: AGI Integrated with Orchestrator")
    logger.info("=" * 60)
    
    # Crear AGI system
    agi = Phi4MiniAGI(
        model_path="./models/phi4_mini_q4.gguf",
        rag_docs="./data/codebase.py",
        memory_path="./data/memory/episodes_integrated.json"
    )
    
    # Crear cliente MCP (asumiendo SARAi corriendo)
    try:
        sarai = SARAiMCPClient("http://localhost:3000")
        await sarai.__aenter__()
        
        if not await sarai.ping():
            logger.warning("SARAi MCP not available, AGI will handle all queries")
    except Exception as e:
        logger.warning(f"Could not connect to SARAi: {e}")
        sarai = None
    
    if not sarai:
        logger.error("Cannot run integrated demo without SARAi MCP server")
        return
    
    # Crear orchestrator con AGI
    orchestrator = HLCSOrchestrator(
        sarai_client=sarai,
        agi_system=agi,
        enable_agi=True,
        complexity_threshold=0.5,
        quality_threshold=0.7
    )
    
    # Test queries
    test_queries = [
        ("¿Hola, cómo estás?", "simple"),  # Uses SAUL via MCP
        ("¿Qué es un agujero negro?", "complex"),  # Uses MCP RAG+LLM
        ("Implement a REST API with authentication", "agi_enhanced"),  # Uses AGI
        ("Create a Python class for data validation", "agi_enhanced"),  # Uses AGI
    ]
    
    for i, (query, expected_strategy) in enumerate(test_queries, 1):
        logger.info(f"\n{i}. Processing: {query}")
        logger.info(f"   Expected strategy: {expected_strategy}")
        
        result = await orchestrator.process(
            query=query,
            user_id="demo_user",
            session_id="demo_session_2"
        )
        
        print(f"\n   ✅ Strategy used: {result['strategy']}")
        print(f"   📝 Result: {result['result'][:200]}...")
        print(f"   ⏱️  Time: {result['processing_time_ms']}ms")
        print(f"   🎯 Quality: {result['quality_score']}")
    
    # Cleanup
    await sarai.close()


async def demo_memory_operations():
    """Demo 3: Operaciones con memoria episódica."""
    logger.info("\n" + "=" * 60)
    logger.info("DEMO 3: Memory Operations")
    logger.info("=" * 60)
    
    from hlcs.memory.episodic_memory import MemoryBuffer
    
    # Crear buffer de memoria
    memory = MemoryBuffer(
        max_size=100,
        persist_path="./data/memory/demo_memory.json",
        auto_save=True
    )
    
    # Agregar episodios
    logger.info("\n1. Adding episodes...")
    for i in range(5):
        memory.add(
            query=f"Test query {i}",
            answer=f"Test answer {i}",
            session_id="demo_session",
            user_id="demo_user",
            metadata={"test": True, "index": i}
        )
    
    print(f"   Added 5 episodes. Total: {len(memory)}")
    
    # Obtener recientes
    logger.info("\n2. Getting recent episodes...")
    recent = memory.get_recent(3)
    for ep in recent:
        print(f"   - {ep.timestamp}: {ep.query}")
    
    # Filtrar por sesión
    logger.info("\n3. Filter by session...")
    by_session = memory.get_by_session("demo_session")
    print(f"   Found {len(by_session)} episodes in session")
    
    # Guardar explícitamente
    logger.info("\n4. Saving to disk...")
    success = memory.save()
    print(f"   Save {'successful' if success else 'failed'}")
    
    # Stats
    stats = memory.get_stats()
    print(f"\n📊 Memory Stats:\n{stats}")


async def main():
    """Ejecutar demos."""
    print("\n" + "=" * 60)
    print("HLCS AGI System - Complete Demo")
    print("=" * 60)
    
    try:
        # Demo 1: AGI standalone
        await demo_agi_standalone()
        
        # Demo 2: AGI integrado (requiere SARAi)
        # await demo_agi_integrated()  # Comentado por defecto
        
        # Demo 3: Operaciones de memoria
        await demo_memory_operations()
        
        print("\n✅ All demos completed successfully!")
        
    except KeyboardInterrupt:
        logger.info("\n⚠️  Demo interrupted by user")
    except Exception as e:
        logger.error(f"\n❌ Demo failed: {e}", exc_info=True)
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
