"""
Tests for HLCS Orchestrator.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from hlcs.orchestrator import HLCSOrchestrator, HLCSState
from hlcs.mcp_client import SARAiMCPClient, ToolCallResult


@pytest.fixture
def mock_sarai_client():
    """Mock SARAi MCP Client."""
    client = AsyncMock(spec=SARAiMCPClient)
    return client


@pytest.fixture
def orchestrator(mock_sarai_client):
    """Create orchestrator with mocked client."""
    return HLCSOrchestrator(
        sarai_client=mock_sarai_client,
        complexity_threshold=0.5,
        quality_threshold=0.7,
        max_iterations=3
    )


@pytest.mark.asyncio
async def test_simple_workflow(orchestrator, mock_sarai_client):
    """Test simple workflow (low complexity)."""
    # Mock TRM classifier → low complexity
    mock_sarai_client.call_tool.side_effect = [
        # TRM classify
        ToolCallResult(
            success=True,
            result={"complexity": 0.3},
            latency_ms=50
        ),
        # SAUL respond
        ToolCallResult(
            success=True,
            result={"text": "Hola, ¿en qué puedo ayudarte?"},
            latency_ms=150
        )
    ]
    
    result = await orchestrator.process("hola")
    
    assert result["result"] == "Hola, ¿en qué puedo ayudarte?"
    assert result["strategy"] == "simple"
    assert result["complexity"] < 0.5
    assert mock_sarai_client.call_tool.call_count == 2


@pytest.mark.asyncio
async def test_complex_workflow(orchestrator, mock_sarai_client):
    """Test complex workflow (high complexity)."""
    # Mock: TRM → RAG → LLM synthesis
    mock_sarai_client.call_tool.side_effect = [
        # TRM classify
        ToolCallResult(
            success=True,
            result={"complexity": 0.8},
            latency_ms=50
        ),
        # RAG search
        ToolCallResult(
            success=True,
            result={"results": [{"text": "Información sobre agujeros negros..."}]},
            latency_ms=5000
        ),
        # LLM synthesis
        ToolCallResult(
            success=True,
            result={"text": "Los agujeros negros son regiones del espacio..."},
            latency_ms=3000
        )
    ]
    
    result = await orchestrator.process("Explica qué son los agujeros negros")
    
    assert result["strategy"] == "complex"
    assert result["complexity"] > 0.5
    assert "agujeros negros" in result["result"].lower()
    assert mock_sarai_client.call_tool.call_count == 3


@pytest.mark.asyncio
async def test_multimodal_workflow(orchestrator, mock_sarai_client):
    """Test multimodal workflow (with image)."""
    # Mock: TRM → Vision → LLM synthesis
    mock_sarai_client.call_tool.side_effect = [
        # TRM classify
        ToolCallResult(
            success=True,
            result={"complexity": 0.6},
            latency_ms=50
        ),
        # Vision analyze
        ToolCallResult(
            success=True,
            result={"description": "Una imagen de un gato naranja"},
            latency_ms=2000
        ),
        # LLM synthesis
        ToolCallResult(
            success=True,
            result={"text": "En la imagen se ve un gato naranja..."},
            latency_ms=3000
        )
    ]
    
    result = await orchestrator.process(
        query="¿Qué hay en esta imagen?",
        image_url="https://example.com/cat.jpg"
    )
    
    assert result["modality"] == "multimodal"
    assert result["metadata"]["vision_done"] is True
    assert "gato" in result["result"].lower()


@pytest.mark.asyncio
async def test_fallback_on_error(orchestrator, mock_sarai_client):
    """Test fallback when tools fail."""
    # Mock: TRM fails → defaults to simple
    mock_sarai_client.call_tool.side_effect = [
        # TRM classify fails
        ToolCallResult(
            success=False,
            result={},
            error="TRM service unavailable",
            latency_ms=100
        ),
        # SAUL respond (fallback)
        ToolCallResult(
            success=True,
            result={"text": "Respuesta de emergencia"},
            latency_ms=150
        )
    ]
    
    result = await orchestrator.process("test query")
    
    assert result["strategy"] == "simple"
    assert len(result["warnings"]) > 0
    assert "Respuesta" in result["result"]


@pytest.mark.asyncio
async def test_quality_refinement_loop(orchestrator, mock_sarai_client):
    """Test refinement loop improves quality."""
    # Mock: Low quality → refine → better quality
    mock_sarai_client.call_tool.side_effect = [
        # TRM classify
        ToolCallResult(success=True, result={"complexity": 0.3}, latency_ms=50),
        # SAUL respond (low quality)
        ToolCallResult(success=True, result={"text": "Respuesta breve"}, latency_ms=150),
        # Quality eval (low)
        ToolCallResult(
            success=True,
            result={"text": '{"score": 0.5, "issues": ["muy breve"]}'},
            latency_ms=1000
        ),
        # Refinement
        ToolCallResult(
            success=True,
            result={"text": "Respuesta mejorada y más completa"},
            latency_ms=2000
        ),
        # Quality eval (better)
        ToolCallResult(
            success=True,
            result={"text": '{"score": 0.8, "issues": []}'},
            latency_ms=1000
        )
    ]
    
    # Lower quality threshold to trigger refinement
    orchestrator.quality_threshold = 0.6
    
    result = await orchestrator.process("test")
    
    assert result["iterations"] > 0
    assert "mejorada" in result["result"].lower()


def test_state_processing_time():
    """Test HLCSState processing time calculation."""
    import time
    from datetime import datetime
    
    state = HLCSState(query="test")
    state.start_time = datetime.now()
    time.sleep(0.1)  # 100ms
    state.end_time = datetime.now()
    
    assert state.processing_time_ms >= 100
    assert state.processing_time_ms < 200  # Should be ~100ms


def test_modality_detection():
    """Test modality detection logic."""
    # Text only
    state = HLCSState(query="test", has_image=False, has_audio=False)
    assert state.modality == "text"
    
    # With image
    state = HLCSState(query="test", has_image=True, has_audio=False)
    orchestrator = HLCSOrchestrator(sarai_client=AsyncMock())
    state = orchestrator._detect_modality(state)
    assert state.modality == "multimodal"
    
    # With audio
    state = HLCSState(query="test", has_image=False, has_audio=True)
    state = orchestrator._detect_modality(state)
    assert state.modality == "multimodal"
