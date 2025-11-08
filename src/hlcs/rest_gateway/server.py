"""
HLCS REST Gateway

FastAPI gateway que traduce REST → gRPC (o llama directamente al orchestrator).
Puerto: 4001

Version 2.0: Soporta AGI system integration
"""

import os
import logging
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn
import yaml

# Local imports
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hlcs.mcp_client import SARAiMCPClient
from hlcs.orchestrator import HLCSOrchestrator

# Try to import AGI system
try:
    from hlcs.agi_system import Phi4MiniAGI
    AGI_AVAILABLE = True
except ImportError:
    AGI_AVAILABLE = False

# Try to import Meta-Consciousness
try:
    from hlcs.metacognition import create_meta_consciousness
    META_AVAILABLE = True
except ImportError:
    META_AVAILABLE = False

# Try to import Strategic Planning
try:
    from hlcs.planning import (
        create_strategic_planner, 
        GoalPriority,
        PlanStepStatus,
        HypothesisOutcome
    )
    PLANNING_AVAILABLE = True
except ImportError:
    PLANNING_AVAILABLE = False

# Try to import Multi-Stakeholder SCI
try:
    from hlcs.sci import (
        create_multi_stakeholder_sci,
        StakeholderRole,
        VoteChoice,
        ConsensusType
    )
    SCI_AVAILABLE = True
except ImportError:
    SCI_AVAILABLE = False

logger = logging.getLogger(__name__)

# Configuration
REST_PORT = int(os.getenv("HLCS_REST_PORT", "4001"))
SARAI_MCP_URL = os.getenv("SARAI_MCP_URL", "http://localhost:3000")
COMPLEXITY_THRESHOLD = float(os.getenv("COMPLEXITY_THRESHOLD", "0.5"))
QUALITY_THRESHOLD = float(os.getenv("QUALITY_THRESHOLD", "0.7"))
MAX_ITERATIONS = int(os.getenv("MAX_ITERATIONS", "3"))
ENABLE_AGI = os.getenv("ENABLE_AGI", "false").lower() == "true"

# Load config from YAML if available
CONFIG_PATH = os.getenv("HLCS_CONFIG", "./config/hlcs.yaml")
CONFIG = {}
try:
    with open(CONFIG_PATH, 'r') as f:
        CONFIG = yaml.safe_load(f)
        logger.info(f"Loaded config from {CONFIG_PATH}")
except Exception as e:
    logger.warning(f"Could not load config from {CONFIG_PATH}: {e}")


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
agi_system: Optional['Phi4MiniAGI'] = None
meta_consciousness = None
strategic_planner = None
multi_stakeholder_sci = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager."""
    global sarai_client, orchestrator, agi_system, meta_consciousness, strategic_planner, multi_stakeholder_sci
    
    logger.info("=" * 60)
    logger.info("HLCS REST Gateway Starting (v3.0 - Autonomous Intelligence)")
    logger.info("=" * 60)
    logger.info(f"Port: {REST_PORT}")
    logger.info(f"SARAi MCP URL: {SARAI_MCP_URL}")
    logger.info(f"Complexity Threshold: {COMPLEXITY_THRESHOLD}")
    logger.info(f"Quality Threshold: {QUALITY_THRESHOLD}")
    logger.info(f"Max Iterations: {MAX_ITERATIONS}")
    logger.info(f"AGI Enabled: {ENABLE_AGI}")
    logger.info("=" * 60)
    
    # Initialize AGI system if enabled
    if ENABLE_AGI and AGI_AVAILABLE:
        try:
            agi_config = CONFIG.get("agi", {})
            logger.info("Initializing AGI system...")
            
            agi_system = Phi4MiniAGI(
                model_path=agi_config.get("model", {}).get("path", "./models/phi4_mini_q4.gguf"),
                rag_docs=agi_config.get("rag", {}).get("docs_path"),
                memory_path=agi_config.get("memory", {}).get("persist_path", "./data/memory/episodes.json"),
                memory_max_size=agi_config.get("memory", {}).get("max_size", 1000),
                n_ctx=agi_config.get("model", {}).get("n_ctx", 4096),
                n_gpu_layers=agi_config.get("model", {}).get("n_gpu_layers", -1)
            )
            logger.info("✅ AGI system initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize AGI system: {e}")
            agi_system = None
    else:
        if ENABLE_AGI and not AGI_AVAILABLE:
            logger.warning("AGI enabled but not available (dependencies missing)")
        logger.info("AGI system disabled")
    
    # Initialize Meta-Consciousness Layer
    enable_meta = CONFIG.get("meta_consciousness", {}).get("enabled", True)
    if enable_meta and META_AVAILABLE:
        try:
            logger.info("Initializing Meta-Consciousness Layer...")
            meta_config = CONFIG.get("meta_consciousness", {})
            meta_consciousness = create_meta_consciousness(
                strategy=meta_config.get("strategy", "adaptive"),
                confidence_threshold=meta_config.get("confidence_threshold", 0.7)
            )
            logger.info("✅ Meta-Consciousness Layer initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Meta-Consciousness: {e}")
            meta_consciousness = None
    else:
        logger.info("Meta-Consciousness disabled or not available")
    
    # Initialize Strategic Planning System
    enable_planning = CONFIG.get("strategic_planning", {}).get("enabled", True)
    if enable_planning and PLANNING_AVAILABLE:
        try:
            logger.info("Initializing Strategic Planning System...")
            strategic_planner = create_strategic_planner()
            logger.info("✅ Strategic Planning System initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Strategic Planning: {e}")
            strategic_planner = None
    else:
        logger.info("Strategic Planning disabled or not available")
    
    # Initialize Multi-Stakeholder SCI
    enable_sci = CONFIG.get("multi_stakeholder_sci", {}).get("enabled", True)
    if enable_sci and SCI_AVAILABLE:
        try:
            logger.info("Initializing Multi-Stakeholder SCI...")
            sci_config = CONFIG.get("multi_stakeholder_sci", {})
            multi_stakeholder_sci = create_multi_stakeholder_sci(
                consensus_type=sci_config.get("consensus_type", "weighted"),
                timeout_minutes=sci_config.get("timeout_minutes", 30.0)
            )
            
            # Register default autonomous agent stakeholder
            multi_stakeholder_sci.register_stakeholder(
                name="HLCS_System",
                role=StakeholderRole.AUTONOMOUS_AGENT,
                verified=True
            )
            
            logger.info("✅ Multi-Stakeholder SCI initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Multi-Stakeholder SCI: {e}")
            multi_stakeholder_sci = None
    else:
        logger.info("Multi-Stakeholder SCI disabled or not available")
    
    # Initialize clients
    sarai_client = SARAiMCPClient(base_url=SARAI_MCP_URL)
    orchestrator = HLCSOrchestrator(
        sarai_client=sarai_client,
        agi_system=agi_system,
        enable_agi=agi_system is not None,
        meta_consciousness=meta_consciousness,
        enable_meta=meta_consciousness is not None,
        strategic_planner=strategic_planner,
        enable_planning=strategic_planner is not None,
        multi_stakeholder_sci=multi_stakeholder_sci,
        enable_sci=multi_stakeholder_sci is not None,
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
# Strategic Planning Endpoints
# ============================================================================

class CreateGoalRequest(BaseModel):
    """Request para crear un goal."""
    title: str
    description: str
    priority: str  # "critical", "high", "medium", "low"
    parent_goal_id: Optional[str] = None
    deadline: Optional[str] = None  # ISO format
    success_criteria: Optional[list[str]] = None
    dependencies: Optional[list[str]] = None


class GoalResponse(BaseModel):
    """Response con información de goal."""
    goal_id: str
    title: str
    description: str
    priority: str
    status: str
    progress: float
    created_at: str


class CreatePlanRequest(BaseModel):
    """Request para crear un plan."""
    goal_id: str
    decomposition_strategy: str = "sequential"  # "sequential", "parallel", "hybrid"


class PlanResponse(BaseModel):
    """Response con información de plan."""
    plan_id: str
    goal_id: str
    title: str
    total_steps: int
    estimated_duration_minutes: float
    progress: float


class ExecutePlanRequest(BaseModel):
    """Request para ejecutar un plan."""
    plan_id: str


class ExecutionSummaryResponse(BaseModel):
    """Response con resumen de ejecución."""
    plan_id: str
    steps_executed: int
    steps_succeeded: int
    steps_failed: int
    total_duration_minutes: float
    status: str


@app.post("/api/v1/planning/goals", response_model=GoalResponse)
async def create_goal(request: CreateGoalRequest):
    """Crear un nuevo goal en el sistema de planificación."""
    if not PLANNING_AVAILABLE:
        raise HTTPException(status_code=503, detail="Strategic Planning not available")
    
    if not hasattr(orchestrator, 'strategic_planner') or not orchestrator.strategic_planner:
        raise HTTPException(status_code=503, detail="Strategic Planner not initialized")
    
    try:
        from datetime import datetime
        
        # Parse priority
        priority_map = {
            "critical": GoalPriority.CRITICAL,
            "high": GoalPriority.HIGH,
            "medium": GoalPriority.MEDIUM,
            "low": GoalPriority.LOW
        }
        priority = priority_map.get(request.priority.lower(), GoalPriority.MEDIUM)
        
        # Parse deadline
        deadline = None
        if request.deadline:
            deadline = datetime.fromisoformat(request.deadline)
        
        # Create goal
        goal = orchestrator.strategic_planner.goal_manager.create_goal(
            title=request.title,
            description=request.description,
            priority=priority,
            parent_goal_id=request.parent_goal_id,
            deadline=deadline,
            success_criteria=request.success_criteria,
            dependencies=request.dependencies
        )
        
        return GoalResponse(
            goal_id=goal.id,
            title=goal.title,
            description=goal.description,
            priority=goal.priority.name.lower(),
            status=goal.status.value,
            progress=goal.progress,
            created_at=goal.created_at.isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error creating goal: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/planning/goals/{goal_id}", response_model=GoalResponse)
async def get_goal(goal_id: str):
    """Obtener información de un goal."""
    if not PLANNING_AVAILABLE:
        raise HTTPException(status_code=503, detail="Strategic Planning not available")
    
    if not hasattr(orchestrator, 'strategic_planner') or not orchestrator.strategic_planner:
        raise HTTPException(status_code=503, detail="Strategic Planner not initialized")
    
    goal = orchestrator.strategic_planner.goal_manager.get_goal(goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    return GoalResponse(
        goal_id=goal.id,
        title=goal.title,
        description=goal.description,
        priority=goal.priority.name.lower(),
        status=goal.status.value,
        progress=goal.progress,
        created_at=goal.created_at.isoformat()
    )


@app.post("/api/v1/planning/plans", response_model=PlanResponse)
async def create_plan(request: CreatePlanRequest):
    """Crear un plan de ejecución para un goal."""
    if not PLANNING_AVAILABLE:
        raise HTTPException(status_code=503, detail="Strategic Planning not available")
    
    if not hasattr(orchestrator, 'strategic_planner') or not orchestrator.strategic_planner:
        raise HTTPException(status_code=503, detail="Strategic Planner not initialized")
    
    try:
        plan = orchestrator.strategic_planner.plan_executor.create_plan_for_goal(
            goal_id=request.goal_id,
            decomposition_strategy=request.decomposition_strategy
        )
        
        return PlanResponse(
            plan_id=plan.id,
            goal_id=plan.goal_id,
            title=plan.title,
            total_steps=len(plan.steps),
            estimated_duration_minutes=plan.total_estimated_duration,
            progress=plan.get_progress()
        )
        
    except Exception as e:
        logger.error(f"Error creating plan: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/planning/plans/{plan_id}/execute", response_model=ExecutionSummaryResponse)
async def execute_plan(plan_id: str):
    """Ejecutar un plan paso a paso."""
    if not PLANNING_AVAILABLE:
        raise HTTPException(status_code=503, detail="Strategic Planning not available")
    
    if not hasattr(orchestrator, 'strategic_planner') or not orchestrator.strategic_planner:
        raise HTTPException(status_code=503, detail="Strategic Planner not initialized")
    
    try:
        # Define executor callback for plan steps
        async def step_executor(step):
            """Execute a single plan step using HLCS orchestrator."""
            logger.info(f"Executing step: {step.description}")
            
            # Use orchestrator to process the step
            result = await orchestrator.process(
                query=f"Execute step: {step.description}",
                context={"step_id": step.id, "required_tools": step.required_tools}
            )
            
            return result["result"]
        
        # Execute plan
        execution_result = await orchestrator.strategic_planner.plan_executor.execute_plan(
            plan_id,
            executor_callback=step_executor
        )
        
        # Determine status
        if execution_result["steps_failed"] > 0:
            status = "failed"
        elif execution_result["steps_executed"] == execution_result["steps_succeeded"]:
            status = "completed"
        else:
            status = "partial"
        
        return ExecutionSummaryResponse(
            plan_id=plan_id,
            steps_executed=execution_result["steps_executed"],
            steps_succeeded=execution_result["steps_succeeded"],
            steps_failed=execution_result["steps_failed"],
            total_duration_minutes=execution_result["total_duration_minutes"],
            status=status
        )
        
    except Exception as e:
        logger.error(f"Error executing plan: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Multi-Stakeholder SCI Endpoints
# ============================================================================

class RegisterStakeholderRequest(BaseModel):
    """Request para registrar stakeholder."""
    name: str
    role: str  # "primary_user", "administrator", "autonomous_agent", "observer"
    verified: bool = False


class StakeholderResponse(BaseModel):
    """Response con información de stakeholder."""
    stakeholder_id: str
    name: str
    role: str
    verified: bool
    vote_count: int
    agreement_rate: float
    voting_weight: float


class CreateDecisionRequest(BaseModel):
    """Request para crear una decisión."""
    title: str
    description: str
    decision_type: str
    criticality: float
    options: Optional[list[dict]] = None
    recommended_option: Optional[str] = None
    required_roles: Optional[list[str]] = None


class DecisionResponse(BaseModel):
    """Response con información de decisión."""
    decision_id: str
    title: str
    description: str
    criticality: float
    final_outcome: Optional[str]
    outcome_rationale: Optional[str]
    votes_count: int


class CastVoteRequest(BaseModel):
    """Request para emitir un voto."""
    stakeholder_id: str
    decision_id: str
    choice: str  # "approve", "reject", "abstain", "delegate"
    rationale: Optional[str] = None


@app.post("/api/v1/sci/stakeholders", response_model=StakeholderResponse)
async def register_stakeholder(request: RegisterStakeholderRequest):
    """Registrar un nuevo stakeholder en el sistema SCI."""
    if not SCI_AVAILABLE:
        raise HTTPException(status_code=503, detail="Multi-Stakeholder SCI not available")
    
    if not hasattr(orchestrator, 'multi_stakeholder_sci') or not orchestrator.multi_stakeholder_sci:
        raise HTTPException(status_code=503, detail="Multi-Stakeholder SCI not initialized")
    
    try:
        # Parse role
        role_map = {
            "primary_user": StakeholderRole.PRIMARY_USER,
            "administrator": StakeholderRole.ADMINISTRATOR,
            "autonomous_agent": StakeholderRole.AUTONOMOUS_AGENT,
            "observer": StakeholderRole.OBSERVER
        }
        role = role_map.get(request.role.lower())
        if not role:
            raise HTTPException(status_code=400, detail=f"Invalid role: {request.role}")
        
        # Register stakeholder
        stakeholder_id = orchestrator.multi_stakeholder_sci.register_stakeholder(
            name=request.name,
            role=role,
            verified=request.verified
        )
        
        # Get summary
        summary = orchestrator.multi_stakeholder_sci.get_stakeholder_summary(stakeholder_id)
        
        return StakeholderResponse(**summary)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering stakeholder: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/sci/decisions", response_model=DecisionResponse)
async def create_decision(request: CreateDecisionRequest):
    """Crear una nueva decisión para consenso."""
    if not SCI_AVAILABLE:
        raise HTTPException(status_code=503, detail="Multi-Stakeholder SCI not available")
    
    if not hasattr(orchestrator, 'multi_stakeholder_sci') or not orchestrator.multi_stakeholder_sci:
        raise HTTPException(status_code=503, detail="Multi-Stakeholder SCI not initialized")
    
    try:
        # Parse required roles
        required_roles = None
        if request.required_roles:
            role_map = {
                "primary_user": StakeholderRole.PRIMARY_USER,
                "administrator": StakeholderRole.ADMINISTRATOR,
                "autonomous_agent": StakeholderRole.AUTONOMOUS_AGENT,
                "observer": StakeholderRole.OBSERVER
            }
            required_roles = [role_map[r.lower()] for r in request.required_roles if r.lower() in role_map]
        
        # Create decision
        decision = orchestrator.multi_stakeholder_sci.create_decision(
            title=request.title,
            description=request.description,
            decision_type=request.decision_type,
            criticality=request.criticality,
            options=request.options,
            recommended_option=request.recommended_option,
            required_roles=required_roles
        )
        
        return DecisionResponse(
            decision_id=decision.decision_id,
            title=decision.title,
            description=decision.description,
            criticality=decision.criticality,
            final_outcome=decision.final_outcome,
            outcome_rationale=decision.outcome_rationale,
            votes_count=len(decision.votes)
        )
        
    except Exception as e:
        logger.error(f"Error creating decision: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/sci/votes")
async def cast_vote(request: CastVoteRequest):
    """Emitir un voto en una decisión."""
    if not SCI_AVAILABLE:
        raise HTTPException(status_code=503, detail="Multi-Stakeholder SCI not available")
    
    if not hasattr(orchestrator, 'multi_stakeholder_sci') or not orchestrator.multi_stakeholder_sci:
        raise HTTPException(status_code=503, detail="Multi-Stakeholder SCI not initialized")
    
    try:
        # Parse vote choice
        choice_map = {
            "approve": VoteChoice.APPROVE,
            "reject": VoteChoice.REJECT,
            "abstain": VoteChoice.ABSTAIN,
            "delegate": VoteChoice.DELEGATE
        }
        choice = choice_map.get(request.choice.lower())
        if not choice:
            raise HTTPException(status_code=400, detail=f"Invalid choice: {request.choice}")
        
        # Cast vote
        vote = orchestrator.multi_stakeholder_sci.cast_vote(
            stakeholder_id=request.stakeholder_id,
            decision_id=request.decision_id,
            choice=choice,
            rationale=request.rationale
        )
        
        return {"vote_id": vote.vote_id, "status": "success"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error casting vote: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/sci/decisions/{decision_id}/consensus")
async def reach_consensus(decision_id: str, wait_for_all: bool = False):
    """Alcanzar consenso en una decisión."""
    if not SCI_AVAILABLE:
        raise HTTPException(status_code=503, detail="Multi-Stakeholder SCI not available")
    
    if not hasattr(orchestrator, 'multi_stakeholder_sci') or not orchestrator.multi_stakeholder_sci:
        raise HTTPException(status_code=503, detail="Multi-Stakeholder SCI not initialized")
    
    try:
        consensus_reached, rationale = orchestrator.multi_stakeholder_sci.reach_consensus(
            decision_id,
            wait_for_all=wait_for_all
        )
        
        return {
            "decision_id": decision_id,
            "consensus_reached": consensus_reached,
            "rationale": rationale
        }
        
    except Exception as e:
        logger.error(f"Error reaching consensus: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


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
