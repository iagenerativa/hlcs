"""
Test E2E de integración completa HLCS ↔ SARAi.

Este test valida:
1. Conexión HLCS → SARAi Mock Server
2. Workflows (simple, complex, multimodal)
3. Calidad de respuestas
4. Refinamiento iterativo
5. Manejo de errores
"""

import asyncio
import pytest
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from hlcs.mcp_client import SARAiMCPClient
from hlcs.orchestrator import HLCSOrchestrator


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
async def mock_sarai_url():
    """URL del servidor mock SARAi."""
    return "http://localhost:3100"  # Puerto diferente para evitar conflictos


@pytest.fixture
async def mcp_client(mock_sarai_url):
    """Cliente MCP configurado."""
    async with SARAiMCPClient(base_url=mock_sarai_url, timeout=30.0) as client:
        yield client


@pytest.fixture
async def orchestrator(mcp_client):
    """Orchestrator configurado."""
    return HLCSOrchestrator(
        sarai_client=mcp_client,
        complexity_threshold=0.5,
        quality_threshold=0.7,
        max_iterations=3
    )


# ============================================================================
# Tests de Conectividad
# ============================================================================

@pytest.mark.asyncio
async def test_sarai_connectivity(mcp_client):
    """Test 1: Verificar que HLCS puede conectarse a SARAi."""
    print("\n" + "=" * 60)
    print("TEST 1: Conectividad HLCS ↔ SARAi")
    print("=" * 60)
    
    # Ping al servidor
    is_healthy = await mcp_client.ping()
    
    print(f"✅ SARAi health check: {'OK' if is_healthy else 'FAILED'}")
    assert is_healthy, "SARAi server should be healthy"
    
    # Listar tools disponibles
    tools = await mcp_client.list_tools()
    
    print(f"✅ Tools disponibles: {len(tools)}")
    for tool in tools:
        print(f"   - {tool['name']} ({tool['category']})")
    
    assert len(tools) > 0, "SARAi should expose tools"
    assert any(t["name"] == "saul.respond" for t in tools), "SAUL tool should be available"


@pytest.mark.asyncio
async def test_saul_direct_call(mcp_client):
    """Test 2: Llamada directa a SAUL."""
    print("\n" + "=" * 60)
    print("TEST 2: Llamada Directa SAUL")
    print("=" * 60)
    
    result = await mcp_client.call_tool(
        tool_name="saul.respond",
        parameters={"query": "hola", "context": {}}
    )
    
    print(f"Query: 'hola'")
    print(f"✅ Respuesta: {result.result.get('text')}")
    print(f"✅ Latencia: {result.latency_ms:.0f}ms")
    
    assert result.success, "SAUL call should succeed"
    assert "text" in result.result, "SAUL should return text"
    assert result.latency_ms < 500, f"SAUL should be fast (<500ms), got {result.latency_ms}ms"


@pytest.mark.asyncio
async def test_trm_classification(mcp_client):
    """Test 3: Clasificación TRM de complejidad."""
    print("\n" + "=" * 60)
    print("TEST 3: Clasificación TRM")
    print("=" * 60)
    
    test_cases = [
        ("hola", "simple"),
        ("explica qué es un agujero negro", "complex"),
        ("cómo funciona un motor de combustión", "complex")
    ]
    
    for query, expected_category in test_cases:
        result = await mcp_client.call_tool(
            tool_name="trm.classify",
            parameters={"query": query, "context": {}}
        )
        
        complexity = result.result.get("complexity", 0)
        category = result.result.get("category", "unknown")
        
        print(f"Query: '{query}'")
        print(f"  Complexity: {complexity:.2f}")
        print(f"  Category: {category}")
        print(f"  Expected: {expected_category}")
        print(f"  ✅ Match: {category == expected_category}")
        
        assert result.success, "TRM call should succeed"
        assert category == expected_category, f"Expected {expected_category}, got {category}"


# ============================================================================
# Tests de Workflows
# ============================================================================

@pytest.mark.asyncio
async def test_simple_workflow(orchestrator):
    """Test 4: Workflow simple (low complexity → SAUL)."""
    print("\n" + "=" * 60)
    print("TEST 4: Workflow Simple")
    print("=" * 60)
    
    result = await orchestrator.process(
        query="hola"
    )
    
    print(f"Query: 'hola'")
    print(f"✅ Strategy: {result['strategy']}")
    print(f"✅ Complexity: {result['complexity']:.2f}")
    print(f"✅ Modality: {result['modality']}")
    print(f"✅ Result: {result['result'][:100]}...")
    print(f"✅ Processing time: {result['processing_time_ms']:.0f}ms")
    
    assert result["strategy"] == "simple", "Should use simple workflow"
    assert result["complexity"] < 0.5, "Should be low complexity"
    assert result["modality"] == "text", "Should be text modality"
    assert len(result["result"]) > 0, "Should have result"
    assert result["processing_time_ms"] < 1000, "Should be fast (<1s)"


@pytest.mark.asyncio
async def test_complex_workflow(orchestrator):
    """Test 5: Workflow complejo (high complexity → RAG + synthesis)."""
    print("\n" + "=" * 60)
    print("TEST 5: Workflow Complejo")
    print("=" * 60)
    
    result = await orchestrator.process(
        query="explica qué es un agujero negro con detalle"
    )
    
    print(f"Query: 'explica qué es un agujero negro con detalle'")
    print(f"✅ Strategy: {result['strategy']}")
    print(f"✅ Complexity: {result['complexity']:.2f}")
    print(f"✅ Modality: {result['modality']}")
    print(f"✅ Result: {result['result'][:200]}...")
    print(f"✅ Processing time: {result['processing_time_ms']:.0f}ms")
    
    assert result["strategy"] == "complex", "Should use complex workflow"
    assert result["complexity"] >= 0.5, "Should be high complexity"
    assert "agujero" in result["result"].lower() or "black hole" in result["result"].lower(), "Should mention black holes"


@pytest.mark.asyncio
async def test_multimodal_workflow(orchestrator):
    """Test 6: Workflow multimodal (vision analysis)."""
    print("\n" + "=" * 60)
    print("TEST 6: Workflow Multimodal (Vision)")
    print("=" * 60)
    
    result = await orchestrator.process(
        query="¿qué hay en esta imagen?",
        image_url="https://example.com/cat.jpg"
    )
    
    print(f"Query: '¿qué hay en esta imagen?' + image")
    print(f"✅ Strategy: {result['strategy']}")
    print(f"✅ Modality: {result['modality']}")
    print(f"✅ Result: {result['result'][:200]}...")
    print(f"✅ Processing time: {result['processing_time_ms']:.0f}ms")
    
    # El orchestrator puede usar strategy "complex" pero modality "multimodal"
    assert result["modality"] == "multimodal", "Should detect multimodal input"
    assert len(result["result"]) > 0, "Should have result"


# ============================================================================
# Tests de Refinamiento
# ============================================================================

@pytest.mark.asyncio
async def test_quality_refinement(orchestrator):
    """Test 7: Refinamiento iterativo de calidad."""
    print("\n" + "=" * 60)
    print("TEST 7: Refinamiento de Calidad")
    print("=" * 60)
    
    # Crear orchestrator con threshold alto para forzar refinamiento
    high_quality_orch = HLCSOrchestrator(
        sarai_client=orchestrator.sarai,
        complexity_threshold=0.5,
        quality_threshold=0.9,  # Muy exigente
        max_iterations=3
    )
    
    result = await high_quality_orch.process(
        query="explica los agujeros negros"
    )
    
    print(f"Query: 'explica los agujeros negros'")
    print(f"✅ Quality Score: {result['quality_score']:.2f}")
    print(f"✅ Iterations: {result['iterations']}")
    print(f"✅ Result: {result['result'][:200]}...")
    
    # Note: El mock siempre devuelve quality 0.75, así que no alcanzará 0.9
    # pero debe intentar refinar
    assert result["iterations"] >= 1, "Should attempt refinement"


# ============================================================================
# Tests de Manejo de Errores
# ============================================================================

@pytest.mark.asyncio
async def test_fallback_on_failure(orchestrator):
    """Test 8: Fallback cuando falla un módulo."""
    print("\n" + "=" * 60)
    print("TEST 8: Fallback en Errores")
    print("=" * 60)
    
    # Query normal debería funcionar incluso si algo falla
    result = await orchestrator.process(
        query="test de fallback"
    )
    
    print(f"Query: 'test de fallback'")
    print(f"✅ Strategy: {result['strategy']}")
    print(f"✅ Result: {result['result'][:100]}...")
    
    assert result["strategy"] in ["simple", "complex", "multimodal"], "Should use valid strategy"
    assert len(result["result"]) > 0, "Should have result even on partial failures"


# ============================================================================
# Test Completo E2E
# ============================================================================

@pytest.mark.asyncio
async def test_e2e_complete_interaction(orchestrator):
    """Test 9: Interacción completa E2E simulando usuario."""
    print("\n" + "=" * 60)
    print("TEST 9: Interacción E2E Completa")
    print("=" * 60)
    
    conversation = [
        "hola",
        "explica qué son los agujeros negros",
        "gracias"
    ]
    
    results = []
    
    for i, query in enumerate(conversation, 1):
        print(f"\n--- Turno {i} ---")
        print(f"Usuario: {query}")
        
        result = await orchestrator.process(query=query)
        results.append(result)
        
        print(f"SARAi: {result['result'][:150]}...")
        print(f"  Strategy: {result['strategy']}")
        print(f"  Latency: {result['processing_time_ms']:.0f}ms")
    
    # Verificaciones
    assert len(results) == 3, "Should process all queries"
    assert results[0]["strategy"] == "simple", "First should be simple"
    assert results[1]["strategy"] == "complex", "Second should be complex"
    assert results[2]["strategy"] == "simple", "Third should be simple"
    
    total_time = sum(r["processing_time_ms"] for r in results)
    print(f"\n✅ Conversación completa en {total_time:.0f}ms")


# ============================================================================
# Test de Rendimiento
# ============================================================================

@pytest.mark.asyncio
async def test_performance_benchmarks(orchestrator):
    """Test 10: Benchmarks de rendimiento."""
    print("\n" + "=" * 60)
    print("TEST 10: Benchmarks de Rendimiento")
    print("=" * 60)
    
    test_cases = [
        ("hola", "simple", 500),
        ("explica Python", "complex", 2000),
    ]
    
    results_table = []
    
    for query, expected_strategy, max_latency_ms in test_cases:
        result = await orchestrator.process(query=query)
        
        latency = result["processing_time_ms"]
        within_budget = latency < max_latency_ms
        
        results_table.append({
            "query": query[:30],
            "strategy": result["strategy"],
            "latency_ms": latency,
            "budget_ms": max_latency_ms,
            "ok": "✅" if within_budget else "❌"
        })
    
    print("\nResultados:")
    print(f"{'Query':<32} {'Strategy':<12} {'Latency':<10} {'Budget':<10} {'OK'}")
    print("-" * 80)
    for r in results_table:
        print(f"{r['query']:<32} {r['strategy']:<12} {r['latency_ms']:<10.0f} {r['budget_ms']:<10} {r['ok']}")
    
    # All should be within budget
    assert all(r["ok"] == "✅" for r in results_table), "All queries should meet latency budget"


# ============================================================================
# Main (para ejecutar standalone)
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("HLCS E2E Integration Test Suite")
    print("=" * 80)
    print("\nIMPORTANTE: Asegúrate de que el Mock SARAi Server esté corriendo:")
    print("  python tests/mock_sarai_server.py")
    print("\n" + "=" * 80)
    
    # Run pytest
    pytest.main([__file__, "-v", "-s"])
