"""
Tests for REST Gateway API.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch


# Mock dependencies before importing app
@pytest.fixture(autouse=True)
def mock_dependencies():
    """Mock SARAi client and orchestrator."""
    with patch('src.hlcs.rest_gateway.server.SARAiMCPClient') as mock_sarai, \
         patch('src.hlcs.rest_gateway.server.HLCSOrchestrator') as mock_orch:
        
        # Mock SARAi client
        mock_sarai_instance = AsyncMock()
        mock_sarai_instance.ping = AsyncMock(return_value=True)
        mock_sarai.return_value = mock_sarai_instance
        
        # Mock orchestrator
        mock_orch_instance = AsyncMock()
        mock_orch.return_value = mock_orch_instance
        
        yield {
            "sarai": mock_sarai_instance,
            "orchestrator": mock_orch_instance
        }


@pytest.fixture
def client():
    """Create test client."""
    from src.hlcs.rest_gateway.server import app
    return TestClient(app)


def test_root_endpoint(client):
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "HLCS"
    assert "endpoints" in data


def test_health_endpoint(client):
    """Test health check."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["healthy"] is True


def test_status_endpoint(client):
    """Test status endpoint."""
    response = client.get("/api/v1/status")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "version" in data
    assert data["sarai_connected"] is True


def test_capabilities_endpoint(client):
    """Test capabilities endpoint."""
    response = client.get("/api/v1/capabilities")
    assert response.status_code == 200
    data = response.json()
    assert "capabilities" in data
    assert len(data["capabilities"]) > 0


def test_query_endpoint_simple(client, mock_dependencies):
    """Test query endpoint with simple query."""
    # Mock orchestrator response
    mock_dependencies["orchestrator"].process = AsyncMock(return_value={
        "result": "Hola, ¿en qué puedo ayudarte?",
        "quality_score": 0.8,
        "complexity": 0.3,
        "strategy": "simple",
        "modality": "text",
        "iterations": 0,
        "processing_time_ms": 150,
        "metadata": {
            "has_image": False,
            "has_audio": False,
            "research_done": False,
            "vision_done": False,
            "audio_done": False,
            "tool_calls": []
        },
        "errors": [],
        "warnings": []
    })
    
    response = client.post(
        "/api/v1/query",
        json={"query": "hola"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["result"] == "Hola, ¿en qué puedo ayudarte?"
    assert data["strategy"] == "simple"
    assert data["complexity"] < 0.5


def test_query_endpoint_complex(client, mock_dependencies):
    """Test query with complex strategy."""
    mock_dependencies["orchestrator"].process = AsyncMock(return_value={
        "result": "Los agujeros negros son...",
        "quality_score": 0.85,
        "complexity": 0.9,
        "strategy": "complex",
        "modality": "text",
        "iterations": 1,
        "processing_time_ms": 8500,
        "metadata": {
            "has_image": False,
            "has_audio": False,
            "research_done": True,
            "vision_done": False,
            "audio_done": False,
            "tool_calls": [
                {"tool_name": "rag.search", "latency_ms": 5000, "success": True},
                {"tool_name": "llm.chat", "latency_ms": 3000, "success": True}
            ]
        },
        "errors": [],
        "warnings": []
    })
    
    response = client.post(
        "/api/v1/query",
        json={
            "query": "Explica qué son los agujeros negros",
            "options": {"quality_threshold": 0.8}
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["strategy"] == "complex"
    assert data["metadata"]["research_done"] is True
    assert data["iterations"] == 1


def test_query_endpoint_multimodal(client, mock_dependencies):
    """Test multimodal query with image."""
    mock_dependencies["orchestrator"].process = AsyncMock(return_value={
        "result": "En la imagen se ve...",
        "quality_score": 0.82,
        "complexity": 0.7,
        "strategy": "complex",
        "modality": "multimodal",
        "iterations": 0,
        "processing_time_ms": 5200,
        "metadata": {
            "has_image": True,
            "has_audio": False,
            "research_done": False,
            "vision_done": True,
            "audio_done": False,
            "tool_calls": [
                {"tool_name": "vision.analyze", "latency_ms": 2000, "success": True},
                {"tool_name": "llm.chat", "latency_ms": 3000, "success": True}
            ]
        },
        "errors": [],
        "warnings": []
    })
    
    response = client.post(
        "/api/v1/query",
        json={
            "query": "¿Qué hay en esta imagen?",
            "image_url": "https://example.com/image.jpg"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["modality"] == "multimodal"
    assert data["metadata"]["vision_done"] is True


def test_query_endpoint_validation_error(client):
    """Test query validation."""
    # Empty query
    response = client.post(
        "/api/v1/query",
        json={"query": ""}
    )
    assert response.status_code == 422  # Validation error
    
    # Missing query
    response = client.post(
        "/api/v1/query",
        json={}
    )
    assert response.status_code == 422
