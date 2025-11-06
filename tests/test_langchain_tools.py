#!/usr/bin/env python3
"""
Tests para LangChain Tools Wrapper

Valida que los wrappers MCP → LangChain funcionan correctamente
con el ecosistema de LangChain.

Versión: 1.0.0
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json
import sys
from pathlib import Path

# Agregar src/ al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from hlcs.langchain_tools import (
    MCPToolWrapper,
    SAULRespondTool,
    SAULSynthesizeTool,
    create_sarai_tools,
    create_saul_tools_only,
    LANGCHAIN_AVAILABLE,
)
from hlcs.mcp_client import SARAiMCPClient, ToolCallResult, ToolDefinition


@pytest.fixture
def mock_mcp_client():
    """Mock del cliente MCP."""
    client = MagicMock(spec=SARAiMCPClient)
    client.call_tool = AsyncMock()
    client.list_tools = AsyncMock()
    client.ping = AsyncMock(return_value=True)
    return client


@pytest.fixture
def saul_respond_tool_def():
    """Definición del tool saul.respond."""
    return ToolDefinition(
        name="saul.respond",
        description="Respuesta rápida con SAUL",
        parameters={
            "query": {"type": "string", "required": True},
            "include_audio": {"type": "boolean", "required": False}
        }
    )


@pytest.fixture
def saul_synthesize_tool_def():
    """Definición del tool saul.synthesize."""
    return ToolDefinition(
        name="saul.synthesize",
        description="Síntesis de voz con Piper TTS",
        parameters={
            "text": {"type": "string", "required": True},
            "voice_model": {"type": "string", "required": False},
            "speed": {"type": "number", "required": False}
        }
    )


class TestMCPToolWrapper:
    """Tests para MCPToolWrapper genérico."""
    
    @pytest.mark.asyncio
    async def test_wrapper_can_call_tool_async(self, mock_mcp_client, saul_respond_tool_def):
        """Verifica que el wrapper puede llamar a un tool asíncronamente."""
        
        # Mock de respuesta exitosa
        mock_mcp_client.call_tool.return_value = ToolCallResult(
            success=True,
            result={
                "response": "¡Hola! ¿En qué puedo ayudarte?",
                "template_id": "greeting",
                "confidence": 0.95
            },
            latency_ms=54.2
        )
        
        # Crear wrapper
        wrapper = MCPToolWrapper(
            name="saul.respond",
            description="Test tool",
            mcp_client=mock_mcp_client,
            tool_def=saul_respond_tool_def
        )
        
        # Ejecutar tool
        result = await wrapper._arun({"query": "hola", "include_audio": False})
        
        # Verificar
        assert result is not None
        result_dict = json.loads(result)
        assert result_dict["response"] == "¡Hola! ¿En qué puedo ayudarte?"
        assert result_dict["template_id"] == "greeting"
        assert result_dict["confidence"] == 0.95
        
        # Verificar que se llamó al cliente MCP
        mock_mcp_client.call_tool.assert_called_once_with(
            tool_name="saul.respond",
            parameters={"query": "hola", "include_audio": False}
        )
    
    @pytest.mark.asyncio
    async def test_wrapper_handles_tool_error(self, mock_mcp_client, saul_respond_tool_def):
        """Verifica que el wrapper maneja errores del tool correctamente."""
        
        # Mock de respuesta con error
        mock_mcp_client.call_tool.return_value = ToolCallResult(
            success=False,
            error="Tool execution failed: connection timeout",
            latency_ms=5000.0
        )
        
        wrapper = MCPToolWrapper(
            name="saul.respond",
            description="Test tool",
            mcp_client=mock_mcp_client,
            tool_def=saul_respond_tool_def
        )
        
        # Debe lanzar excepción
        with pytest.raises(Exception) as exc_info:
            await wrapper._arun({"query": "test"})
        
        assert "failed" in str(exc_info.value).lower()
    
    def test_wrapper_has_correct_attributes(self, mock_mcp_client, saul_respond_tool_def):
        """Verifica que el wrapper tiene los atributos correctos."""
        
        wrapper = MCPToolWrapper(
            name="test.tool",
            description="Test tool description",
            mcp_client=mock_mcp_client,
            tool_def=saul_respond_tool_def
        )
        
        assert wrapper.name == "test.tool"
        assert wrapper.description == "Test tool description"
        assert wrapper.mcp_client == mock_mcp_client
        assert wrapper.tool_def == saul_respond_tool_def


class TestSAULSpecificTools:
    """Tests para wrappers específicos de SAUL."""
    
    @pytest.mark.asyncio
    async def test_saul_respond_tool(self, mock_mcp_client, saul_respond_tool_def):
        """Verifica que SAULRespondTool funciona correctamente."""
        
        mock_mcp_client.call_tool.return_value = ToolCallResult(
            success=True,
            result={
                "response": "Gracias por tu mensaje",
                "template_id": "thanks",
                "confidence": 0.88
            },
            latency_ms=62.1
        )
        
        tool = SAULRespondTool(
            mcp_client=mock_mcp_client,
            tool_def=saul_respond_tool_def
        )
        
        # Verificar nombre y descripción predefinidos
        assert tool.name == "saul_respond"
        assert "Respuesta rápida con SAUL" in tool.description
        assert "latencia < 200ms" in tool.description
        
        # Ejecutar
        result = await tool._arun({"query": "gracias", "include_audio": False})
        result_dict = json.loads(result)
        
        assert result_dict["response"] == "Gracias por tu mensaje"
        assert result_dict["template_id"] == "thanks"
    
    @pytest.mark.asyncio
    async def test_saul_synthesize_tool(self, mock_mcp_client, saul_synthesize_tool_def):
        """Verifica que SAULSynthesizeTool funciona correctamente."""
        
        mock_mcp_client.call_tool.return_value = ToolCallResult(
            success=True,
            result={
                "audio": "base64encodedaudio==",
                "duration": 2.5,
                "sample_rate": 22050
            },
            latency_ms=185.3
        )
        
        tool = SAULSynthesizeTool(
            mcp_client=mock_mcp_client,
            tool_def=saul_synthesize_tool_def
        )
        
        # Verificar nombre y descripción
        assert tool.name == "saul_synthesize"
        assert "Síntesis de voz" in tool.description
        assert "Piper TTS" in tool.description
        
        # Ejecutar
        result = await tool._arun({
            "text": "Hola mundo",
            "voice_model": "es_ES-sharvard-medium",
            "speed": 1.0
        })
        result_dict = json.loads(result)
        
        assert "audio" in result_dict
        assert result_dict["duration"] == 2.5
        assert result_dict["sample_rate"] == 22050


class TestCreateSARAiTools:
    """Tests para la función de creación de tools."""
    
    @pytest.mark.asyncio
    async def test_create_sarai_tools_success(self):
        """Verifica que create_sarai_tools crea todas las tools disponibles."""
        
        # Mock del cliente y sus respuestas
        with patch("hlcs.langchain_tools.SARAiMCPClient") as MockClient:
            mock_client_instance = MagicMock()
            mock_client_instance.ping = AsyncMock(return_value=True)
            mock_client_instance.list_tools = AsyncMock(return_value=[
                ToolDefinition(
                    name="saul.respond",
                    description="SAUL respond",
                    parameters={}
                ),
                ToolDefinition(
                    name="saul.synthesize",
                    description="SAUL synthesize",
                    parameters={}
                ),
            ])
            
            # Configurar context manager
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=None)
            
            # Crear tools
            tools = await create_sarai_tools("http://localhost:3000")
            
            # Verificar
            assert len(tools) == 2
            assert any(t.name == "saul_respond" for t in tools)
            assert any(t.name == "saul_synthesize" for t in tools)
    
    @pytest.mark.asyncio
    async def test_create_sarai_tools_server_unavailable(self):
        """Verifica que lanza excepción si el servidor no está disponible."""
        
        with patch("hlcs.langchain_tools.SARAiMCPClient") as MockClient:
            mock_client_instance = MagicMock()
            mock_client_instance.ping = AsyncMock(return_value=False)
            
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=None)
            
            # Debe lanzar excepción
            with pytest.raises(Exception) as exc_info:
                await create_sarai_tools("http://localhost:3000")
            
            assert "not available" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_create_sarai_tools_no_tools(self):
        """Verifica que lanza excepción si no hay tools disponibles."""
        
        with patch("hlcs.langchain_tools.SARAiMCPClient") as MockClient:
            mock_client_instance = MagicMock()
            mock_client_instance.ping = AsyncMock(return_value=True)
            mock_client_instance.list_tools = AsyncMock(return_value=[])
            
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=None)
            
            # Debe lanzar excepción
            with pytest.raises(Exception) as exc_info:
                await create_sarai_tools("http://localhost:3000")
            
            assert "no tools" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_create_saul_tools_only(self):
        """Verifica que create_saul_tools_only filtra correctamente."""
        
        with patch("hlcs.langchain_tools.SARAiMCPClient") as MockClient:
            mock_client_instance = MagicMock()
            mock_client_instance.ping = AsyncMock(return_value=True)
            mock_client_instance.list_tools = AsyncMock(return_value=[
                ToolDefinition(name="saul.respond", description="SAUL", parameters={}),
                ToolDefinition(name="saul.synthesize", description="SAUL", parameters={}),
                ToolDefinition(name="vision.analyze", description="Vision", parameters={}),
            ])
            
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=None)
            
            # Crear solo SAUL tools
            tools = await create_saul_tools_only("http://localhost:3000")
            
            # Verificar que solo tiene SAUL tools
            assert len(tools) == 2
            assert all(t.name in ["saul_respond", "saul_synthesize"] for t in tools)


@pytest.mark.skipif(not LANGCHAIN_AVAILABLE, reason="LangChain not installed")
class TestLangChainIntegration:
    """Tests de integración con LangChain (solo si está instalado)."""
    
    @pytest.mark.asyncio
    async def test_tool_is_langchain_compatible(self, mock_mcp_client, saul_respond_tool_def):
        """Verifica que el wrapper es compatible con la interfaz de LangChain."""
        
        mock_mcp_client.call_tool.return_value = ToolCallResult(
            success=True,
            result={"response": "test"},
            latency_ms=50.0
        )
        
        tool = SAULRespondTool(
            mcp_client=mock_mcp_client,
            tool_def=saul_respond_tool_def
        )
        
        # Verificar que tiene los atributos requeridos por LangChain
        assert hasattr(tool, "name")
        assert hasattr(tool, "description")
        assert hasattr(tool, "_run")
        assert hasattr(tool, "_arun")
        
        # Verificar que es instancia de BaseTool
        from langchain.tools import BaseTool
        assert isinstance(tool, BaseTool)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
