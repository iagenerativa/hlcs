"""
Mock SARAi MCP Server para testing.

Simula el comportamiento del SARAi MCP Server para pruebas E2E de HLCS.
"""

import asyncio
import logging
from typing import Dict, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Mock SARAi MCP Server", version="1.0.0")


# ============================================================================
# Request Models
# ============================================================================

class SAULRequest(BaseModel):
    query: str
    context: Dict[str, Any] = {}


class TRMRequest(BaseModel):
    query: str
    context: Dict[str, Any] = {}


class RAGRequest(BaseModel):
    query: str
    k: int = 5


class LLMChatRequest(BaseModel):
    messages: list
    temperature: float = 0.3


class VisionRequest(BaseModel):
    image_url: str


class AudioRequest(BaseModel):
    audio_url: str


# ============================================================================
# Mock Endpoints
# ============================================================================

@app.get("/")
async def root():
    return {"service": "Mock SARAi MCP Server", "status": "healthy"}


@app.get("/health")
async def health():
    return {"status": "healthy", "version": "1.0.0"}


@app.get("/tools")
async def list_tools():
    return {
        "tools": [
            {"name": "saul.respond", "category": "chat"},
            {"name": "trm.classify", "category": "classification"},
            {"name": "rag.search", "category": "retrieval"},
            {"name": "llm.chat", "category": "generation"},
            {"name": "vision.analyze", "category": "multimodal"},
            {"name": "audio.transcribe", "category": "multimodal"}
        ]
    }


@app.post("/api/saul/respond")
async def saul_respond(request: SAULRequest):
    """Mock SAUL responses."""
    query = request.query.lower()
    
    # Simulate different responses based on query
    if "hola" in query or "hello" in query:
        return {"text": "¡Hola! ¿En qué puedo ayudarte hoy?"}
    elif "gracias" in query:
        return {"text": "¡De nada! Estoy aquí para ayudarte."}
    elif "adiós" in query or "bye" in query:
        return {"text": "¡Hasta luego! Que tengas un buen día."}
    else:
        return {"text": f"Entiendo que preguntaste: '{request.query}'. ¿Cómo puedo ayudarte?"}


@app.post("/api/trm/classify")
async def trm_classify(request: TRMRequest):
    """Mock TRM complexity classification."""
    query = request.query.lower()
    
    # Simple heuristic
    if len(query) < 20:
        complexity = 0.2
    elif "explica" in query or "cómo" in query or "qué es" in query:
        complexity = 0.8
    elif "imagen" in query or "audio" in query or "analiza" in query:
        complexity = 0.9
    else:
        complexity = 0.5
    
    logger.info(f"TRM Classify: '{query}' → complexity={complexity}")
    
    return {
        "complexity": complexity,
        "category": "complex" if complexity > 0.6 else "simple",
        "confidence": 0.85
    }


@app.post("/api/rag/search")
async def rag_search(request: RAGRequest):
    """Mock RAG search."""
    # Simulate research results
    await asyncio.sleep(0.1)  # Simulate search latency
    
    logger.info(f"RAG Search: '{request.query}' (k={request.k})")
    
    results = [
        {
            "text": f"Información relevante sobre '{request.query}': Los agujeros negros son regiones del espacio-tiempo donde la gravedad es tan fuerte que nada puede escapar.",
            "source": "wikipedia.org",
            "score": 0.92
        },
        {
            "text": "Un agujero negro se forma cuando una estrella masiva colapsa al final de su vida.",
            "source": "nasa.gov",
            "score": 0.88
        },
        {
            "text": "El horizonte de eventos es el límite a partir del cual nada puede escapar de un agujero negro.",
            "source": "arxiv.org",
            "score": 0.85
        }
    ]
    
    return {
        "results": results[:request.k],
        "total": len(results),
        "query_time_ms": 100
    }


@app.post("/api/llm/chat")
async def llm_chat(request: LLMChatRequest):
    """Mock LLM chat/synthesis."""
    await asyncio.sleep(0.2)  # Simulate LLM inference
    
    # Extract user message
    user_messages = [m["content"] for m in request.messages if m.get("role") == "user"]
    last_user_msg = user_messages[-1] if user_messages else ""
    
    logger.info(f"LLM Chat: {len(request.messages)} messages, temp={request.temperature}")
    
    # Check if it's evaluation or synthesis
    if "evalúa" in last_user_msg.lower() or '"score"' in last_user_msg:
        # Quality evaluation response
        return {
            "text": '{"score": 0.75, "issues": ["podría ser más detallado"]}'
        }
    else:
        # Synthesis response
        if "agujero" in last_user_msg.lower() or "black hole" in last_user_msg.lower():
            return {
                "text": "Los agujeros negros son regiones del espacio-tiempo donde la gravedad es tan intensa que nada, ni siquiera la luz, puede escapar de ellos. Se forman cuando estrellas masivas colapsan al final de su ciclo de vida."
            }
        else:
            return {
                "text": f"Basándome en la información proporcionada, puedo decir que {last_user_msg[:50]}... [respuesta sintetizada por el modelo]"
            }


@app.post("/api/vision/analyze")
async def vision_analyze(request: VisionRequest):
    """Mock vision analysis."""
    await asyncio.sleep(0.15)  # Simulate inference
    
    logger.info(f"Vision Analyze: {request.image_url}")
    
    # Mock response based on URL
    if "cat" in request.image_url.lower():
        description = "La imagen muestra un gato naranja descansando en un sofá"
    elif "dog" in request.image_url.lower():
        description = "Un perro labrador dorado jugando en un parque"
    else:
        description = "Imagen analizada: se observan varios objetos y elementos visuales"
    
    return {
        "description": description,
        "objects": ["cat", "sofa"],
        "confidence": 0.91
    }


@app.post("/api/audio/transcribe")
async def audio_transcribe(request: AudioRequest):
    """Mock audio transcription."""
    await asyncio.sleep(0.1)
    
    logger.info(f"Audio Transcribe: {request.audio_url}")
    
    return {
        "text": "Hola, esto es una transcripción de prueba del audio proporcionado.",
        "language": "es",
        "confidence": 0.94
    }


# ============================================================================
# Main
# ============================================================================

def run_mock_server(port: int = 3000):
    """Run mock SARAi server."""
    logger.info("=" * 60)
    logger.info("Mock SARAi MCP Server Starting")
    logger.info("=" * 60)
    logger.info(f"Port: {port}")
    logger.info("Endpoints:")
    logger.info("  GET  /health")
    logger.info("  POST /api/saul/respond")
    logger.info("  POST /api/trm/classify")
    logger.info("  POST /api/rag/search")
    logger.info("  POST /api/llm/chat")
    logger.info("  POST /api/vision/analyze")
    logger.info("  POST /api/audio/transcribe")
    logger.info("=" * 60)
    
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")


if __name__ == "__main__":
    run_mock_server()
