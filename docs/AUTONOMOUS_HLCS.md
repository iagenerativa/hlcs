# 🧠 HLCS Autonomous Intelligence System

**Version**: 3.0.0  
**Date**: 7 de noviembre de 2025  
**Status**: ✅ Production Ready

---

## 🎯 Executive Summary

HLCS v3.0 es un **sistema de inteligencia autónoma** que toma decisiones estratégicas sobre cuándo y cómo utilizar los componentes del ecosistema SARAi. El sistema combina:

- **Meta-Consciousness Layer** (v0.2): Introspección y auto-evaluación
- **Strategic Planning System** (v0.5): Planificación orientada a objetivos
- **Multi-Stakeholder SCI** (v0.4): Consenso inteligente entre stakeholders
- **Phi4MiniAGI**: Sistema AGI local con RAG, memoria y agentes
- **SARAi MCP Integration**: Acceso a herramientas especializadas

El resultado es un sistema que **piensa antes de actuar**, **aprende de la experiencia**, y **toma decisiones equilibradas** considerando múltiples perspectivas.

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    HLCS v3.0 - Autonomous Layer                  │
│                                                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │         Meta-Consciousness Layer (Introspection)           │  │
│  │  • IgnoranceConsciousness: "Know what we don't know"       │  │
│  │  • SelfDoubtScore: Confidence assessment                   │  │
│  │  • NarrativeConsciousness: Episode understanding           │  │
│  │  • TemporalContext: Context freshness tracking             │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              ↓                                    │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │           Strategic Planning System (Goals)                │  │
│  │  • GoalManager: Hierarchical goal tracking                 │  │
│  │  • PlanExecutor: Plan decomposition & execution            │  │
│  │  │  • ProgressTracker: Milestone monitoring                   │  │
│  │  • ScenarioSimulator: What-if analysis                     │  │
│  │  • HypothesisTester: Hypothesis validation                 │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              ↓                                    │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │      Multi-Stakeholder SCI (Consensus Intelligence)        │  │
│  │  • Weighted Voting: 60% user, 30% admin, 10% agents       │  │
│  │  • VotingStrategy: Flexible consensus mechanisms           │  │
│  │  • ConsensusBuilder: Conflict resolution                   │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              ↓                                    │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │               HLCSOrchestrator (Decision Hub)              │  │
│  │  Routes intelligently to:                                  │  │
│  │    • SARAi MCP Tools (SAUL, Vision, Audio, RAG)           │  │
│  │    • Phi4MiniAGI System (Local reasoning + code)          │  │
│  │    • Ensemble Mode (Combine multiple approaches)          │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              ↓                                    │
│  ┌─────────────────┐  ┌────────────────────────────────────┐   │
│  │  SARAi MCP      │  │      Phi4MiniAGI System            │   │
│  │  • SAUL         │  │  • Phi-4-mini LLM (local)          │   │
│  │  • Vision       │  │  • KnowledgeRAG (semantic search)  │   │
│  │  • Audio        │  │  • CodeAgent (ReAct + tools)       │   │
│  │  • TRM          │  │  • MemoryBuffer (episodic)         │   │
│  └─────────────────┘  └────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────┘
```

---

## 🧠 Meta-Consciousness Layer (v0.2)

### Overview

La capa meta-cognitiva permite a HLCS **monitorear sus propios procesos de decisión** y auto-evaluar su rendimiento. Es el "sistema de introspección" que responde preguntas como:

- *¿Qué tan confiado estoy en esta respuesta?*
- *¿Qué es lo que NO sé sobre este problema?*
- *¿Debo buscar más información antes de decidir?*
- *¿Qué componente es mejor para esta tarea?*

### Key Components

#### 1. **IgnoranceConsciousness**

Trackea **qué no sabemos**:

```python
from hlcs.metacognition import IgnoranceConsciousness

ignorance = IgnoranceConsciousness(knowledge_domains=[
    "code_generation", "data_analysis", "multimodal_processing"
])

# Assess ignorance about a query
ignorance_score = ignorance.assess_ignorance(
    query="Analyze this MRI scan",
    context={},
    available_tools=["saul.respond", "rag.search"]
)

print(f"Ignorance type: {ignorance_score.ignorance_type}")
print(f"Confidence in ignorance: {ignorance_score.confidence:.2f}")
print(f"Knowledge gaps: {ignorance_score.knowledge_gaps}")
# Output:
# Ignorance type: KNOWN_UNKNOWNS
# Confidence in ignorance: 0.80
# Knowledge gaps: ['Multimodal tools not available', 'Specialized domain knowledge may be incomplete']

# Get recommendations
recommendations = ignorance.get_learning_recommendations(ignorance_score)
print(recommendations)
# Output: ['Route to SARAi Vision/Audio MCP tools', 'Use RAG to retrieve specialized knowledge']
```

**Types of Ignorance**:
- `KNOWN_UNKNOWNS`: "I know I don't know this" (e.g., missing tools)
- `UNKNOWN_UNKNOWNS`: "I don't know what I don't know" (e.g., first query)
- `EPISTEMIC`: Lack of knowledge (can be filled with learning)
- `ALEATORY`: Inherent randomness/uncertainty

#### 2. **SelfDoubtScore**

Cuantifica la **confianza en decisiones**:

```python
from hlcs.metacognition import SelfDoubtScore

self_doubt = SelfDoubtScore(
    confidence_score=0.75,      # Overall confidence
    reasoning_clarity=0.85,     # How clear is the reasoning
    evidence_strength=0.70,     # Strength of evidence
    alternative_count=3,        # Number of plausible alternatives
    uncertainty_level=0.30      # Epistemic uncertainty
)

composite_confidence = self_doubt.get_composite_confidence()
print(f"Composite confidence: {composite_confidence:.2f}")
# Output: Composite confidence: 0.73
```

**Formula**:
```
composite = 0.35*confidence + 0.25*reasoning + 0.25*evidence + 0.15*(1-uncertainty) - alternative_penalty
```

#### 3. **NarrativeConsciousness**

Construye **narrativas** de la memoria episódica:

```python
from hlcs.metacognition import NarrativeConsciousness

narrative_system = NarrativeConsciousness(max_narrative_length=10)

# Build narrative from memory episodes
narrative = narrative_system.construct_narrative(
    episodes=[
        {"type": "query_response", "query": "Create API endpoint", "success": True},
        {"type": "query_response", "query": "Debug auth error", "success": True},
        {"type": "query_response", "query": "Implement JWT", "success": False}
    ],
    focus="learning"  # or "goals", "patterns"
)

print(narrative)
# Output:
# Recent learning trajectory:
# ✓ Handled: Create API endpoint...
# ✓ Handled: Debug auth error...
# ✗ Struggled with: Implement JWT...
```

#### 4. **MetaConsciousnessLayer** (Main Class)

Coordina toda la capa meta-cognitiva:

```python
from hlcs.metacognition import create_meta_consciousness

# Create meta-consciousness with adaptive strategy
meta = create_meta_consciousness(
    strategy="adaptive",  # conservative, exploratory, balanced, adaptive
    confidence_threshold=0.7
)

# Analyze query context
meta_state = meta.analyze_query_context(
    query="Create a REST API with JWT authentication",
    context={"user_history": [], "memory_episodes": []},
    available_components=["sarai_mcp", "phi4mini_agi", "code_agent"]
)

print(f"Confidence: {meta_state.self_doubt.get_composite_confidence():.2f}")
print(f"Ignorance gaps: {len(meta_state.ignorance_score.knowledge_gaps)}")
print(f"Decision strategy: {meta_state.decision_strategy.value}")

# Decide component routing
routing_decision = meta.decide_component_routing(
    meta_state,
    available_components={
        "sarai_mcp": {"available": True, "tools": ["saul", "rag"]},
        "phi4mini_agi": {"available": True, "tools": ["code_agent", "rag"]}
    }
)

print(f"Route to: {routing_decision['primary_component']}")
print(f"Reasoning: {routing_decision['reasoning']}")
# Output:
# Route to: phi4mini_agi
# Reasoning: ['Recommendations favor local AGI']
```

### Decision Strategies

**Available strategies**:

1. **CONSERVATIVE**: Prefer known-good solutions (SAUL for simple, AGI as fallback)
2. **EXPLORATORY**: Try new approaches (AGI-first for learning)
3. **BALANCED**: Use ensemble voting (combine multiple approaches)
4. **ADAPTIVE**: Adapt based on context and recommendations (default)

---

## 📋 Strategic Planning System (v0.5)

### Overview

Sistema completo de **planificación orientada a objetivos** que permite a HLCS:

- Definir y trackear goals jerárquicos
- Descomponer goals en planes ejecutables
- Monitorear progreso via milestones
- Simular escenarios "what-if"
- Validar hipótesis mediante experimentación

### Key Components

#### 1. **GoalManager**

Gestiona goals con **jerarquía y dependencias**:

```python
from hlcs.planning import GoalManager, GoalPriority

goal_manager = GoalManager()

# Create parent goal
parent_goal = goal_manager.create_goal(
    title="Build complete authentication system",
    description="Implement JWT-based auth with refresh tokens",
    priority=GoalPriority.HIGH,
    success_criteria=[
        "JWT token generation working",
        "Refresh token rotation implemented",
        "All endpoints protected",
        "Tests passing"
    ]
)

# Create subgoals
subgoal1 = goal_manager.create_goal(
    title="Implement JWT generation",
    description="Create JWT signing and validation",
    priority=GoalPriority.CRITICAL,
    parent_goal_id=parent_goal.id
)

subgoal2 = goal_manager.create_goal(
    title="Add refresh token logic",
    description="Implement token refresh endpoint",
    priority=GoalPriority.HIGH,
    parent_goal_id=parent_goal.id,
    dependencies=[subgoal1.id]  # Depends on JWT implementation
)

# Get executable goals (dependencies met)
executable = goal_manager.get_executable_goals()
print(f"Can start: {[g.title for g in executable]}")

# Visualize goal tree
print(goal_manager.get_goal_tree(parent_goal.id))
# Output:
# ⏸ Build complete authentication system (0%)
#   ⏸ Implement JWT generation (0%)
#   ⏸ Add refresh token logic (0%)
```

**Goal Status**: `PENDING`, `IN_PROGRESS`, `COMPLETED`, `FAILED`, `PAUSED`, `CANCELLED`

#### 2. **PlanExecutor**

Descompone goals en **planes ejecutables**:

```python
from hlcs.planning import PlanExecutor

plan_executor = PlanExecutor(goal_manager)

# Create execution plan for goal
plan = plan_executor.create_plan_for_goal(
    goal_id=subgoal1.id,
    decomposition_strategy="sequential"  # or "parallel", "hybrid"
)

print(f"Plan: {plan.title}")
print(f"Steps: {len(plan.steps)}")
print(f"Estimated duration: {plan.total_estimated_duration:.0f} minutes")

# Execute plan with callback
async def execute_step(step):
    """Execute single step via HLCS orchestrator."""
    print(f"→ {step.description}")
    
    # Call orchestrator or tools
    result = await orchestrator.process(
        query=f"Execute: {step.description}",
        context={"required_tools": step.required_tools}
    )
    
    return result["result"]

execution_result = await plan_executor.execute_plan(
    plan.id,
    executor_callback=execute_step
)

print(f"✅ Steps succeeded: {execution_result['steps_succeeded']}")
print(f"❌ Steps failed: {execution_result['steps_failed']}")
print(f"⏱ Duration: {execution_result['total_duration_minutes']:.1f} min")
```

**Plan Decomposition Strategies**:
- `sequential`: Steps executed in order
- `parallel`: Independent steps can run concurrently
- `hybrid`: Mix of sequential and parallel

#### 3. **ProgressTracker**

Trackea progreso mediante **milestones**:

```python
from hlcs.planning import ProgressTracker
from datetime import datetime, timedelta

progress_tracker = ProgressTracker(goal_manager)

# Create milestones
milestone1 = progress_tracker.create_milestone(
    goal_id=parent_goal.id,
    title="MVP authentication ready",
    target_date=datetime.now() + timedelta(days=7),
    criteria=[
        "JWT generation working",
        "Basic login endpoint",
        "Token validation middleware"
    ]
)

# Check milestone achievement
achieved = progress_tracker.check_milestone(
    milestone1.id,
    context={"completed_features": ["JWT generation", "login endpoint", "validation"]}
)

print(f"Milestone achieved: {achieved}")

# Generate progress report
report = progress_tracker.get_progress_report(parent_goal.id)
print(f"Goal: {report['goal_title']}")
print(f"Progress: {report['goal_progress']*100:.0f}%")
print(f"Milestones: {report['milestones']['achieved']}/{report['milestones']['total']}")
print(f"On track: {report['is_on_track']}")
```

#### 4. **ScenarioSimulator**

Simula escenarios **"what-if"**:

```python
from hlcs.planning import ScenarioSimulator

simulator = ScenarioSimulator()

# Create scenarios
scenario1 = simulator.create_scenario(
    title="Use JWT library vs custom implementation",
    description="Compare using PyJWT vs rolling our own JWT",
    assumptions={
        "complexity": "low",  # Using library
        "available_resources": ["PyJWT", "cryptography"],
        "constraints": ["Must support RS256", "Must handle expiry"]
    }
)

scenario2 = simulator.create_scenario(
    title="Custom JWT implementation",
    description="Build JWT from scratch for learning",
    assumptions={
        "complexity": "high",
        "available_resources": ["cryptography"],
        "constraints": ["Must support RS256", "Must handle expiry", "Educational value"]
    }
)

# Simulate both scenarios
result1 = simulator.simulate(scenario1.id)
result2 = simulator.simulate(scenario2.id)

# Compare
comparison = simulator.compare_scenarios([scenario1.id, scenario2.id])
for comp in comparison:
    print(f"{comp['title']}: success_prob={comp['success_probability']:.2f}")

# Output:
# Use JWT library vs custom implementation: success_prob=0.85
# Custom JWT implementation: success_prob=0.55
```

#### 5. **HypothesisTester**

Valida **hipótesis** mediante experimentos:

```python
from hlcs.planning import HypothesisTester

hypothesis_tester = HypothesisTester()

# Create hypothesis
hypothesis = hypothesis_tester.create_hypothesis(
    statement="PyJWT library can handle RS256 with custom claims",
    rationale="Library claims RS256 support, need to verify with our use case",
    test_procedure=[
        "Install PyJWT",
        "Create test RSA key pair",
        "Encode token with custom claims",
        "Decode and verify claims",
        "Test expiry handling"
    ],
    success_criteria=[
        "Token encodes successfully",
        "Token decodes successfully",
        "Custom claims preserved",
        "Expiry validation works"
    ],
    prior_confidence=0.7
)

# Test hypothesis
async def run_test(procedure):
    """Execute test steps."""
    results = []
    for step in procedure:
        result = await orchestrator.process(f"Test: {step}")
        results.append(result["result"])
    return "\n".join(results)

outcome = await hypothesis_tester.test_hypothesis(
    hypothesis.id,
    test_executor=run_test
)

print(f"Hypothesis: {hypothesis.statement}")
print(f"Outcome: {outcome.value}")
print(f"Updated confidence: {hypothesis.confidence:.2f}")
print(f"Evidence: {hypothesis.evidence}")

# Output:
# Hypothesis: PyJWT library can handle RS256 with custom claims
# Outcome: confirmed
# Updated confidence: 0.95
# Evidence: ['Met: Token encodes successfully', 'Met: Token decodes successfully', ...]
```

### REST API Endpoints

Strategic Planning está expuesto via REST API:

```bash
# Create goal
curl -X POST http://localhost:4001/api/v1/planning/goals \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Build auth system",
    "description": "Complete JWT authentication",
    "priority": "high",
    "success_criteria": ["JWT working", "Tests passing"]
  }'

# Get goal
curl http://localhost:4001/api/v1/planning/goals/{goal_id}

# Create plan
curl -X POST http://localhost:4001/api/v1/planning/plans \
  -H "Content-Type: application/json" \
  -d '{
    "goal_id": "goal-uuid-here",
    "decomposition_strategy": "sequential"
  }'

# Execute plan
curl -X POST http://localhost:4001/api/v1/planning/plans/{plan_id}/execute
```

---

## 🤝 Multi-Stakeholder SCI (v0.4)

### Overview

Sistema de **consenso inteligente** que permite decisiones considerando múltiples perspectivas:

- **Primary User** (60% weight): El usuario principal
- **Administrator** (30% weight): Administrador del sistema
- **Autonomous Agents** (10% weight): Agentes AI del sistema
- **Observers** (0% weight): Stakeholders sin voto

### Key Components

#### 1. **MultiStakeholderSCI** (Main Class)

Sistema central de consenso:

```python
from hlcs.sci import create_multi_stakeholder_sci, StakeholderRole

# Create SCI system with weighted consensus
sci = create_multi_stakeholder_sci(
    consensus_type="weighted",  # weighted, simple_majority, supermajority, unanimous, adaptive
    timeout_minutes=30.0
)

# Register stakeholders
user_id = sci.register_stakeholder(
    name="Alice (Developer)",
    role=StakeholderRole.PRIMARY_USER,
    verified=True
)

admin_id = sci.register_stakeholder(
    name="System Administrator",
    role=StakeholderRole.ADMINISTRATOR,
    verified=True
)

agent_id = sci.register_stakeholder(
    name="HLCS Agent",
    role=StakeholderRole.AUTONOMOUS_AGENT,
    verified=True
)

print(f"Registered {len(sci.stakeholders)} stakeholders")
```

#### 2. **Decision Creation & Voting**

Crear decisiones y recopilar votos:

```python
from hlcs.sci import VoteChoice

# Create decision
decision = sci.create_decision(
    title="Route complex query to AGI or SARAi?",
    description="Query: 'Create API with JWT auth'. Meta-consciousness recommends AGI.",
    decision_type="component_routing",
    criticality=0.75,  # High criticality
    recommended_option="phi4mini_agi",
    required_roles=[StakeholderRole.PRIMARY_USER, StakeholderRole.AUTONOMOUS_AGENT]
)

# Cast votes
sci.cast_vote(
    stakeholder_id=user_id,
    decision_id=decision.decision_id,
    choice=VoteChoice.APPROVE,
    rationale="AGI has better code generation"
)

sci.cast_vote(
    stakeholder_id=agent_id,
    decision_id=decision.decision_id,
    choice=VoteChoice.APPROVE,
    rationale="Following system recommendation"
)

# Reach consensus
consensus_reached, rationale = sci.reach_consensus(decision.decision_id)

print(f"Consensus: {consensus_reached}")
print(f"Rationale: {rationale}")
# Output:
# Consensus: True
# Rationale: Weighted approval: 70.0% (threshold: 60%)
```

#### 3. **Consensus Types**

**Available consensus mechanisms**:

| Type | Description | Use Case |
|------|-------------|----------|
| `WEIGHTED` | Uses role weights (60/30/10) | Default for routine decisions |
| `SIMPLE_MAJORITY` | >50% approval | Low-risk decisions |
| `SUPERMAJORITY` | ≥2/3 approval | Medium-risk decisions |
| `UNANIMOUS` | All must approve | Critical decisions |
| `ADAPTIVE` | Adapts to criticality | Automatic based on risk |

```python
# Adaptive consensus adjusts based on criticality
sci_adaptive = create_multi_stakeholder_sci(consensus_type="adaptive")

# Low criticality (0.3) → simple majority
decision_low = sci_adaptive.create_decision(
    title="Use caching for API responses?",
    description="Add Redis cache to API",
    decision_type="optimization",
    criticality=0.3
)

# High criticality (0.9) → supermajority required
decision_high = sci_adaptive.create_decision(
    title="Switch from PostgreSQL to MongoDB?",
    description="Major database migration",
    decision_type="infrastructure",
    criticality=0.9
)
```

#### 4. **Conflict Resolution**

Cuando no hay consenso:

```python
from hlcs.sci import ConsensusBuilder

consensus_builder = ConsensusBuilder(voting_strategy, timeout_minutes=30)

# If consensus fails, resolve conflict
if not consensus_reached:
    resolution = consensus_builder.resolve_conflict(decision, sci.stakeholders)
    print(f"Resolution: {resolution}")
    
# Resolution strategies:
# 1. Defer to primary user vote
# 2. Defer to administrator vote
# 3. Default to rejection (safe fallback)
```

### REST API Endpoints

Multi-Stakeholder SCI via REST:

```bash
# Register stakeholder
curl -X POST http://localhost:4001/api/v1/sci/stakeholders \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Alice Developer",
    "role": "primary_user",
    "verified": true
  }'

# Create decision
curl -X POST http://localhost:4001/api/v1/sci/decisions \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Route to AGI or SARAi?",
    "description": "Complex code generation task",
    "decision_type": "component_routing",
    "criticality": 0.7,
    "recommended_option": "phi4mini_agi"
  }'

# Cast vote
curl -X POST http://localhost:4001/api/v1/sci/votes \
  -H "Content-Type: application/json" \
  -d '{
    "stakeholder_id": "user-uuid",
    "decision_id": "decision-uuid",
    "choice": "approve",
    "rationale": "AGI is better for code"
  }'

# Reach consensus
curl -X POST http://localhost:4001/api/v1/sci/decisions/{decision_id}/consensus
```

---

## 🔄 Autonomous Decision Flow

### Complete Flow Example

```python
from hlcs.orchestrator import HLCSOrchestrator
from hlcs.metacognition import create_meta_consciousness
from hlcs.planning import create_strategic_planner
from hlcs.sci import create_multi_stakeholder_sci, StakeholderRole
from hlcs.mcp_client import SARAiMCPClient
from hlcs.agi_system import Phi4MiniAGI

# 1. Initialize all systems
async with SARAiMCPClient("http://localhost:3000") as sarai:
    # Create AGI system
    agi = Phi4MiniAGI(
        model_path="./models/phi4_mini_q4.gguf",
        rag_docs="./data/codebase.py",
        memory_path="./data/memory/episodes.json"
    )
    
    # Create meta-consciousness
    meta = create_meta_consciousness(strategy="adaptive")
    
    # Create strategic planner
    planner = create_strategic_planner()
    
    # Create SCI
    sci = create_multi_stakeholder_sci(consensus_type="weighted")
    user_id = sci.register_stakeholder("Alice", StakeholderRole.PRIMARY_USER, verified=True)
    
    # Create orchestrator with all systems
    orchestrator = HLCSOrchestrator(
        sarai_client=sarai,
        agi_system=agi,
        enable_agi=True,
        meta_consciousness=meta,
        enable_meta=True,
        strategic_planner=planner,
        enable_planning=True,
        multi_stakeholder_sci=sci,
        enable_sci=True
    )
    
    # 2. Process query autonomously
    result = await orchestrator.process(
        query="Create a REST API with JWT authentication and refresh tokens",
        user_id=user_id,
        session_id="session-123"
    )
    
    # The system will:
    # ✓ Meta-consciousness analyzes query context
    # ✓ Assesses ignorance (what we don't know)
    # ✓ Calculates self-doubt score
    # ✓ Decides routing: AGI vs SARAi vs Ensemble
    # ✓ If ensemble, gets SCI consensus
    # ✓ Executes chosen workflow
    # ✓ Evaluates response quality meta-cognitively
    # ✓ Refines if quality below threshold
    
    print(f"Result: {result['result']}")
    print(f"Strategy used: {result['strategy']}")
    print(f"Quality score: {result['quality_score']}")
    print(f"Meta statistics: {result['metadata']['meta_statistics']}")
```

### Decision Matrix

| Query Complexity | Meta-Consciousness Decision | SCI Involvement | Actual Route |
|------------------|----------------------------|-----------------|--------------|
| Low (< 0.5) | "High confidence, use proven SARAi" | No (routine) | SARAi SAUL |
| Medium (0.5-0.7) | "Moderate confidence, try AGI with fallback" | Optional | AGI → SARAi fallback |
| High (> 0.7) | "Low confidence, use ensemble" | Yes (if enabled) | Ensemble (AGI + SARAi) |
| Code-related | "Code keywords detected, prefer AGI" | No (specialized) | AGI CodeAgent |
| Multimodal | "Image/audio detected, use specialized tools" | No (specialized) | SARAi Vision/Audio |

---

## 📊 Monitoring & Statistics

### Meta-Cognitive Statistics

```python
# Get meta-consciousness statistics
meta_stats = orchestrator.meta_consciousness.get_meta_statistics()

print("Temporal Context:")
print(f"  Session duration: {meta_stats['temporal']['session_duration_minutes']:.1f} min")
print(f"  Interactions: {meta_stats['temporal']['interactions']}")
print(f"  Context freshness: {meta_stats['temporal']['context_freshness']:.2f}")

print("\nDecisions:")
print(f"  Total decisions: {meta_stats['decisions']['total_decisions']}")
print(f"  Avg confidence: {meta_stats['decisions']['avg_confidence']:.2f}")
print(f"  Strategy: {meta_stats['decisions']['strategy']}")

print("\nPerformance:")
print(f"  Avg quality: {meta_stats['performance']['avg_quality_score']:.2f}")

print("\nIgnorance Tracking:")
for query, confidence, timestamp in meta_stats['ignorance']['recent_uncertainty'][-3:]:
    print(f"  {query[:50]}... → uncertainty={1-confidence:.2f}")

print("\nNarratives:")
print(f"  Episodes processed: {meta_stats['narratives']['total_constructed']}")
print(f"  Recent: {meta_stats['narratives']['recent_narrative']}")
```

### Planning Statistics

```python
# Get strategic planner status
planner_status = orchestrator.strategic_planner.get_system_status()

print("Goals:")
print(f"  Total: {planner_status['goals']['total']}")
print(f"  In progress: {planner_status['goals']['in_progress']}")
print(f"  Completed: {planner_status['goals']['completed']}")

print("\nPlans:")
print(f"  Total: {planner_status['plans']['total']}")
print(f"  Active: {planner_status['plans']['active']}")

print("\nMilestones:")
print(f"  Achieved: {planner_status['milestones']['achieved']}/{planner_status['milestones']['total']}")

print("\nHypotheses:")
print(f"  Confirmed: {planner_status['hypotheses']['confirmed']}/{planner_status['hypotheses']['total']}")
```

### SCI Statistics

```python
# Get SCI system statistics
sci_stats = orchestrator.multi_stakeholder_sci.get_system_statistics()

print("Stakeholders:")
for role, count in sci_stats['stakeholders']['by_role'].items():
    print(f"  {role}: {count}")

print("\nDecisions:")
print(f"  Total: {sci_stats['decisions']['total']}")
print(f"  Approved: {sci_stats['decisions']['approved']}")
print(f"  Rejected: {sci_stats['decisions']['rejected']}")
print(f"  Approval rate: {sci_stats['consensus']['approval_rate']:.1f}%")
```

---

## 🎓 Best Practices

### 1. **Enable All Systems for Maximum Autonomy**

```yaml
# config/hlcs.yaml
meta_consciousness:
  enabled: true
  strategy: "adaptive"

strategic_planning:
  enabled: true

multi_stakeholder_sci:
  enabled: true
  consensus_type: "weighted"
```

### 2. **Register Stakeholders Early**

```python
# Register user as primary stakeholder
user_id = sci.register_stakeholder(
    name=current_user.name,
    role=StakeholderRole.PRIMARY_USER,
    verified=True
)

# Pass user_id to orchestrator for SCI decisions
result = await orchestrator.process(
    query=user_query,
    user_id=user_id,
    session_id=session_id
)
```

### 3. **Use Planning for Complex Multi-Step Tasks**

```python
# Instead of one big query, create a goal
goal = planner.goal_manager.create_goal(
    title="Build complete auth system",
    description="JWT + refresh tokens + protected routes",
    priority=GoalPriority.HIGH
)

# Let planner decompose and execute
plan = planner.plan_executor.create_plan_for_goal(goal.id)
result = await planner.plan_executor.execute_plan(plan.id, step_executor)
```

### 4. **Monitor Meta-Statistics**

```python
# Periodically check meta-cognitive health
meta_stats = meta.get_meta_statistics()

if meta_stats['temporal']['context_freshness'] < 0.3:
    logger.warning("Context is stale, consider refreshing")

if meta_stats['performance']['avg_quality_score'] < 0.6:
    logger.warning("Quality is dropping, investigate")
```

### 5. **Use Adaptive Strategies**

```python
# Let systems adapt automatically
meta = create_meta_consciousness(strategy="adaptive")  # Adapts to context
sci = create_multi_stakeholder_sci(consensus_type="adaptive")  # Adapts to criticality
```

---

## 🚀 Quick Start

### Minimal Setup

```python
from hlcs.orchestrator import HLCSOrchestrator
from hlcs.metacognition import create_meta_consciousness
from hlcs.planning import create_strategic_planner
from hlcs.sci import create_multi_stakeholder_sci, StakeholderRole
from hlcs.mcp_client import SARAiMCPClient
from hlcs.agi_system import Phi4MiniAGI

async def create_autonomous_hlcs():
    """Create fully autonomous HLCS system."""
    
    # Initialize components
    sarai = SARAiMCPClient("http://localhost:3000")
    agi = Phi4MiniAGI(model_path="./models/phi4_mini_q4.gguf")
    meta = create_meta_consciousness(strategy="adaptive")
    planner = create_strategic_planner()
    sci = create_multi_stakeholder_sci(consensus_type="weighted")
    
    # Register default agent
    sci.register_stakeholder("HLCS_Agent", StakeholderRole.AUTONOMOUS_AGENT, verified=True)
    
    # Create orchestrator
    orchestrator = HLCSOrchestrator(
        sarai_client=sarai,
        agi_system=agi,
        enable_agi=True,
        meta_consciousness=meta,
        enable_meta=True,
        strategic_planner=planner,
        enable_planning=True,
        multi_stakeholder_sci=sci,
        enable_sci=True
    )
    
    return orchestrator

# Use it
orchestrator = await create_autonomous_hlcs()
result = await orchestrator.process("Create API with JWT auth")
```

### REST API Usage

```bash
# Start server (automatically initializes all systems)
python -m hlcs.rest_gateway.server

# Use autonomous processing
curl -X POST http://localhost:4001/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Create REST API with JWT authentication",
    "user_id": "user-123",
    "session_id": "session-456"
  }'
```

---

## 📝 Configuration Reference

Complete `config/hlcs.yaml`:

```yaml
# Meta-Consciousness Layer
meta_consciousness:
  enabled: true
  strategy: "adaptive"  # conservative, exploratory, balanced, adaptive
  confidence_threshold: 0.7
  ignorance:
    enabled: true
    track_history: true
  narrative:
    enabled: true
    max_narratives: 10

# Strategic Planning System
strategic_planning:
  enabled: true
  goals:
    max_hierarchy_depth: 5
    auto_progress_tracking: true
  plans:
    default_decomposition: "sequential"
    auto_retry_failed_steps: true
  scenarios:
    enabled: true
    max_simulations_per_decision: 5
  hypotheses:
    enabled: true
    auto_testing: false

# Multi-Stakeholder SCI
multi_stakeholder_sci:
  enabled: true
  consensus_type: "weighted"  # weighted, simple_majority, supermajority, unanimous, adaptive
  timeout_minutes: 30.0
  role_weights:
    primary_user: 0.60
    administrator: 0.30
    autonomous_agent: 0.10
    observer: 0.00
  agents:
    auto_vote: true
    follow_recommendations: true
  conflict_resolution:
    defer_to_primary: true
    fallback: "sarai_mcp"
```

---

## 🔬 Testing

Run comprehensive tests:

```bash
# Test meta-consciousness
pytest tests/test_meta_consciousness.py -v

# Test strategic planning
pytest tests/test_strategic_planner.py -v

# Test multi-stakeholder SCI
pytest tests/test_multi_stakeholder.py -v

# Integration tests
pytest tests/test_autonomous_integration.py -v

# Full test suite
make test
```

---

## 📚 Additional Resources

- **Architecture Docs**: See `README.md` for system architecture
- **MCP Integration**: See `docs/INTEGRACION_SARAI_MCP.md`
- **AGI System**: See `docs/AGI_INTEGRATION_COMPLETE.md`
- **Quick Start**: See `QUICKSTART.md`

---

## 🎯 Summary

**HLCS v3.0** es un sistema verdaderamente autónomo que:

✅ **Piensa antes de actuar** (Meta-Consciousness)  
✅ **Planifica estratégicamente** (Strategic Planning)  
✅ **Decide consensuadamente** (Multi-Stakeholder SCI)  
✅ **Aprende de la experiencia** (Episodic Memory + Narratives)  
✅ **Se adapta al contexto** (Adaptive Strategies)  
✅ **Conoce sus limitaciones** (Ignorance Consciousness)

**El objetivo**: Un sistema que usa SARAi, SAUL y todos los componentes del ecosistema **en base a sus propios intereses** y análisis estratégico, no por reglas fijas.

---

**Version**: 3.0.0  
**Last Updated**: 7 de noviembre de 2025  
**Status**: Production Ready ✅
