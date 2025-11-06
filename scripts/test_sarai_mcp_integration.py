#!/usr/bin/env python3
"""
Test de Integración HLCS → SARAi MCP Server → SAUL

Demuestra el flujo completo end-to-end de la arquitectura modular:
  1. HLCS inicia y conecta con SARAi MCP Server
  2. Lista tools disponibles
  3. Llama a saul.respond para respuestas rápidas
  4. Llama a saul.synthesize para TTS
  5. Valida latencias y respuestas

Requisitos:
  - SARAi MCP Server corriendo en http://localhost:3000
  - (Opcional) SAUL gRPC Server en localhost:50051

Uso:
    python scripts/test_sarai_mcp_integration.py
"""

import asyncio
import logging
import sys
from pathlib import Path

# Agregar src/ al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from hlcs.mcp_client import SARAiMCPClient

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger = logging.getLogger(__name__)


async def test_integration():
    """Test completo de integración HLCS → SARAi MCP → SAUL."""
    
    print("=" * 80)
    print("  HLCS → SARAi MCP Server → SAUL - Test de Integración E2E")
    print("=" * 80)
    print()
    
    # 1. Conectar con SARAi MCP Server
    print("🔗 Paso 1: Conectando con SARAi MCP Server...")
    
    async with SARAiMCPClient("http://localhost:3000", timeout=10) as client:
        
        # 2. Health check
        print("🏥 Paso 2: Verificando health del servidor...")
        is_healthy = await client.ping()
        
        if not is_healthy:
            print("❌ SARAi MCP Server no está disponible")
            print("   Por favor, inicia el servidor con:")
            print("   python scripts/start_mcp_server.py")
            return False
        
        print("✅ SARAi MCP Server está healthy")
        print()
        
        # 3. Listar tools disponibles
        print("📋 Paso 3: Listando tools disponibles...")
        tools = await client.list_tools()
        
        if not tools:
            print("❌ No se encontraron tools disponibles")
            return False
        
        print(f"✅ Encontrados {len(tools)} tools:")
        for tool in tools:
            print(f"   - {tool.name}: {tool.description}")
        print()
        
        # 4. Test: saul.respond (simple)
        print("💬 Paso 4: Probando saul.respond (query simple)...")
        result1 = await client.call_tool("saul.respond", {
            "query": "hola",
            "include_audio": False
        })
        
        if not result1.success:
            print(f"❌ saul.respond failed: {result1.error}")
            return False
        
        print(f"✅ saul.respond exitoso:")
        print(f"   Query: 'hola'")
        print(f"   Response: {result1.result.get('response', 'N/A')}")
        print(f"   Template: {result1.result.get('template_id', 'N/A')}")
        print(f"   Confidence: {result1.result.get('confidence', 0):.2f}")
        print(f"   Latency: {result1.latency_ms:.1f}ms")
        print()
        
        # 5. Test: saul.respond (con audio)
        print("🔊 Paso 5: Probando saul.respond (con audio TTS)...")
        result2 = await client.call_tool("saul.respond", {
            "query": "¿cómo estás?",
            "include_audio": True
        })
        
        if not result2.success:
            print(f"❌ saul.respond (audio) failed: {result2.error}")
            return False
        
        audio_size = len(result2.result.get("audio", "")) if "audio" in result2.result else 0
        
        print(f"✅ saul.respond (audio) exitoso:")
        print(f"   Query: '¿cómo estás?'")
        print(f"   Response: {result2.result.get('response', 'N/A')}")
        print(f"   Template: {result2.result.get('template_id', 'N/A')}")
        print(f"   Audio size: {audio_size} bytes")
        print(f"   Latency: {result2.latency_ms:.1f}ms")
        print()
        
        # 6. Test: saul.synthesize
        print("🎤 Paso 6: Probando saul.synthesize (solo TTS)...")
        result3 = await client.call_tool("saul.synthesize", {
            "text": "Esto es una prueba de síntesis de voz desde HLCS.",
            "voice_model": "es_ES-sharvard-medium",
            "speed": 1.0
        })
        
        if not result3.success:
            print(f"❌ saul.synthesize failed: {result3.error}")
            return False
        
        audio_size3 = len(result3.result.get("audio", "")) if "audio" in result3.result else 0
        
        print(f"✅ saul.synthesize exitoso:")
        print(f"   Text: 'Esto es una prueba...'")
        print(f"   Audio size: {audio_size3} bytes")
        print(f"   Duration: {result3.result.get('duration', 0):.2f}s")
        print(f"   Sample rate: {result3.result.get('sample_rate', 0)} Hz")
        print(f"   Latency: {result3.latency_ms:.1f}ms")
        print()
        
        # 7. Test: Múltiples queries
        print("🔄 Paso 7: Probando múltiples queries secuenciales...")
        queries = ["hola", "gracias", "¿qué hora es?", "necesito ayuda"]
        latencies = []
        
        for i, query in enumerate(queries, 1):
            result = await client.call_tool("saul.respond", {
                "query": query,
                "include_audio": False
            })
            
            if result.success:
                latencies.append(result.latency_ms)
                print(f"   Query {i}/4: '{query}' → {result.result.get('response', 'N/A')[:50]}... "
                      f"({result.latency_ms:.1f}ms)")
            else:
                print(f"   Query {i}/4: '{query}' → ERROR: {result.error}")
        
        avg_latency = sum(latencies) / len(latencies) if latencies else 0
        print(f"✅ Queries completadas: {len(latencies)}/4")
        print(f"   Latencia promedio: {avg_latency:.1f}ms")
        print()
        
        # 8. Métricas del servidor
        print("📊 Paso 8: Obteniendo métricas del servidor...")
        metrics = await client.get_metrics()
        
        if metrics:
            # Extraer algunas métricas relevantes
            lines = metrics.split("\n")
            relevant_metrics = [l for l in lines if any(
                k in l for k in ["uptime", "requests_total", "tools_registered"]
            ) and not l.startswith("#")]
            
            print("✅ Métricas del servidor:")
            for line in relevant_metrics[:5]:  # Mostrar primeras 5
                print(f"   {line}")
        else:
            print("⚠️  No se pudieron obtener métricas")
        
        print()
    
    # Resumen final
    print("=" * 80)
    print("  ✅ TEST DE INTEGRACIÓN COMPLETADO EXITOSAMENTE")
    print("=" * 80)
    print()
    print("Arquitectura validada:")
    print("  Usuario → HLCS → SARAi MCP Server (http://localhost:3000)")
    print("                 → SAUL Module (fallback mode)")
    print("                 → Respuesta al Usuario")
    print()
    print("KPIs logrados:")
    print(f"  - Tools disponibles: {len(tools)}")
    print(f"  - Latencia saul.respond: {result1.latency_ms:.1f}ms")
    print(f"  - Latencia saul.respond+TTS: {result2.latency_ms:.1f}ms")
    print(f"  - Latencia saul.synthesize: {result3.latency_ms:.1f}ms")
    print(f"  - Latencia promedio (4 queries): {avg_latency:.1f}ms")
    print()
    
    return True


async def main():
    """Main entry point."""
    try:
        success = await test_integration()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrumpido por el usuario")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error en test de integración: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
