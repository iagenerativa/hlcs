"""
Tests for SARAi MCP Client.
"""

import pytest
from src.hlcs.mcp_client import SARAiMCPClient, ToolCallResult


@pytest.fixture
async def client():
    """Create test client."""
    client = SARAiMCPClient(base_url="http://localhost:3000", timeout=5)
    yield client
    await client.close()


def test_tool_endpoint_mapping():
    """Test tool name to endpoint mapping."""
    client = SARAiMCPClient()
    
    assert client._get_endpoint("saul.respond") == "/api/saul/respond"
    assert client._get_endpoint("vision.analyze") == "/api/vision/analyze"
    assert client._get_endpoint("rag.search") == "/api/rag/search"
    assert client._get_endpoint("unknown.tool") == "/api/tools/unknown.tool"


@pytest.mark.asyncio
async def test_call_tool_success(client, httpx_mock):
    """Test successful tool call."""
    httpx_mock.add_response(
        url="http://localhost:3000/api/saul/respond",
        json={"text": "Hola!"},
        status_code=200
    )
    
    result = await client.call_tool("saul.respond", {"query": "hola"})
    
    assert result.success is True
    assert result.result["text"] == "Hola!"
    assert result.latency_ms > 0


@pytest.mark.asyncio
async def test_call_tool_timeout(client, httpx_mock):
    """Test tool call timeout."""
    import httpx
    
    httpx_mock.add_exception(httpx.TimeoutException("Timeout"))
    
    result = await client.call_tool("saul.respond", {"query": "test"})
    
    assert result.success is False
    assert "Timeout" in result.error


@pytest.mark.asyncio
async def test_call_tool_http_error(client, httpx_mock):
    """Test HTTP error handling."""
    httpx_mock.add_response(
        url="http://localhost:3000/api/saul/respond",
        status_code=500,
        text="Internal Server Error"
    )
    
    result = await client.call_tool("saul.respond", {"query": "test"})
    
    assert result.success is False
    assert "500" in result.error


@pytest.mark.asyncio
async def test_ping_success(client, httpx_mock):
    """Test ping successful."""
    httpx_mock.add_response(
        url="http://localhost:3000/health",
        status_code=200
    )
    
    is_healthy = await client.ping()
    assert is_healthy is True


@pytest.mark.asyncio
async def test_ping_failure(client, httpx_mock):
    """Test ping failure."""
    httpx_mock.add_response(
        url="http://localhost:3000/health",
        status_code=503
    )
    
    is_healthy = await client.ping()
    assert is_healthy is False


@pytest.mark.asyncio
async def test_context_manager(httpx_mock):
    """Test async context manager."""
    httpx_mock.add_response(
        url="http://localhost:3000/health",
        status_code=200
    )
    
    async with SARAiMCPClient() as client:
        result = await client.ping()
        assert result is True
    
    # Client should be closed after context
    # (no easy way to assert this without internal inspection)
