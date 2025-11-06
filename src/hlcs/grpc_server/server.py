"""
HLCS gRPC Server

Servidor gRPC principal en puerto 4000.
"""

import asyncio
import logging
import os
from concurrent import futures
from typing import Dict, Any

# Nota: En producción, importar stubs generados:
# from .generated import hlcs_pb2, hlcs_pb2_grpc

logger = logging.getLogger(__name__)

# Configuración
GRPC_PORT = int(os.getenv("HLCS_GRPC_PORT", "4000"))
MAX_WORKERS = int(os.getenv("HLCS_MAX_WORKERS", "10"))


class HLCSServicer:
    """
    Implementación del servicio HLCS.
    
    Nota: Esta es una versión simplificada sin los stubs gRPC reales.
    Ejecutar `bash scripts/generate_proto.sh` para generar código completo.
    """
    
    def __init__(self, orchestrator):
        self.orchestrator = orchestrator
        logger.info("HLCS gRPC Servicer initialized")
    
    async def ProcessQuery(self, request, context):
        """Procesar query."""
        try:
            result = await self.orchestrator.process(
                query=request.query,
                image_url=getattr(request, 'image_url', None),
                audio_url=getattr(request, 'audio_url', None),
                context=dict(getattr(request, 'context', {})),
                user_id=getattr(request, 'user_id', None),
                session_id=getattr(request, 'session_id', None)
            )
            
            # Construir respuesta (mock)
            return self._build_proto_response(result)
        
        except Exception as e:
            logger.error(f"ProcessQuery error: {e}", exc_info=True)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return QueryResponse()
    
    async def GetStatus(self, request, context):
        """Obtener status del sistema."""
        return {
            "status": "healthy",
            "version": "1.0.0",
            "uptime_seconds": 0  # TODO: track uptime
        }
    
    async def HealthCheck(self, request, context):
        """Health check."""
        return {
            "healthy": True,
            "message": "HLCS is healthy"
        }
    
    def _build_proto_response(self, result: Dict[str, Any]):
        """Convertir dict a proto response (mock)."""
        # En producción, usar hlcs_pb2.QueryResponse()
        class MockResponse:
            def __init__(self, data):
                for k, v in data.items():
                    setattr(self, k, v)
        
        return MockResponse(result)


def serve():
    """
    Iniciar servidor gRPC.
    
    Nota: Versión simplificada. Para producción completa:
    1. Ejecutar `bash scripts/generate_proto.sh`
    2. Importar hlcs_pb2_grpc
    3. Registrar servicer con add_HLCSServicer_to_server()
    """
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from hlcs.mcp_client import SARAiMCPClient
    from hlcs.orchestrator import HLCSOrchestrator
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger.info("=" * 60)
    logger.info("HLCS gRPC Server Starting")
    logger.info("=" * 60)
    logger.info(f"Port: {GRPC_PORT}")
    logger.info(f"Workers: {MAX_WORKERS}")
    logger.info("=" * 60)
    
    logger.warning(
        "⚠️  Running with mock proto stubs. "
        "Run `bash scripts/generate_proto.sh` for full gRPC support."
    )
    
    # TODO: Implementar servidor gRPC real cuando tengamos stubs generados
    # Por ahora, solo logging
    
    logger.info("HLCS gRPC Server would start here...")
    logger.info(f"To implement: Install grpcio and generate proto stubs")
    logger.info(f"Then use: server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers={MAX_WORKERS}))")
    
    # Placeholder: mantener vivo
    try:
        import time
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        logger.info("Shutting down...")


if __name__ == "__main__":
    serve()
