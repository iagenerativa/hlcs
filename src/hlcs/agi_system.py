"""
Phi-4-Mini AGI System para HLCS

Sistema AGI completo que integra:
- Motor lógico (Phi-4-mini vía llama-cpp)
- Memoria externa (RAG)
- Agente con tools (CodeAgent)
- Memoria episódica (MemoryBuffer)

Decide automáticamente entre razonamiento simple (LLM directo + RAG)
o complejo (agente multi-step con tools).

Version: 1.0.0
Inspired by: Production-ready AGI patterns
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
import asyncio

# Import local modules
from .memory.episodic_memory import MemoryBuffer
from .memory.rag import KnowledgeRAG
from .planning.agentes import CodeAgent

logger = logging.getLogger(__name__)


# Try to import llama-cpp-python, fallback gracefully
try:
    from llama_cpp import Llama
    LLAMA_CPP_AVAILABLE = True
except ImportError:
    logger.warning("llama-cpp-python not installed, AGI system will run in mock mode")
    LLAMA_CPP_AVAILABLE = False
    # Mock Llama class
    class Llama:
        def __init__(self, *args, **kwargs):
            logger.warning("Using mock Llama (llama-cpp-python not installed)")
        
        def __call__(self, prompt: str, **kwargs) -> Dict[str, Any]:
            return {
                "choices": [{
                    "text": f"[MOCK RESPONSE] This would be Phi-4-mini response to: {prompt[:100]}..."
                }]
            }


@dataclass
class AGIStats:
    """Estadísticas del sistema AGI."""
    total_calls: int = 0
    simple_calls: int = 0  # LLM directo + RAG
    complex_calls: int = 0  # Agente multi-step
    tool_uses: int = 0
    errors: int = 0
    total_latency_ms: float = 0.0
    
    @property
    def avg_latency_ms(self) -> float:
        """Latencia promedio."""
        return self.total_latency_ms / max(self.total_calls, 1)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a dict."""
        return {
            "total_calls": self.total_calls,
            "simple_calls": self.simple_calls,
            "complex_calls": self.complex_calls,
            "tool_uses": self.tool_uses,
            "errors": self.errors,
            "avg_latency_ms": round(self.avg_latency_ms, 2)
        }


class Phi4MiniAGI:
    """
    Sistema AGI basado en Phi-4-mini con RAG, agentes y memoria.
    
    Este sistema actúa como un AGI-like que decide automáticamente
    la estrategia óptima basándose en la complejidad del query.
    
    Estrategias:
    1. Simple: Query directo → RAG context → LLM → Response (~300ms)
    2. Complex: Query → Agente ReAct → Tools → LLM → Response (~8s)
    
    Example:
        >>> agi = Phi4MiniAGI(
        ...     model_path="./phi4_mini_q4.gguf",
        ...     rag_docs="./codebase.py",
        ...     memory_path="./data/memory.json"
        ... )
        >>> 
        >>> # Simple query
        >>> result = await agi.process("¿Qué es HLCS?")
        >>> # → Uses RAG + LLM direct (fast)
        >>> 
        >>> # Complex query
        >>> result = await agi.process("Create API endpoint with JWT auth and logging")
        >>> # → Uses agent with tools (slower but capable)
    """
    
    def __init__(
        self,
        model_path: str,
        rag_docs: Optional[str] = None,
        memory_path: Optional[str] = None,
        memory_max_size: int = 1000,
        n_ctx: int = 4096,
        n_gpu_layers: int = -1,
        complexity_keywords: Optional[List[str]] = None
    ):
        """
        Inicializa el sistema AGI.
        
        Args:
            model_path: Path al modelo GGUF (Phi-4-mini)
            rag_docs: Path a documentos para RAG
            memory_path: Path para persistir memoria episódica
            memory_max_size: Tamaño máximo del buffer de memoria
            n_ctx: Tamaño del contexto del modelo
            n_gpu_layers: Capas en GPU (-1 = todas)
            complexity_keywords: Keywords para detectar queries complejos
        """
        self.model_path = model_path
        self.n_ctx = n_ctx
        
        # 1. Motor lógico (Phi-4-mini)
        if LLAMA_CPP_AVAILABLE:
            logger.info(f"Loading Phi-4-mini from {model_path}...")
            self.llm = Llama(
                model_path=model_path,
                n_ctx=n_ctx,
                n_gpu_layers=n_gpu_layers,
                n_threads=4,
                verbose=False
            )
            logger.info("✅ Phi-4-mini loaded successfully")
        else:
            logger.warning("Using mock LLM (llama-cpp-python not available)")
            self.llm = Llama()
        
        # 2. Memoria externa (RAG)
        if rag_docs:
            logger.info(f"Initializing RAG with docs: {rag_docs}")
            self.rag = KnowledgeRAG(rag_docs)
            logger.info(f"✅ RAG initialized with {len(self.rag.docs)} chunks")
        else:
            logger.warning("No RAG docs provided, RAG disabled")
            self.rag = None
        
        # 3. Agente (planning)
        logger.info("Initializing CodeAgent...")
        self.agent = CodeAgent(self.llm, self.rag)
        logger.info("✅ CodeAgent initialized")
        
        # 4. Memoria episódica
        logger.info(f"Initializing memory buffer (max_size={memory_max_size})...")
        self.memory = MemoryBuffer(
            max_size=memory_max_size,
            persist_path=memory_path,
            auto_save=True
        )
        logger.info(f"✅ Memory buffer initialized ({len(self.memory)} episodes)")
        
        # 5. Keywords para detectar complejidad
        self.complexity_keywords = complexity_keywords or [
            "create", "implement", "build", "develop",
            "using", "and then", "step by step",
            "search for", "find and", "execute",
            "generate code", "write a script"
        ]
        
        # 6. Estado del sistema
        self.stats = AGIStats()
        
        logger.info("✅ Phi4MiniAGI system initialized successfully")
    
    async def process(
        self,
        query: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        force_strategy: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Procesa un query con el sistema AGI.
        
        Este es el endpoint principal. Decide automáticamente
        entre estrategia simple o compleja.
        
        Args:
            query: Query del usuario
            user_id: ID de usuario (para memoria)
            session_id: ID de sesión (para memoria)
            force_strategy: Forzar estrategia ("simple" o "complex")
        
        Returns:
            Dict con:
                - answer: Respuesta generada
                - strategy: Estrategia usada
                - status: "success" o "error"
                - latency_ms: Latencia en milisegundos
                - stats: Estadísticas del sistema
        """
        start_time = datetime.now()
        self.stats.total_calls += 1
        
        try:
            # Decidir estrategia
            if force_strategy:
                needs_complex = force_strategy == "complex"
            else:
                needs_complex = self._needs_complex_reasoning(query)
            
            # Ejecutar estrategia apropiada
            if needs_complex:
                logger.info(f"Using COMPLEX strategy for: {query[:60]}...")
                answer = await self._complex_strategy(query)
                self.stats.complex_calls += 1
                strategy = "complex"
            else:
                logger.info(f"Using SIMPLE strategy for: {query[:60]}...")
                answer = await self._simple_strategy(query)
                self.stats.simple_calls += 1
                strategy = "simple"
            
            # Guardar en memoria episódica
            self.memory.add(
                query=query,
                answer=answer,
                session_id=session_id,
                user_id=user_id,
                metadata={
                    "strategy": strategy,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            # Calcular latencia
            end_time = datetime.now()
            latency_ms = (end_time - start_time).total_seconds() * 1000
            self.stats.total_latency_ms += latency_ms
            
            return {
                "answer": answer,
                "strategy": strategy,
                "status": "success",
                "latency_ms": round(latency_ms, 2),
                "stats": self.stats.to_dict()
            }
        
        except Exception as e:
            self.stats.errors += 1
            logger.error(f"AGI processing error: {e}", exc_info=True)
            
            return {
                "answer": "Lo siento, ocurrió un error procesando tu solicitud.",
                "strategy": "error",
                "status": "error",
                "error_details": str(e),
                "stats": self.stats.to_dict()
            }
    
    async def _simple_strategy(self, query: str) -> str:
        """
        Estrategia simple: RAG + LLM directo.
        
        Flujo:
        1. Retrieve context from RAG
        2. Build prompt with context
        3. Generate with LLM
        
        Latencia esperada: ~300ms
        """
        # Retrieve context si RAG disponible
        context = ""
        if self.rag:
            try:
                retrieved = self.rag.retrieve(query, top_k=3)
                context = "\n\n".join(retrieved)
                logger.debug(f"Retrieved {len(retrieved)} chunks from RAG")
            except Exception as e:
                logger.warning(f"RAG retrieval failed: {e}")
        
        # Build prompt
        prompt = self._build_simple_prompt(query, context)
        
        # Generate response
        response = await asyncio.to_thread(
            self.llm,
            prompt,
            max_tokens=512,
            temperature=0.2,
            stop=["<|end|>", "<|user|>"]
        )
        
        answer = response["choices"][0]["text"].strip()
        return answer
    
    async def _complex_strategy(self, query: str) -> str:
        """
        Estrategia compleja: Agente ReAct con tools.
        
        Flujo:
        1. Agente analiza query
        2. Decide qué tools usar
        3. Ejecuta tools (search_codebase, execute_code, web_search)
        4. Sintetiza respuesta final
        
        Latencia esperada: ~8s (depende de tools)
        """
        try:
            # Ejecutar agente
            result = await asyncio.to_thread(
                self.agent.run,
                query,
                max_steps=5
            )
            
            self.stats.tool_uses += 1
            return result
            
        except Exception as e:
            logger.error(f"Agent execution failed: {e}")
            # Fallback a estrategia simple
            logger.info("Falling back to simple strategy")
            return await self._simple_strategy(query)
    
    def _needs_complex_reasoning(self, query: str) -> bool:
        """
        Heurística para detectar si necesita razonamiento complejo.
        
        Busca keywords que indican necesidad de:
        - Crear código
        - Ejecutar múltiples pasos
        - Buscar información externa
        - Razonamiento multi-hop
        
        Args:
            query: Query a analizar
        
        Returns:
            True si necesita estrategia compleja
        """
        query_lower = query.lower()
        
        # Check keywords
        for keyword in self.complexity_keywords:
            if keyword in query_lower:
                logger.debug(f"Complex reasoning triggered by keyword: {keyword}")
                return True
        
        # Check query length (queries muy largos suelen ser complejos)
        if len(query.split()) > 30:
            logger.debug("Complex reasoning triggered by query length")
            return True
        
        # Check si menciona "tool" o "execute"
        if any(word in query_lower for word in ["tool", "execute", "run", "search"]):
            logger.debug("Complex reasoning triggered by tool mention")
            return True
        
        return False
    
    def _build_simple_prompt(self, query: str, context: str) -> str:
        """
        Construye prompt para estrategia simple.
        
        Formato Phi-4:
        <|user|>
        Context: ...
        Query: ...
        <|end|>
        <|assistant|>
        """
        prompt = "<|user|>\n"
        
        if context:
            prompt += f"Context:\n{context}\n\n"
        
        prompt += f"Query: {query}<|end|>\n<|assistant|>\n"
        
        return prompt
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del sistema."""
        return {
            **self.stats.to_dict(),
            "memory_episodes": len(self.memory),
            "memory_stats": self.memory.get_stats(),
            "rag_enabled": self.rag is not None
        }
    
    def get_recent_memory(self, n: int = 10) -> List[Dict[str, Any]]:
        """Obtiene memoria reciente."""
        episodes = self.memory.get_recent(n)
        return [
            {
                "query": ep.query,
                "answer": ep.answer[:200] + "..." if len(ep.answer) > 200 else ep.answer,
                "timestamp": ep.timestamp,
                "metadata": ep.metadata
            }
            for ep in episodes
        ]
    
    def __repr__(self) -> str:
        return (
            f"Phi4MiniAGI("
            f"calls={self.stats.total_calls}, "
            f"memory={len(self.memory)}, "
            f"avg_latency={self.stats.avg_latency_ms:.1f}ms"
            f")"
        )


# Factory function
def create_agi_system(config: Dict[str, Any]) -> Phi4MiniAGI:
    """
    Crea un sistema AGI desde configuración.
    
    Args:
        config: Dict con configuración del sistema
            - model_path: Path al modelo GGUF
            - rag_docs: Path a docs para RAG
            - memory_path: Path para memoria
            - memory_max_size: Tamaño buffer
            - n_ctx: Context size
            - n_gpu_layers: GPU layers
    
    Returns:
        Phi4MiniAGI configurado
    """
    return Phi4MiniAGI(
        model_path=config.get("model_path"),
        rag_docs=config.get("rag_docs"),
        memory_path=config.get("memory_path"),
        memory_max_size=config.get("memory_max_size", 1000),
        n_ctx=config.get("n_ctx", 4096),
        n_gpu_layers=config.get("n_gpu_layers", -1),
        complexity_keywords=config.get("complexity_keywords")
    )
