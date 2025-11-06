#!/usr/bin/env python3
"""
Test de Integración HLCS MCP Client con SARAi MCP Server

Usa pytest con fixtures para simular el servidor MCP y validar
que el cliente HLCS funciona correctamente con el protocolo MCP.

Este test NO requiere servidores corriendo - usa mocking.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import sys
from pathlib import Path

# Agregar src/ al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from hlcs.mcp_client import SARAiMCPClient, ToolCallResult, ToolDefinition


class TestMCPClientIntegration:
    """Tests de integración del cliente MCP de HLCS."""
    
    @pytest.mark.asyncio
    async def test_client_can_ping_server(self):
        """Verifica que el cliente puede hacer ping al servidor MCP."""
        
        # Mock de httpx.AsyncClient
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "healthy", "uptime": 123.45}
        
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            
            async with SARAiMCPClient("http://localhost:3000") as client:
                is_healthy = await client.ping()
                
                assert is_healthy is True
                mock_get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_client_can_list_tools(self):
        """Verifica que el cliente puede listar tools del servidor MCP."""
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "tools": [
                {
                    "name": "saul.respond",
                    "description": "Respuesta rápida con SAUL",
                    "parameters": {
                        "query": {"type": "string", "required": True},
                        "include_audio": {"type": "boolean", "required": False}
                    }
                },
                {
                    "name": "saul.synthesize",
                    "description": "Síntesis de voz con Piper TTS",
                    "parameters": {
                        "text": {"type": "string", "required": True}
                    }
                }
            ]
        }
        
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            
            async with SARAiMCPClient("http://localhost:3000") as client:
                tools = await client.list_tools()
                
                assert len(tools) == 2
                assert tools[0].name == "saul.respond"
                assert tools[1].name == "saul.synthesize"
                mock_post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_client_can_call_saul_respond(self):
        """Verifica que el cliente puede llamar a saul.respond correctamente."""
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "result": {
                "response": "¡Hola! ¿En qué puedo ayudarte?",
                "template_id": "greeting",
                "confidence": 0.95,
                "latency_ms": 54.2
            },
            "latency_ms": 56.8
        }
        
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            
            async with SARAiMCPClient("http://localhost:3000") as client:
                result = await client.call_tool("saul.respond", {
                    "query": "hola",
                    "include_audio": False
                })
                
                assert result.success is True
                assert result.result["response"] == "¡Hola! ¿En qué puedo ayudarte?"
                assert result.result["template_id"] == "greeting"
                assert result.result["confidence"] == 0.95
                assert result.latency_ms == 56.8
                
                # Verificar que se llamó con el payload correcto
                call_args = mock_post.call_args
                assert call_args[0][0] == "http://localhost:3000/tools/call"
                assert call_args[1]["json"]["name"] == "saul.respond"
                assert call_args[1]["json"]["parameters"]["query"] == "hola"
    
    @pytest.mark.asyncio
    async def test_client_can_call_saul_synthesize(self):
        """Verifica que el cliente puede llamar a saul.synthesize correctamente."""
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "result": {
                "audio": "base64encodedaudiodata==",
                "duration": 2.5,
                "sample_rate": 22050
            },
            "latency_ms": 185.3
        }
        
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            
            async with SARAiMCPClient("http://localhost:3000") as client:
                result = await client.call_tool("saul.synthesize", {
                    "text": "Hola mundo",
                    "voice_model": "es_ES-sharvard-medium",
                    "speed": 1.0
                })
                
                assert result.success is True
                assert "audio" in result.result
                assert result.result["duration"] == 2.5
                assert result.latency_ms == 185.3
    
    @pytest.mark.asyncio
    async def test_client_handles_tool_errors(self):
        """Verifica que el cliente maneja errores de tools correctamente."""
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": False,
            "error": "Tool 'invalid.tool' not found",
            "latency_ms": 12.5
        }
        
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            
            async with SARAiMCPClient("http://localhost:3000") as client:
                result = await client.call_tool("invalid.tool", {})
                
                assert result.success is False
                assert "not found" in result.error
    
    @pytest.mark.asyncio
    async def test_client_caches_tools_list(self):
        """Verifica que el cliente cachea la lista de tools."""
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "tools": [
                {"name": "tool1", "description": "Tool 1", "parameters": {}}
            ]
        }
        
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            
            async with SARAiMCPClient("http://localhost:3000") as client:
                # Primera llamada - debe hacer request
                tools1 = await client.list_tools(use_cache=True)
                assert len(tools1) == 1
                assert mock_post.call_count == 1
                
                # Segunda llamada - debe usar cache
                tools2 = await client.list_tools(use_cache=True)
                assert len(tools2) == 1
                assert mock_post.call_count == 1  # No debe aumentar
                
                # Tercera llamada sin cache - debe hacer request
                tools3 = await client.list_tools(use_cache=False)
                assert len(tools3) == 1
                assert mock_post.call_count == 2  # Debe aumentar
    
    @pytest.mark.asyncio
    async def test_client_can_get_metrics(self):
        """Verifica que el cliente puede obtener métricas Prometheus."""
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """# HELP sarai_uptime_seconds Server uptime in seconds
# TYPE sarai_uptime_seconds gauge
sarai_uptime_seconds 123.45
# HELP sarai_tools_registered Number of tools registered
# TYPE sarai_tools_registered gauge
sarai_tools_registered 2.0
"""
        
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            
            async with SARAiMCPClient("http://localhost:3000") as client:
                metrics = await client.get_metrics()
                
                assert metrics is not None
                assert "sarai_uptime_seconds" in metrics
                assert "sarai_tools_registered" in metrics
                assert "123.45" in metrics
                assert "2.0" in metrics


@pytest.mark.asyncio
async def test_integration_flow_simulation():
    """
    Test de integración que simula el flujo completo:
    HLCS → SARAi MCP Server → SAUL Module
    """
    
    # Mock de respuestas del servidor MCP
    health_response = MagicMock()
    health_response.status_code = 200
    health_response.json.return_value = {"status": "healthy"}
    
    list_tools_response = MagicMock()
    list_tools_response.status_code = 200
    list_tools_response.json.return_value = {
        "tools": [
            {"name": "saul.respond", "description": "SAUL respond", "parameters": {}},
            {"name": "saul.synthesize", "description": "SAUL synthesize", "parameters": {}}
        ]
    }
    
    call_tool_response = MagicMock()
    call_tool_response.status_code = 200
    call_tool_response.json.return_value = {
        "success": True,
        "result": {
            "response": "¡Hola! ¿En qué puedo ayudarte?",
            "template_id": "greeting",
            "confidence": 0.95,
            "latency_ms": 54.2
        },
        "latency_ms": 56.8
    }
    
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get, \
         patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        
        # Configurar mocks
        mock_get.return_value = health_response
        
        def post_side_effect(url, **kwargs):
            if "tools/list" in url:
                return list_tools_response
            elif "tools/call" in url:
                return call_tool_response
            return MagicMock()
        
        mock_post.side_effect = post_side_effect
        
        # Flujo de integración
        async with SARAiMCPClient("http://localhost:3000") as client:
            # 1. Health check
            is_healthy = await client.ping()
            assert is_healthy is True
            
            # 2. Listar tools
            tools = await client.list_tools()
            assert len(tools) == 2
            assert any(t.name == "saul.respond" for t in tools)
            
            # 3. Llamar a saul.respond
            result = await client.call_tool("saul.respond", {
                "query": "hola",
                "include_audio": False
            })
            
            assert result.success is True
            assert "Hola" in result.result["response"]
            assert result.latency_ms < 100  # < 100ms total


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
