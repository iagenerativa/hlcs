#!/usr/bin/env python3
"""
Ejemplo de Agente usando SARAi MCP Server

Demuestra cómo crear un agente simple que usa el cliente MCP
para acceder a las capacidades de SARAi (SAUL, Vision, etc.).

Este ejemplo NO requiere LangChain - usa el cliente MCP directamente.

Versión: 1.0.0
Autor: Equipo SARAi + IA
Fecha: 6 de noviembre de 2025

Uso:
    # Asegúrate de que SARAi MCP Server esté corriendo
    python examples/agent_with_sarai_mcp.py
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List

# Agregar src/ al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from hlcs.mcp_client import SARAiMCPClient

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

logger = logging.getLogger(__name__)


class SimpleAgent:
    """
    Agente simple que usa SARAi MCP Server.
    
    Este agente puede:
    - Responder preguntas simples usando SAUL
    - Sintetizar voz
    - Acceder a otras capacidades vía MCP
    
    Attributes:
        mcp_url: URL del SARAi MCP Server
        client: Cliente MCP conectado
        tools: Lista de tools disponibles
    """
    
    def __init__(self, mcp_url: str = "http://localhost:3000"):
        """
        Inicializa el agente.
        
        Args:
            mcp_url: URL del SARAi MCP Server
        """
        self.mcp_url = mcp_url
        self.client: SARAiMCPClient = None
        self.tools: List = []
    
    async def initialize(self):
        """Conecta con el servidor MCP y carga tools."""
        logger.info(f"Conectando con SARAi MCP Server en {self.mcp_url}...")
        
        # Crear cliente
        self.client = SARAiMCPClient(self.mcp_url)
        await self.client.__aenter__()
        
        # Verificar health
        if not await self.client.ping():
            raise Exception(f"SARAi MCP Server en {self.mcp_url} no disponible")
        
        logger.info("✅ Conectado con SARAi MCP Server")
        
        # Cargar tools
        self.tools = await self.client.list_tools()
        logger.info(f"✅ {len(self.tools)} tools disponibles:")
        for tool in self.tools:
            logger.info(f"   - {tool.name}: {tool.description}")
    
    async def shutdown(self):
        """Cierra la conexión con el servidor."""
        if self.client:
            await self.client.close()
            logger.info("Conexión cerrada")
    
    async def think(self, user_input: str) -> Dict[str, Any]:
        """
        Proceso de razonamiento del agente.
        
        Determina qué tool usar basándose en el input del usuario.
        
        Args:
            user_input: Entrada del usuario
        
        Returns:
            Dict con la decisión del agente
        """
        user_lower = user_input.lower()
        
        # Lógica simple de decisión
        if any(word in user_lower for word in ["sintetiza", "lee", "di en voz alta"]):
            return {
                "tool": "saul.synthesize",
                "reasoning": "Usuario pide síntesis de voz",
                "parameters": {
                    "text": user_input.replace("sintetiza", "").replace("lee", "").strip(),
                    "voice_model": "es_ES-sharvard-medium",
                    "speed": 1.0
                }
            }
        else:
            # Por defecto, usar SAUL para responder
            return {
                "tool": "saul.respond",
                "reasoning": "Respuesta rápida con SAUL",
                "parameters": {
                    "query": user_input,
                    "include_audio": False
                }
            }
    
    async def act(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ejecuta la acción decidida.
        
        Args:
            decision: Decisión del método think()
        
        Returns:
            Resultado de la acción
        """
        tool_name = decision["tool"]
        parameters = decision["parameters"]
        
        logger.info(f"🤖 Ejecutando: {tool_name}")
        logger.info(f"   Razonamiento: {decision['reasoning']}")
        logger.info(f"   Parámetros: {parameters}")
        
        # Llamar al tool via MCP
        result = await self.client.call_tool(tool_name, parameters)
        
        if not result.success:
            logger.error(f"❌ Error: {result.error}")
            return {"success": False, "error": result.error}
        
        logger.info(f"✅ Completado en {result.latency_ms:.1f}ms")
        
        return {
            "success": True,
            "result": result.result,
            "latency_ms": result.latency_ms
        }
    
    async def run(self, user_input: str) -> Dict[str, Any]:
        """
        Ciclo completo: pensar → actuar.
        
        Args:
            user_input: Entrada del usuario
        
        Returns:
            Resultado final
        """
        logger.info(f"\n{'=' * 80}")
        logger.info(f"📥 Usuario: {user_input}")
        logger.info(f"{'=' * 80}")
        
        # 1. Pensar: decidir qué tool usar
        decision = await self.think(user_input)
        
        # 2. Actuar: ejecutar el tool
        result = await self.act(decision)
        
        return result


async def demo():
    """Demostración del agente."""
    
    print("=" * 80)
    print("  AGENTE SIMPLE CON SARAi MCP")
    print("=" * 80)
    print()
    
    # Crear agente
    agent = SimpleAgent("http://localhost:3000")
    
    try:
        # Inicializar
        await agent.initialize()
        print()
        
        # Ejemplos de interacción
        test_cases = [
            "hola",
            "¿cómo estás?",
            "gracias",
            "¿qué hora es?",
        ]
        
        for i, user_input in enumerate(test_cases, 1):
            result = await agent.run(user_input)
            
            if result["success"]:
                print(f"\n🤖 Agente responde:")
                if "response" in result["result"]:
                    print(f"   {result['result']['response']}")
                if "template_id" in result["result"]:
                    print(f"   (Template: {result['result']['template_id']})")
                if "audio" in result["result"]:
                    audio_size = len(result["result"]["audio"])
                    print(f"   (Audio: {audio_size} bytes)")
                print(f"   ⏱️  Latencia: {result['latency_ms']:.1f}ms")
            else:
                print(f"\n❌ Error: {result['error']}")
            
            if i < len(test_cases):
                await asyncio.sleep(0.5)  # Pausa entre requests
        
        print()
        print("=" * 80)
        print("  ✅ DEMO COMPLETADO")
        print("=" * 80)
    
    finally:
        await agent.shutdown()


async def interactive_mode():
    """Modo interactivo con el agente."""
    
    print("=" * 80)
    print("  MODO INTERACTIVO - Agente SARAi MCP")
    print("=" * 80)
    print()
    print("Comandos:")
    print("  - Escribe cualquier pregunta o mensaje")
    print("  - 'salir' o 'exit' para terminar")
    print("  - 'tools' para ver tools disponibles")
    print()
    
    agent = SimpleAgent("http://localhost:3000")
    
    try:
        await agent.initialize()
        print()
        
        while True:
            # Leer input del usuario
            try:
                user_input = input("👤 Tú: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nSaliendo...")
                break
            
            if not user_input:
                continue
            
            # Comandos especiales
            if user_input.lower() in ["salir", "exit", "quit"]:
                print("¡Hasta luego!")
                break
            
            if user_input.lower() == "tools":
                print("\n🔧 Tools disponibles:")
                for tool in agent.tools:
                    print(f"   - {tool.name}: {tool.description}")
                print()
                continue
            
            # Ejecutar agente
            result = await agent.run(user_input)
            
            # Mostrar resultado
            if result["success"]:
                print(f"🤖 Agente: {result['result'].get('response', 'OK')}")
                print(f"   ⏱️  {result['latency_ms']:.1f}ms\n")
            else:
                print(f"❌ Error: {result['error']}\n")
    
    finally:
        await agent.shutdown()


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Agente simple con SARAi MCP")
    parser.add_argument(
        "--mode",
        choices=["demo", "interactive"],
        default="demo",
        help="Modo de ejecución (default: demo)"
    )
    parser.add_argument(
        "--mcp-url",
        default="http://localhost:3000",
        help="URL del SARAi MCP Server (default: http://localhost:3000)"
    )
    
    args = parser.parse_args()
    
    try:
        if args.mode == "demo":
            await demo()
        else:
            await interactive_mode()
    except KeyboardInterrupt:
        print("\n\nInterrumpido por el usuario")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
