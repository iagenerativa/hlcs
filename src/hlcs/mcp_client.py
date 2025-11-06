"""
SARAi MCP Client (v2.0)

Cliente HTTP para consumir SARAi MCP Server usando Model Context Protocol estándar.

Actualizado para usar:
  - POST /tools/list - Listar tools disponibles
  - POST /tools/call - Ejecutar tool
  - POST /resources/list - Listar resources
  - POST /resources/read - Leer resource
  - GET /health - Health check
  - GET /metrics - Métricas Prometheus

Version: 2.0.0 (MCP Protocol Standard)
"""

import httpx
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import asyncio

logger = logging.getLogger(__name__)


@dataclass
class ToolCallResult:
    """Resultado de una llamada a tool MCP."""
    success: bool
    result: Any
    error: Optional[str] = None
    latency_ms: float = 0.0


@dataclass
class ToolDefinition:
    """Definición de un tool MCP."""
    name: str
    description: str
    parameters: Dict[str, Any]


class SARAiMCPClient:
    """
    Cliente para SARAi MCP Server (Model Context Protocol).
    
    Consume tools expuestos por SARAi vía protocolo MCP estándar.
    
    Example:
        >>> client = SARAiMCPClient("http://localhost:3000")
        >>> result = await client.call_tool("saul.respond", {"query": "hola"})
        >>> print(result.result["response"])
        ¡Hola! ¿En qué puedo ayudarte?
    """
    
    def __init__(
        self,
        base_url: str = "http://localhost:3000",
        timeout: int = 30,
        max_retries: int = 3
    ):
        """
        Initialize SARAi MCP Client.
        
        Args:
            base_url: Base URL del SARAi MCP Server
            timeout: Timeout en segundos
            max_retries: Máximo de reintentos
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20)
        )
        self._tools_cache: Optional[List[ToolDefinition]] = None
        
        logger.info(f"SARAi MCP Client v2.0 initialized: {base_url}")
    
    async def call_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        timeout: Optional[int] = None
    ) -> ToolCallResult:
        """
        Llamar a un tool usando MCP Protocol.
        
        Args:
            tool_name: Nombre del tool (ej: "saul.respond", "vision.analyze")
            parameters: Parámetros del tool
            timeout: Override timeout (opcional)
        
        Returns:
            ToolCallResult con resultado o error
        
        Example:
            >>> result = await client.call_tool("saul.respond", {
            ...     "query": "¿Cómo estás?",
            ...     "include_audio": False
            ... })
            >>> print(result.result["response"])
        """
        import time
        start_time = time.time()
        
        try:
            # MCP Protocol: POST /tools/call
            request_payload = {
                "name": tool_name,
                "parameters": parameters
            }
            
            logger.debug(f"MCP call_tool: {tool_name} with params: {list(parameters.keys())}")
            
            response = await self._client.post(
                f"{self.base_url}/tools/call",
                json=request_payload,
                timeout=timeout or self.timeout
            )
            
            latency_ms = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                
                # MCP response structure: {success, result, error, latency_ms}
                logger.debug(
                    f"Tool {tool_name} → success={data.get('success')}, "
                    f"latency={data.get('latency_ms', 0):.1f}ms"
                )
                
                return ToolCallResult(
                    success=data.get("success", True),
                    result=data.get("result"),
                    error=data.get("error"),
                    latency_ms=data.get("latency_ms", latency_ms)
                )
            else:
                error_msg = f"HTTP {response.status_code}: {response.text[:200]}"
                logger.warning(f"Tool {tool_name} failed: {error_msg}")
                return ToolCallResult(
                    success=False,
                    result=None,
                    error=error_msg,
                    latency_ms=latency_ms
                )
        
        except httpx.TimeoutException:
            latency_ms = (time.time() - start_time) * 1000
            error_msg = f"Timeout after {timeout or self.timeout}s"
            logger.error(f"Tool {tool_name} timeout: {error_msg}")
            return ToolCallResult(
                success=False,
                result=None,
                error=error_msg,
                latency_ms=latency_ms
            )
        
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            error_msg = f"Error: {str(e)}"
            logger.error(f"Tool {tool_name} error: {error_msg}", exc_info=True)
            return ToolCallResult(
                success=False,
                result=None,
                error=error_msg,
                latency_ms=latency_ms
            )
    
    async def list_tools(self, use_cache: bool = True) -> List[ToolDefinition]:
        """
        Listar tools disponibles usando MCP Protocol.
        
        Args:
            use_cache: Usar cache local (default: True)
        
        Returns:
            Lista de ToolDefinition
        """
        if use_cache and self._tools_cache is not None:
            return self._tools_cache
        
        try:
            # MCP Protocol: POST /tools/list
            response = await self._client.post(f"{self.base_url}/tools/list")
            
            if response.status_code == 200:
                data = response.json()
                tools_data = data.get("tools", [])
                
                tools = [
                    ToolDefinition(
                        name=tool["name"],
                        description=tool.get("description", ""),
                        parameters=tool.get("parameters", {})
                    )
                    for tool in tools_data
                ]
                
                self._tools_cache = tools
                logger.info(f"Listed {len(tools)} tools from SARAi MCP Server")
                
                return tools
            
            logger.warning(f"Failed to list tools: HTTP {response.status_code}")
            return []
        
        except Exception as e:
            logger.error(f"Failed to list tools: {e}")
            return []
    
    async def ping(self) -> bool:
        """
        Health check del SARAi MCP Server.
        
        Returns:
            True si el servidor está disponible
        """
        try:
            response = await self._client.get(
                f"{self.base_url}/health",
                timeout=5.0
            )
            
            if response.status_code == 200:
                data = response.json()
                status = data.get("status", "unknown")
                logger.debug(f"SARAi MCP Server health: {status}")
                return status == "healthy"
            
            return False
        
        except Exception as e:
            logger.debug(f"SARAi MCP Server ping failed: {e}")
            return False
    
    async def get_metrics(self) -> Optional[str]:
        """
        Obtener métricas Prometheus del servidor.
        
        Returns:
            Métricas en formato Prometheus (texto) o None
        """
        try:
            response = await self._client.get(
                f"{self.base_url}/metrics",
                timeout=5.0
            )
            
            if response.status_code == 200:
                return response.text
            
            return None
        
        except Exception as e:
            logger.error(f"Failed to get metrics: {e}")
            return None
    
    async def close(self):
        """Cerrar cliente HTTP."""
        await self._client.aclose()
        logger.debug("SARAi MCP Client closed")
    
    async def __aenter__(self):
        """Context manager support."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager support."""
        await self.close()


# Convenience functions
async def create_sarai_client(base_url: str = "http://localhost:3000") -> SARAiMCPClient:
    """
    Factory function para crear cliente SARAi MCP.
    
    Args:
        base_url: URL del SARAi MCP Server
    
    Returns:
        SARAiMCPClient configurado
    
    Example:
        >>> async with create_sarai_client() as client:
        ...     tools = await client.list_tools()
        ...     print(f"Available tools: {[t.name for t in tools]}")
    """
    return SARAiMCPClient(base_url)


# Alias para compatibilidad
MCPClient = SARAiMCPClient
