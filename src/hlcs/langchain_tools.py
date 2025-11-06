#!/usr/bin/env python3
"""
LangChain Tools Wrapper for SARAi MCP

Convierte tools del SARAi MCP Server en herramientas nativas de LangChain,
permitiendo su uso con agentes, chains, y otros componentes del ecosistema.

Versión: 1.0.0
Autor: Equipo SARAi + IA
Fecha: 6 de noviembre de 2025

Ejemplo de uso:
    ```python
    from hlcs.langchain_tools import create_sarai_tools
    from langchain.agents import AgentExecutor, create_openai_functions_agent
    from langchain_openai import ChatOpenAI
    
    # Crear tools del MCP Server
    tools = await create_sarai_tools("http://localhost:3000")
    
    # Usar con agente LangChain
    llm = ChatOpenAI(model="gpt-4")
    agent = create_openai_functions_agent(llm, tools, prompt)
    executor = AgentExecutor(agent=agent, tools=tools)
    
    result = await executor.ainvoke({"input": "Hola, ¿cómo estás?"})
    ```
"""

from typing import Any, Dict, List, Optional, Type
from pydantic import BaseModel, Field
import asyncio
import logging

try:
    from langchain.tools import BaseTool
    from langchain.callbacks.manager import AsyncCallbackManagerForToolRun, CallbackManagerForToolRun
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    # Fallback para cuando LangChain no esté instalado
    class BaseTool:
        """Fallback BaseTool cuando LangChain no está disponible."""
        name: str
        description: str
        
        def _run(self, *args, **kwargs):
            raise NotImplementedError("LangChain not installed")
        
        async def _arun(self, *args, **kwargs):
            raise NotImplementedError("LangChain not installed")
    
    # Fallback para los callback managers
    class CallbackManagerForToolRun:
        """Fallback para CallbackManagerForToolRun."""
        pass
    
    class AsyncCallbackManagerForToolRun:
        """Fallback para AsyncCallbackManagerForToolRun."""
        pass

from hlcs.mcp_client import SARAiMCPClient, ToolDefinition

logger = logging.getLogger(__name__)


class MCPToolWrapper(BaseTool):
    """
    Wrapper que convierte un tool MCP en una herramienta de LangChain.
    
    Esta clase adapta la interfaz del SARAi MCP Server al formato esperado
    por LangChain, permitiendo usar tools MCP en agentes, chains, etc.
    
    Attributes:
        name: Nombre del tool (ej: "saul.respond")
        description: Descripción del tool
        mcp_client: Cliente MCP para comunicarse con el servidor
        tool_def: Definición completa del tool desde el servidor
    
    Examples:
        ```python
        # Crear wrapper para un tool específico
        tool = MCPToolWrapper(
            name="saul.respond",
            description="Respuesta rápida con SAUL",
            mcp_client=client,
            tool_def=tool_definition
        )
        
        # Usar sincronicamente
        result = tool.run({"query": "hola", "include_audio": False})
        
        # Usar asíncronamente (recomendado)
        result = await tool.arun({"query": "hola", "include_audio": False})
        ```
    """
    
    name: str = Field(description="Tool name")
    description: str = Field(description="Tool description")
    mcp_client: SARAiMCPClient = Field(description="MCP client instance")
    tool_def: ToolDefinition = Field(description="Tool definition from MCP")
    
    class Config:
        """Pydantic config."""
        arbitrary_types_allowed = True
    
    def _run(
        self,
        tool_input: Dict[str, Any],
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """
        Ejecuta el tool sincrónicamente (fallback).
        
        Nota: Esta es una implementación de fallback. Prefiere usar _arun()
        para mejor rendimiento y compatibilidad con async/await.
        
        Args:
            tool_input: Parámetros del tool en formato dict
            run_manager: Callback manager de LangChain
        
        Returns:
            Resultado del tool como string JSON
        """
        # Ejecutar versión async en loop sincrónico
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(self._arun(tool_input, run_manager))
            return result
        finally:
            loop.close()
    
    async def _arun(
        self,
        tool_input: Dict[str, Any],
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None
    ) -> str:
        """
        Ejecuta el tool asíncronamente (método preferido).
        
        Args:
            tool_input: Parámetros del tool en formato dict
            run_manager: Async callback manager de LangChain
        
        Returns:
            Resultado del tool como string JSON
        
        Raises:
            Exception: Si el tool falla en el servidor MCP
        """
        try:
            # Log inicio
            logger.info(f"Calling MCP tool: {self.name} with input: {tool_input}")
            
            # Llamar al tool via MCP
            result = await self.mcp_client.call_tool(
                tool_name=self.name,
                parameters=tool_input
            )
            
            # Verificar éxito
            if not result.success:
                error_msg = f"MCP tool '{self.name}' failed: {result.error}"
                logger.error(error_msg)
                raise Exception(error_msg)
            
            # Log resultado
            logger.info(f"MCP tool '{self.name}' completed in {result.latency_ms:.1f}ms")
            
            # Retornar resultado como JSON string para LangChain
            import json
            return json.dumps(result.result, ensure_ascii=False)
        
        except Exception as e:
            logger.error(f"Error executing MCP tool '{self.name}': {e}", exc_info=True)
            raise


class SAULRespondTool(MCPToolWrapper):
    """
    Tool específico para SAUL Respond.
    
    Herramienta de respuesta rápida usando el sistema SAUL.
    Proporciona respuestas template-based con latencia < 200ms.
    
    Examples:
        ```python
        tool = SAULRespondTool(mcp_client=client, tool_def=definition)
        
        # Respuesta simple
        result = await tool.arun({
            "query": "hola",
            "include_audio": False
        })
        
        # Respuesta con audio
        result = await tool.arun({
            "query": "¿cómo estás?",
            "include_audio": True
        })
        ```
    """
    
    name: str = "saul_respond"
    description: str = (
        "Respuesta rápida con SAUL (Sistema de Atención Ultra Ligero). "
        "Proporciona respuestas template-based con latencia < 200ms. "
        "Ideal para saludos, agradecimientos, preguntas simples. "
        "Parámetros: query (string, requerido), include_audio (bool, opcional)."
    )


class SAULSynthesizeTool(MCPToolWrapper):
    """
    Tool específico para SAUL Synthesize.
    
    Herramienta de síntesis de voz usando Piper TTS.
    Convierte texto a audio con latencia < 300ms.
    
    Examples:
        ```python
        tool = SAULSynthesizeTool(mcp_client=client, tool_def=definition)
        
        result = await tool.arun({
            "text": "Hola, esto es una prueba",
            "voice_model": "es_ES-sharvard-medium",
            "speed": 1.0
        })
        ```
    """
    
    name: str = "saul_synthesize"
    description: str = (
        "Síntesis de voz con SAUL usando Piper TTS. "
        "Convierte texto a audio con latencia < 300ms. "
        "Parámetros: text (string, requerido), voice_model (string, opcional), "
        "speed (float, opcional)."
    )


async def create_sarai_tools(
    mcp_url: str = "http://localhost:3000",
    timeout: int = 30,
    use_specific_wrappers: bool = True
) -> List[BaseTool]:
    """
    Crea lista de herramientas LangChain desde el SARAi MCP Server.
    
    Esta función se conecta al servidor MCP, obtiene la lista de tools
    disponibles, y crea wrappers de LangChain para cada uno.
    
    Args:
        mcp_url: URL del SARAi MCP Server
        timeout: Timeout para conexión en segundos
        use_specific_wrappers: Si True, usa wrappers específicos (SAULRespondTool)
                               Si False, usa MCPToolWrapper genérico
    
    Returns:
        Lista de herramientas LangChain listas para usar
    
    Raises:
        Exception: Si no se puede conectar al servidor o no hay tools disponibles
    
    Examples:
        ```python
        # Crear todas las tools disponibles
        tools = await create_sarai_tools("http://localhost:3000")
        
        # Usar con agente
        from langchain.agents import AgentExecutor
        executor = AgentExecutor(agent=agent, tools=tools)
        ```
    """
    if not LANGCHAIN_AVAILABLE:
        raise ImportError(
            "LangChain is not installed. Install with: pip install langchain"
        )
    
    logger.info(f"Creating SARAi tools from MCP server: {mcp_url}")
    
    # Conectar con el servidor MCP
    async with SARAiMCPClient(mcp_url, timeout=timeout) as client:
        
        # Verificar health del servidor
        if not await client.ping():
            raise Exception(f"SARAi MCP Server at {mcp_url} is not available")
        
        # Obtener lista de tools
        tool_definitions = await client.list_tools()
        
        if not tool_definitions:
            raise Exception(f"No tools available from MCP server at {mcp_url}")
        
        logger.info(f"Found {len(tool_definitions)} tools from MCP server")
        
        # Crear wrappers para cada tool
        tools: List[BaseTool] = []
        
        for tool_def in tool_definitions:
            # Usar wrapper específico si está disponible y habilitado
            if use_specific_wrappers:
                if tool_def.name == "saul.respond":
                    tool = SAULRespondTool(
                        mcp_client=client,
                        tool_def=tool_def
                    )
                elif tool_def.name == "saul.synthesize":
                    tool = SAULSynthesizeTool(
                        mcp_client=client,
                        tool_def=tool_def
                    )
                else:
                    # Wrapper genérico para otros tools
                    tool = MCPToolWrapper(
                        name=tool_def.name.replace(".", "_"),  # LangChain prefiere snake_case
                        description=tool_def.description,
                        mcp_client=client,
                        tool_def=tool_def
                    )
            else:
                # Wrapper genérico para todos
                tool = MCPToolWrapper(
                    name=tool_def.name.replace(".", "_"),
                    description=tool_def.description,
                    mcp_client=client,
                    tool_def=tool_def
                )
            
            tools.append(tool)
            logger.info(f"Created LangChain tool: {tool.name}")
        
        return tools


async def create_saul_tools_only(
    mcp_url: str = "http://localhost:3000",
    timeout: int = 30
) -> List[BaseTool]:
    """
    Crea solo las herramientas SAUL (respond y synthesize).
    
    Versión optimizada que solo carga los tools SAUL, útil cuando
    solo necesitas respuestas rápidas y TTS.
    
    Args:
        mcp_url: URL del SARAi MCP Server
        timeout: Timeout para conexión en segundos
    
    Returns:
        Lista con SAULRespondTool y SAULSynthesizeTool
    
    Examples:
        ```python
        tools = await create_saul_tools_only()
        # tools = [SAULRespondTool, SAULSynthesizeTool]
        ```
    """
    all_tools = await create_sarai_tools(mcp_url, timeout, use_specific_wrappers=True)
    
    # Filtrar solo tools SAUL
    saul_tools = [
        tool for tool in all_tools
        if tool.name in ["saul_respond", "saul_synthesize"]
    ]
    
    if not saul_tools:
        raise Exception("No SAUL tools found in MCP server")
    
    logger.info(f"Created {len(saul_tools)} SAUL tools")
    return saul_tools


# Conveniencia: función sincrónica wrapper
def create_sarai_tools_sync(
    mcp_url: str = "http://localhost:3000",
    timeout: int = 30,
    use_specific_wrappers: bool = True
) -> List[BaseTool]:
    """
    Versión sincrónica de create_sarai_tools (conveniencia).
    
    Nota: Prefiere usar la versión async cuando sea posible para mejor rendimiento.
    
    Args:
        mcp_url: URL del SARAi MCP Server
        timeout: Timeout para conexión en segundos
        use_specific_wrappers: Usar wrappers específicos vs genéricos
    
    Returns:
        Lista de herramientas LangChain
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(
            create_sarai_tools(mcp_url, timeout, use_specific_wrappers)
        )
    finally:
        loop.close()


# Exports públicos
__all__ = [
    "MCPToolWrapper",
    "SAULRespondTool",
    "SAULSynthesizeTool",
    "create_sarai_tools",
    "create_saul_tools_only",
    "create_sarai_tools_sync",
    "LANGCHAIN_AVAILABLE",
]
