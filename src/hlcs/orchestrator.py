"""
HLCS Orchestrator

Custom orchestrator sin frameworks pesados.
Implementa clasificación, routing, refinamiento iterativo.

NUEVO: Integración con Phi4MiniAGI para razonamiento avanzado.

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

# Try to import AGI system
try:
    from .agi_system import Phi4MiniAGI
    AGI_AVAILABLE = True
except ImportError:
    AGI_AVAILABLE = False
    logger.warning("AGI system not available (agi_system.py import failed)")

# Try to import Meta-Consciousness Layer
try:
    from .metacognition import MetaConsciousnessLayer, DecisionStrategy, create_meta_consciousness
    META_CONSCIOUSNESS_AVAILABLE = True
except ImportError:
    META_CONSCIOUSNESS_AVAILABLE = False
    logger.warning("Meta-Consciousness Layer not available (metacognition import failed)")

# Try to import Strategic Planning System
try:
    from .planning import StrategicPlanningSystem, create_strategic_planner
    STRATEGIC_PLANNING_AVAILABLE = True
except ImportError:
    STRATEGIC_PLANNING_AVAILABLE = False
    logger.warning("Strategic Planning System not available (planning import failed)")

# Try to import Multi-Stakeholder SCI
try:
    from .sci import MultiStakeholderSCI, create_multi_stakeholder_sci, StakeholderRole
    MULTI_STAKEHOLDER_AVAILABLE = True
except ImportError:
    MULTI_STAKEHOLDER_AVAILABLE = False
    logger.warning("Multi-Stakeholder SCI not available (sci import failed)")


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
        max_iterations: int = 3,
        agi_system: Optional['Phi4MiniAGI'] = None,
        enable_agi: bool = False,
        meta_consciousness: Optional['MetaConsciousnessLayer'] = None,
        enable_meta: bool = False,
        strategic_planner: Optional['StrategicPlanningSystem'] = None,
        enable_planning: bool = False,
        multi_stakeholder_sci: Optional['MultiStakeholderSCI'] = None,
        enable_sci: bool = False
    ):
        self.sarai = sarai_client
        self.complexity_threshold = complexity_threshold
        self.quality_threshold = quality_threshold
        self.max_iterations = max_iterations
        
        # AGI system integration
        self.agi_system = agi_system
        self.enable_agi = enable_agi and agi_system is not None
        
        # Meta-Consciousness Layer integration
        self.meta_consciousness = meta_consciousness
        self.enable_meta = enable_meta and meta_consciousness is not None
        
        # Strategic Planning System integration
        self.strategic_planner = strategic_planner
        self.enable_planning = enable_planning and strategic_planner is not None
        
        # Multi-Stakeholder SCI integration
        self.multi_stakeholder_sci = multi_stakeholder_sci
        self.enable_sci = enable_sci and multi_stakeholder_sci is not None
        
        if self.enable_agi:
            logger.info("AGI system enabled in orchestrator")
        if self.enable_meta:
            logger.info("Meta-Consciousness Layer enabled in orchestrator")
        if self.enable_planning:
            logger.info("Strategic Planning System enabled in orchestrator")
        if self.enable_sci:
            logger.info("Multi-Stakeholder SCI enabled in orchestrator")
        
        logger.info(
            f"HLCS Orchestrator initialized: "
            f"complexity={complexity_threshold}, quality={quality_threshold}, "
            f"max_iter={max_iterations}, agi={self.enable_agi}, "
            f"meta={self.enable_meta}, planning={self.enable_planning}, sci={self.enable_sci}"
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
            
            # 3. Meta-Cognitive Analysis (if enabled)
            meta_state = None
            if self.enable_meta:
                available_components = self._get_available_components()
                meta_state = self.meta_consciousness.analyze_query_context(
                    query=query,
                    context=context or {},
                    available_components=available_components
                )
                logger.info(
                    f"Meta-cognitive analysis: confidence={meta_state.self_doubt.get_composite_confidence():.2f}, "
                    f"ignorance_gaps={len(meta_state.ignorance_score.knowledge_gaps)}"
                )
            
            # 4. Intelligent Routing Decision (Meta-Consciousness + SCI)
            routing_decision = None
            if self.enable_meta and meta_state:
                available_components_dict = {
                    "sarai_mcp": {"available": True, "tools": ["saul", "vision", "audio", "rag", "trm"]},
                    "phi4mini_agi": {"available": self.enable_agi, "tools": ["rag", "code_agent", "memory"]}
                }
                
                routing_decision = self.meta_consciousness.decide_component_routing(
                    meta_state,
                    available_components_dict
                )
                
                # If SCI enabled, get consensus on routing
                if self.enable_sci and routing_decision.get("use_ensemble"):
                    routing_decision = await self._get_sci_consensus_routing(
                        routing_decision, state, user_id
                    )
                
                logger.info(f"Routing decision: {routing_decision['primary_component']}")
            
            # 5. Execute workflow based on routing decision
            if routing_decision and routing_decision["primary_component"] == "phi4mini_agi":
                logger.info("Meta-consciousness routed to AGI system")
                state = await self._agi_workflow(state, user_id, session_id, context)
            elif routing_decision and routing_decision["primary_component"] == "ensemble":
                logger.info("Meta-consciousness routed to ensemble workflow")
                state = await self._ensemble_workflow(state, user_id, session_id, context)
            # Traditional routing (backward compatible)
            elif self.enable_agi and self._should_use_agi(state):
                logger.info("Using AGI-enhanced workflow (traditional routing)")
                state = await self._agi_workflow(
                    state, user_id, session_id, context
                )
            elif state.modality == "multimodal":
                state = await self._multimodal_workflow(
                    state, image_url, audio_url, context
                )
            elif state.strategy == "complex":
                state = await self._complex_workflow(state, context)
            else:
                state = await self._simple_workflow(state, context)
            
            # 6. Meta-Cognitive Quality Evaluation
            if self.enable_meta:
                quality_score, quality_issues = self.meta_consciousness.evaluate_response_quality(
                    state.final_result,
                    expected_criteria=["coherent", "complete", "relevant"]
                )
                state.quality_score = quality_score
                if quality_issues:
                    state.warnings.extend(quality_issues)
                logger.info(f"Meta-cognitive quality score: {quality_score:.2f}")
            
            # 7. Refinar si necesario
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
    
    def _should_use_agi(self, state: HLCSState) -> bool:
        """
        Decide si usar el sistema AGI.
        
        Usa AGI cuando:
        - Complejidad muy alta (>0.7)
        - Query con keywords de código/implementación
        - No es multimodal (AGI es principalmente para texto)
        
        Returns:
            True si debe usar AGI
        """
        if not self.enable_agi:
            return False
        
        # No usar AGI para multimodal (usa workflows especializados)
        if state.modality == "multimodal":
            return False
        
        # Usar AGI para alta complejidad
        if state.complexity >= 0.7:
            return True
        
        # Usar AGI si query menciona código/implementación
        code_keywords = [
            "create", "implement", "build", "develop",
            "code", "script", "function", "class",
            "api", "endpoint", "database"
        ]
        query_lower = state.query.lower()
        if any(kw in query_lower for kw in code_keywords):
            return True
        
        return False
    
    async def _agi_workflow(
        self,
        state: HLCSState,
        user_id: Optional[str],
        session_id: Optional[str],
        context: Optional[Dict]
    ) -> HLCSState:
        """
        Workflow usando sistema AGI completo.
        
        Delega el procesamiento al Phi4MiniAGI system que:
        - Decide automáticamente estrategia (simple/complex)
        - Usa RAG + LLM o agente con tools
        - Maneja memoria episódica
        
        Args:
            state: Estado actual
            user_id: ID de usuario
            session_id: ID de sesión
            context: Contexto adicional
        
        Returns:
            Estado actualizado con respuesta del AGI
        """
        logger.info("Executing AGI-enhanced workflow")
        state.strategy = "agi_enhanced"
        
        try:
            # Llamar al sistema AGI
            agi_result = await self.agi_system.process(
                query=state.query,
                user_id=user_id,
                session_id=session_id,
                force_strategy=None  # Dejar que AGI decida
            )
            
            # Track tool call
            state.tool_calls.append({
                "tool_name": "agi_system.process",
                "latency_ms": agi_result.get("latency_ms", 0),
                "success": agi_result["status"] == "success",
                "strategy": agi_result.get("strategy")
            })
            
            if agi_result["status"] == "success":
                state.final_result = agi_result["answer"]
                # AGI system ya decide calidad basado en estrategia usada
                if agi_result.get("strategy") == "complex":
                    state.quality_score = 0.9  # Alta calidad por agente
                else:
                    state.quality_score = 0.8  # Buena calidad por RAG+LLM
                
                # Actualizar stats si disponibles
                if "stats" in agi_result:
                    state.metadata["agi_stats"] = agi_result["stats"]
                
                logger.info(
                    f"AGI workflow completed: strategy={agi_result.get('strategy')}, "
                    f"quality={state.quality_score}"
                )
            else:
                # AGI falló, fallback a workflow simple
                error_msg = agi_result.get("error_details", "Unknown AGI error")
                state.warnings.append(f"AGI processing failed: {error_msg}")
                logger.warning(f"AGI workflow failed, falling back to simple: {error_msg}")
                return await self._simple_workflow(state, context)
        
        except Exception as e:
            logger.error(f"AGI workflow exception: {e}", exc_info=True)
            state.errors.append(f"AGI workflow error: {str(e)}")
            # Fallback a workflow simple
            return await self._simple_workflow(state, context)
        
        return "\n".join(parts)
    
    def _get_available_components(self) -> List[str]:
        """Get list of available components for meta-cognitive analysis."""
        components = ["saul.respond", "saul.synthesize", "rag.search", "trm.classify"]
        
        if self.enable_agi:
            components.extend(["phi4mini_agi", "code_agent"])
        
        # Check if multimodal tools are available (assuming they are via SARAi)
        components.extend(["vision.analyze", "audio.transcribe"])
        
        return components
    
    async def _get_sci_consensus_routing(
        self,
        routing_decision: Dict[str, Any],
        state: HLCSState,
        user_id: Optional[str]
    ) -> Dict[str, Any]:
        """
        Get consensus from Multi-Stakeholder SCI on routing decision.
        
        Args:
            routing_decision: Initial routing decision from meta-consciousness
            state: Current processing state
            user_id: User ID (becomes primary stakeholder)
            
        Returns:
            Consensus-approved routing decision
        """
        if not self.enable_sci:
            return routing_decision
        
        try:
            # Create decision in SCI
            decision = self.multi_stakeholder_sci.create_decision(
                title=f"Route query: {state.query[:50]}...",
                description=f"Meta-consciousness recommends: {routing_decision['primary_component']}",
                decision_type="component_routing",
                criticality=state.complexity,
                recommended_option=routing_decision["primary_component"],
                required_roles=[StakeholderRole.PRIMARY_USER, StakeholderRole.AUTONOMOUS_AGENT]
            )
            
            # If user_id provided, cast their vote (assume approve recommendation)
            if user_id and user_id in self.multi_stakeholder_sci.stakeholders:
                from .sci import VoteChoice
                self.multi_stakeholder_sci.cast_vote(
                    stakeholder_id=user_id,
                    decision_id=decision.decision_id,
                    choice=VoteChoice.APPROVE,
                    rationale="User implicit approval"
                )
            
            # Reach consensus
            consensus_reached, rationale = self.multi_stakeholder_sci.reach_consensus(
                decision.decision_id,
                wait_for_all=False
            )
            
            if consensus_reached:
                logger.info(f"SCI consensus approved routing: {rationale}")
            else:
                logger.warning(f"SCI consensus rejected, using fallback: {rationale}")
                # Fallback to SARAi MCP (safest option)
                routing_decision["primary_component"] = "sarai_mcp"
            
        except Exception as e:
            logger.error(f"SCI consensus error: {e}")
            # Keep original routing decision
        
        return routing_decision
    
    async def _ensemble_workflow(
        self,
        state: HLCSState,
        user_id: Optional[str],
        session_id: Optional[str],
        context: Optional[Dict]
    ) -> HLCSState:
        """
        Ensemble workflow that combines multiple approaches.
        
        Executes both AGI and SARAi workflows, then combines results.
        
        Args:
            state: Current processing state
            user_id: User ID
            session_id: Session ID
            context: Additional context
            
        Returns:
            State with ensemble result
        """
        logger.info("Executing ensemble workflow (AGI + SARAi)")
        state.strategy = "ensemble"
        
        results = []
        
        # Execute AGI workflow if available
        if self.enable_agi:
            try:
                agi_result = await self.agi_system.process(
                    query=state.query,
                    user_id=user_id,
                    session_id=session_id
                )
                if agi_result["status"] == "success":
                    results.append({
                        "source": "agi",
                        "answer": agi_result["answer"],
                        "confidence": 0.85
                    })
                    state.tool_calls.append({
                        "tool_name": "agi_system.process",
                        "latency_ms": agi_result.get("latency_ms", 0),
                        "success": True
                    })
            except Exception as e:
                logger.warning(f"AGI ensemble component failed: {e}")
        
        # Execute SARAi workflow
        try:
            if state.complexity > self.complexity_threshold:
                sarai_state = await self._complex_workflow(state, context)
            else:
                sarai_state = await self._simple_workflow(state, context)
            
            if sarai_state.final_result:
                results.append({
                    "source": "sarai",
                    "answer": sarai_state.final_result,
                    "confidence": 0.80
                })
        except Exception as e:
            logger.warning(f"SARAi ensemble component failed: {e}")
        
        # Combine results
        if len(results) >= 2:
            # Use SAUL to synthesize ensemble results
            synthesis_result = await self.sarai.call_tool("saul.synthesize", {
                "sources": results,
                "query": state.query
            })
            
            if synthesis_result.success:
                state.final_result = synthesis_result.result.get("synthesis", "")
                state.quality_score = 0.95  # Ensemble = high quality
                state.tool_calls.append({
                    "tool_name": "saul.synthesize",
                    "latency_ms": synthesis_result.latency_ms,
                    "success": True
                })
            else:
                # Fallback: use highest confidence result
                best_result = max(results, key=lambda r: r["confidence"])
                state.final_result = best_result["answer"]
                state.quality_score = best_result["confidence"]
        elif len(results) == 1:
            # Only one result available
            state.final_result = results[0]["answer"]
            state.quality_score = results[0]["confidence"]
        else:
            # No results, fallback
            state.errors.append("Ensemble workflow produced no results")
            return await self._simple_workflow(state, context)
        
        logger.info(f"Ensemble workflow completed with {len(results)} sources")
        return state
    
    def _build_response(self, state: HLCSState) -> Dict[str, Any]:
        """Construir respuesta compatible con proto."""
        response = {
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
        
        # Add meta-cognitive statistics if available
        if self.enable_meta:
            response["metadata"]["meta_statistics"] = self.meta_consciousness.get_meta_statistics()
        
        return response
