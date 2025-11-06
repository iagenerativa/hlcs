"""
HLCS REST Gateway

FastAPI gateway que traduce REST → gRPC (o llama directamente al orchestrator).
Puerto: 4001
"""

import os
import logging
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

# Local imports
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hlcs.mcp_client import SARAiMCPClient
from hlcs.orchestrator import HLCSOrchestrator

logger = logging.getLogger(__name__)

# Configuration
REST_PORT = int(os.getenv("HLCS_REST_PORT", "4001"))
SARAI_MCP_URL = os.getenv("SARAI_MCP_URL", "http://localhost:3000")
COMPLEXITY_THRESHOLD = float(os.getenv("COMPLEXITY_THRESHOLD", "0.5"))
QUALITY_THRESHOLD = float(os.getenv("QUALITY_THRESHOLD", "0.7"))
MAX_ITERATIONS = int(os.getenv("MAX_ITERATIONS", "3"))


# ============================================================================
# Pydantic Models (Request/Response schemas)
# ============================================================================

class ProcessingOptions(BaseModel):
    """Opciones de procesamiento."""
    quality_threshold: Optional[float] = Field(None, ge=0.0, le=1.0)
    max_iterations: Optional[int] = Field(None, ge=1, le=10)
    timeout_seconds: Optional[int] = Field(None, ge=1, le=300)
    strategy: Optional[str] = None  # "simple", "complex", "multimodal"


class QueryRequest(BaseModel):
    """Request para /query endpoint."""
    query: str = Field(..., min_length=1, max_length=10000)
    image_url: Optional[str] = None
    audio_url: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    options: Optional[ProcessingOptions] = None


class QueryResponse(BaseModel):
    """Response de query processing."""
    result: str
    quality_score: float
    complexity: float
    strategy: str
    modality: str
    iterations: int
    processing_time_ms: int
    metadata: Dict[str, Any]
    errors: list[str] = []
    warnings: list[str] = []


class StatusResponse(BaseModel):
    """Response de /status."""
    status: str
    version: str
    sarai_connected: bool
    sarai_url: str


class CapabilityItem(BaseModel):
    """Capability individual."""
    name: str
    description: str
    available: bool


class CapabilitiesResponse(BaseModel):
    """Response de /capabilities."""
    capabilities: list[CapabilityItem]


# ============================================================================
# Application Lifecycle
# ============================================================================

sarai_client: Optional[SARAiMCPClient] = None
orchestrator: Optional[HLCSOrchestrator] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager."""
    global sarai_client, orchestrator
    
    logger.info("=" * 60)
    logger.info("HLCS REST Gateway Starting")
    logger.info("=" * 60)
    logger.info(f"Port: {REST_PORT}")
    logger.info(f"SARAi MCP URL: {SARAI_MCP_URL}")
    logger.info(f"Complexity Threshold: {COMPLEXITY_THRESHOLD}")
    logger.info(f"Quality Threshold: {QUALITY_THRESHOLD}")
    logger.info(f"Max Iterations: {MAX_ITERATIONS}")
    logger.info("=" * 60)
    
    # Initialize clients
    sarai_client = SARAiMCPClient(base_url=SARAI_MCP_URL)
    orchestrator = HLCSOrchestrator(
        sarai_client=sarai_client,
        complexity_threshold=COMPLEXITY_THRESHOLD,
        quality_threshold=QUALITY_THRESHOLD,
        max_iterations=MAX_ITERATIONS
    )
    
    # Check SARAi connectivity
    sarai_connected = await sarai_client.ping()
    if sarai_connected:
        logger.info("✅ SARAi MCP Server connected")
    else:
        logger.warning("⚠️  SARAi MCP Server not reachable (will retry on requests)")
    
    logger.info("HLCS REST Gateway ready!")
    
    yield
    
    # Cleanup
    logger.info("Shutting down HLCS REST Gateway...")
    await sarai_client.close()


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="HLCS - High-Level Consciousness System",
    description="Strategic orchestration API for SARAi AGI",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "HLCS",
        "version": "1.0.0",
        "status": "healthy",
        "endpoints": {
            "query": "POST /api/v1/query",
            "status": "GET /api/v1/status",
            "capabilities": "GET /api/v1/capabilities",
            "health": "GET /health"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    sarai_ok = await sarai_client.ping() if sarai_client else False
    
    return {
        "healthy": True,
        "sarai_connected": sarai_ok,
        "version": "1.0.0"
    }


@app.post("/api/v1/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """
    Procesar query con orquestación inteligente.
    
    Example:
        ```bash
        curl -X POST http://localhost:4001/api/v1/query \\
          -H "Content-Type: application/json" \\
          -d '{"query": "Explica agujeros negros"}'
        ```
    """
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    try:
        result = await orchestrator.process(
            query=request.query,
            image_url=request.image_url,
            audio_url=request.audio_url,
            context=request.context,
            user_id=request.user_id,
            session_id=request.session_id
        )
        
        return QueryResponse(**result)
    
    except Exception as e:
        logger.error(f"Query processing error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")


@app.get("/api/v1/status", response_model=StatusResponse)
async def get_status():
    """Obtener status del sistema."""
    sarai_connected = await sarai_client.ping() if sarai_client else False
    
    return StatusResponse(
        status="healthy" if sarai_connected else "degraded",
        version="1.0.0",
        sarai_connected=sarai_connected,
        sarai_url=SARAI_MCP_URL
    )


@app.get("/api/v1/capabilities", response_model=CapabilitiesResponse)
async def list_capabilities():
    """Listar capacidades disponibles."""
    # TODO: Obtener de SARAi dinámicamente
    capabilities = [
        CapabilityItem(
            name="simple_response",
            description="Respuestas rápidas via SAUL",
            available=True
        ),
        CapabilityItem(
            name="complex_research",
            description="Investigación profunda con RAG",
            available=True
        ),
        CapabilityItem(
            name="vision_analysis",
            description="Análisis de imágenes",
            available=False  # TODO: check SARAi
        ),
        CapabilityItem(
            name="audio_transcription",
            description="Transcripción de audio",
            available=False  # TODO: check SARAi
        ),
        CapabilityItem(
            name="iterative_refinement",
            description="Refinamiento iterativo de respuestas",
            available=True
        )
    ]
    
    return CapabilitiesResponse(capabilities=capabilities)


# ============================================================================
# Main
# ============================================================================

def serve():
    """Start REST server."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=REST_PORT,
        log_level="info",
        access_log=True
    )


if __name__ == "__main__":
    serve()
