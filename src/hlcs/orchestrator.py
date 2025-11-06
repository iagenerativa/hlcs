"""
HLCS Orchestrator

Custom orchestrator sin frameworks pesados.
Implementa clasificación, routing, refinamiento iterativo.

Total: ~280 LOC de código limpio.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json

from .mcp_client import SARAiMCPClient

logger = logging.getLogger(__name__)


@dataclass
class HLCSState:
    """Estado del workflow de procesamiento."""
    query: str
    complexity: float = 0.0
    strategy: str = "unknown"
    has_image: bool = False
    has_audio: bool = False
    modality: str = "text"
    
    # Resultados intermedios
    research_results: Optional[Dict[str, Any]] = None
    vision_results: Optional[Dict[str, Any]] = None
    audio_results: Optional[Dict[str, Any]] = None
    
    # Resultado final
    final_result: str = ""
    quality_score: float = 0.0
    
    # Metadata
    iterations: int = 0
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    
    @property
    def processing_time_ms(self) -> int:
        """Tiempo de procesamiento en milisegundos."""
        if self.end_time:
            return int((self.end_time - self.start_time).total_seconds() * 1000)
        return 0


class HLCSOrchestrator:
    """
    Orquestador estratégico de alto nivel.
    
    Flujo:
    1. Clasificar complejidad
    2. Detectar modalidad
    3. Ejecutar workflow apropiado
    4. Refinar hasta calidad objetivo
    5. Retornar resultado
    
    Example:
        >>> async with SARAiMCPClient() as sarai:
        ...     orchestrator = HLCSOrchestrator(sarai)
        ...     result = await orchestrator.process("Explica agujeros negros")
        ...     print(result["result"])
    """
    
    def __init__(
        self,
        sarai_client: SARAiMCPClient,
        complexity_threshold: float = 0.5,
        quality_threshold: float = 0.7,
        max_iterations: int = 3
    ):
        self.sarai = sarai_client
        self.complexity_threshold = complexity_threshold
        self.quality_threshold = quality_threshold
        self.max_iterations = max_iterations
        
        logger.info(
            f"HLCS Orchestrator initialized: "
            f"complexity={complexity_threshold}, quality={quality_threshold}, "
            f"max_iter={max_iterations}"
        )
    
    async def process(
        self,
        query: str,
        image_url: Optional[str] = None,
        audio_url: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Procesar query con orquestación inteligente.
        
        Returns:
            Dict compatible con QueryResponse proto
        """
        state = HLCSState(
            query=query,
            has_image=image_url is not None,
            has_audio=audio_url is not None
        )
        
        logger.info(
            f"Processing query (user={user_id}, session={session_id}): "
            f"{query[:50]}... [image={state.has_image}, audio={state.has_audio}]"
        )
        
        try:
            # 1. Clasificar complejidad
            state = await self._classify_complexity(state, context)
            
            # 2. Detectar modalidad
            state = self._detect_modality(state)
            
            # 3. Ejecutar workflow
            if state.modality == "multimodal":
                state = await self._multimodal_workflow(
                    state, image_url, audio_url, context
                )
            elif state.strategy == "complex":
                state = await self._complex_workflow(state, context)
            else:
                state = await self._simple_workflow(state, context)
            
            # 4. Refinar si necesario
            if state.quality_score < self.quality_threshold:
                state = await self._refinement_loop(state, context)
            
        except Exception as e:
            logger.error(f"Processing failed: {e}", exc_info=True)
            state.errors.append(f"Processing error: {str(e)}")
            state.final_result = "Lo siento, hubo un error procesando tu solicitud."
            state.quality_score = 0.0
        
        # 5. Finalizar
        state.end_time = datetime.now()
        
        return self._build_response(state)
    
    async def _classify_complexity(
        self,
        state: HLCSState,
        context: Optional[Dict]
    ) -> HLCSState:
        """Clasificar complejidad usando SARAi TRM."""
        try:
            result = await self.sarai.call_tool("trm.classify", {
                "query": state.query,
                "context": context or {}
            })
            
            if result.success:
                state.complexity = result.result.get("complexity", 0.5)
                state.strategy = (
                    "complex" if state.complexity > self.complexity_threshold
                    else "simple"
                )
                state.tool_calls.append({
                    "tool_name": "trm.classify",
                    "latency_ms": result.latency_ms,
                    "success": True
                })
                logger.info(f"Complexity: {state.complexity:.2f} → {state.strategy}")
            else:
                state.warnings.append(f"TRM classify failed: {result.error}")
                state.complexity = 0.5
                state.strategy = "simple"
        
        except Exception as e:
            logger.warning(f"Complexity classification error: {e}")
            state.warnings.append(f"Complexity classification error: {str(e)}")
            state.complexity = 0.5
            state.strategy = "simple"
        
        return state
    
    def _detect_modality(self, state: HLCSState) -> HLCSState:
        """Detectar modalidad."""
        if state.has_image or state.has_audio:
            state.modality = "multimodal"
        else:
            state.modality = "text"
        return state
    
    async def _simple_workflow(
        self,
        state: HLCSState,
        context: Optional[Dict]
    ) -> HLCSState:
        """Workflow simple: SAUL directo."""
        logger.info("Executing SIMPLE workflow (SAUL)")
        
        result = await self.sarai.call_tool("saul.respond", {
            "query": state.query,
            "context": context or {}
        })
        
        state.tool_calls.append({
            "tool_name": "saul.respond",
            "latency_ms": result.latency_ms,
            "success": result.success,
            "error": result.error
        })
        
        if result.success:
            state.final_result = result.result.get("text", "")
            state.quality_score = 0.75  # SAUL baseline
        else:
            state.errors.append(f"SAUL failed: {result.error}")
            state.final_result = "Lo siento, no pude procesar tu solicitud."
            state.quality_score = 0.0
        
        return state
    
    async def _complex_workflow(
        self,
        state: HLCSState,
        context: Optional[Dict]
    ) -> HLCSState:
        """Workflow complejo: RAG → Synthesis."""
        logger.info("Executing COMPLEX workflow (RAG + Synthesis)")
        
        # Step 1: RAG search
        rag_result = await self.sarai.call_tool("rag.search", {
            "query": state.query,
            "k": 5
        })
        
        state.tool_calls.append({
            "tool_name": "rag.search",
            "latency_ms": rag_result.latency_ms,
            "success": rag_result.success,
            "error": rag_result.error
        })
        
        if rag_result.success:
            state.research_results = rag_result.result
        else:
            state.warnings.append(f"RAG search failed: {rag_result.error}")
        
        # Step 2: Synthesis
        synthesis_prompt = self._build_synthesis_prompt(
            state.query,
            state.research_results,
            context
        )
        
        llm_result = await self.sarai.call_tool("llm.chat", {
            "messages": [
                {"role": "system", "content": "Eres un sintetizador experto."},
                {"role": "user", "content": synthesis_prompt}
            ],
            "temperature": 0.3
        })
        
        state.tool_calls.append({
            "tool_name": "llm.chat",
            "latency_ms": llm_result.latency_ms,
            "success": llm_result.success,
            "error": llm_result.error
        })
        
        if llm_result.success:
            state.final_result = llm_result.result.get("text", "")
            state.quality_score = 0.7  # Initial, puede refinarse
        else:
            # Fallback a SAUL
            state.warnings.append(f"LLM synthesis failed: {llm_result.error}")
            return await self._simple_workflow(state, context)
        
        return state
    
    async def _multimodal_workflow(
        self,
        state: HLCSState,
        image_url: Optional[str],
        audio_url: Optional[str],
        context: Optional[Dict]
    ) -> HLCSState:
        """Workflow multimodal: Vision/Audio → Research → Synthesis."""
        logger.info("Executing MULTIMODAL workflow")
        
        tasks = []
        
        # Vision
        if state.has_image and image_url:
            tasks.append(self._analyze_vision(image_url, state))
        
        # Audio
        if state.has_audio and audio_url:
            tasks.append(self._transcribe_audio(audio_url, state))
        
        # Ejecutar en paralelo
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combinar resultados
        vision_text = ""
        audio_text = ""
        
        if state.vision_results:
            vision_text = state.vision_results.get("description", "")
        
        if state.audio_results:
            audio_text = state.audio_results.get("text", "")
        
        combined_query = f"{state.query}\n\nImagen: {vision_text}\nAudio: {audio_text}"
        
        # RAG opcional si complejo
        if state.complexity > 0.6:
            rag_result = await self.sarai.call_tool("rag.search", {
                "query": combined_query,
                "k": 3
            })
            
            state.tool_calls.append({
                "tool_name": "rag.search",
                "latency_ms": rag_result.latency_ms,
                "success": rag_result.success
            })
            
            if rag_result.success:
                state.research_results = rag_result.result
        
        # Síntesis final
        synthesis_prompt = self._build_synthesis_prompt(
            combined_query,
            state.research_results,
            context
        )
        
        llm_result = await self.sarai.call_tool("llm.chat", {
            "messages": [
                {"role": "system", "content": "Eres un asistente multimodal experto."},
                {"role": "user", "content": synthesis_prompt}
            ],
            "temperature": 0.3
        })
        
        state.tool_calls.append({
            "tool_name": "llm.chat",
            "latency_ms": llm_result.latency_ms,
            "success": llm_result.success
        })
        
        if llm_result.success:
            state.final_result = llm_result.result.get("text", "")
            state.quality_score = 0.75
        else:
            state.final_result = "Error procesando contenido multimodal."
            state.quality_score = 0.0
        
        return state
    
    async def _analyze_vision(self, image_url: str, state: HLCSState):
        """Analizar imagen."""
        result = await self.sarai.call_tool("vision.analyze", {
            "image_url": image_url
        })
        
        state.tool_calls.append({
            "tool_name": "vision.analyze",
            "latency_ms": result.latency_ms,
            "success": result.success
        })
        
        if result.success:
            state.vision_results = result.result
    
    async def _transcribe_audio(self, audio_url: str, state: HLCSState):
        """Transcribir audio."""
        result = await self.sarai.call_tool("audio.transcribe", {
            "audio_url": audio_url
        })
        
        state.tool_calls.append({
            "tool_name": "audio.transcribe",
            "latency_ms": result.latency_ms,
            "success": result.success
        })
        
        if result.success:
            state.audio_results = result.result
    
    async def _refinement_loop(
        self,
        state: HLCSState,
        context: Optional[Dict]
    ) -> HLCSState:
        """Loop de refinamiento iterativo."""
        while (
            state.quality_score < self.quality_threshold
            and state.iterations < self.max_iterations
        ):
            state.iterations += 1
            logger.info(f"Refinement iteration {state.iterations}/{self.max_iterations}")
            
            try:
                # Evaluar calidad
                eval_result = await self._evaluate_quality(
                    state.final_result,
                    state.query
                )
                
                if eval_result["score"] >= self.quality_threshold:
                    state.quality_score = eval_result["score"]
                    break
                
                # Refinar
                refined = await self._refine_response(
                    state.final_result,
                    state.query,
                    eval_result.get("issues", [])
                )
                
                if refined.success:
                    state.final_result = refined.result.get("text", state.final_result)
                    state.quality_score = min(eval_result["score"] + 0.15, 1.0)
                else:
                    break
            
            except Exception as e:
                logger.warning(f"Refinement iteration {state.iterations} failed: {e}")
                break
        
        logger.info(
            f"Refinement complete: quality={state.quality_score:.2f}, "
            f"iterations={state.iterations}"
        )
        return state
    
    async def _evaluate_quality(
        self,
        response: str,
        original_query: str
    ) -> Dict[str, Any]:
        """Evaluar calidad (LLM-as-judge)."""
        eval_prompt = f"""Evalúa esta respuesta (0.0-1.0):

Query: {original_query}
Respuesta: {response}

Devuelve JSON: {{"score": 0.85, "issues": ["issue1"]}}
"""
        
        try:
            result = await self.sarai.call_tool("llm.chat", {
                "messages": [{"role": "user", "content": eval_prompt}],
                "temperature": 0.1
            })
            
            if result.success:
                quality_data = json.loads(result.result.get("text", "{}"))
                return quality_data
        except Exception as e:
            logger.warning(f"Quality evaluation failed: {e}")
        
        return {"score": 0.7, "issues": []}
    
    async def _refine_response(
        self,
        response: str,
        original_query: str,
        issues: List[str]
    ):
        """Refinar respuesta."""
        refinement_prompt = f"""Mejora esta respuesta:

Query: {original_query}
Respuesta actual: {response}
Problemas: {', '.join(issues)}

Genera versión mejorada.
"""
        
        return await self.sarai.call_tool("llm.chat", {
            "messages": [{"role": "user", "content": refinement_prompt}],
            "temperature": 0.3
        })
    
    def _build_synthesis_prompt(
        self,
        query: str,
        research: Optional[Dict],
        context: Optional[Dict]
    ) -> str:
        """Construir prompt de síntesis."""
        parts = [f"Query: {query}"]
        
        if research and research.get("results"):
            results_text = "\n".join([
                f"- {r.get('text', '')[:200]}"
                for r in research["results"][:5]
            ])
            parts.append(f"\nInformación:\n{results_text}")
        
        if context:
            parts.append(f"\nContexto: {context}")
        
        parts.append("\nGenera respuesta completa y precisa.")
        
        return "\n".join(parts)
    
    def _build_response(self, state: HLCSState) -> Dict[str, Any]:
        """Construir respuesta compatible con proto."""
        return {
            "result": state.final_result,
            "quality_score": state.quality_score,
            "complexity": state.complexity,
            "strategy": state.strategy,
            "modality": state.modality,
            "iterations": state.iterations,
            "processing_time_ms": state.processing_time_ms,
            "metadata": {
                "has_image": state.has_image,
                "has_audio": state.has_audio,
                "research_done": state.research_results is not None,
                "vision_done": state.vision_results is not None,
                "audio_done": state.audio_results is not None,
                "tool_calls": state.tool_calls
            },
            "errors": state.errors,
            "warnings": state.warnings
        }
