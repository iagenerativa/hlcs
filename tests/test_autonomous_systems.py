"""
Test autonomous systems imports and basic initialization.

Tests that all v3.0 autonomous components can be imported and initialized.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest


def test_meta_consciousness_import():
    """Test Meta-Consciousness Layer imports."""
    from hlcs.metacognition import (
        MetaConsciousnessLayer,
        IgnoranceConsciousness,
        NarrativeConsciousness,
        DecisionStrategy,
        IgnoranceType,
        create_meta_consciousness
    )
    
    # Test creation
    meta = create_meta_consciousness(strategy="adaptive", confidence_threshold=0.7)
    assert meta is not None
    assert isinstance(meta, MetaConsciousnessLayer)
    assert meta.decision_strategy == DecisionStrategy.ADAPTIVE


def test_strategic_planning_import():
    """Test Strategic Planning System imports."""
    from hlcs.planning import (
        StrategicPlanningSystem,
        GoalManager,
        PlanExecutor,
        ProgressTracker,
        ScenarioSimulator,
        HypothesisTester,
        GoalPriority,
        GoalStatus,
        create_strategic_planner
    )
    
    # Test creation
    planner = create_strategic_planner()
    assert planner is not None
    assert isinstance(planner, StrategicPlanningSystem)
    assert planner.goal_manager is not None


def test_multi_stakeholder_sci_import():
    """Test Multi-Stakeholder SCI imports."""
    from hlcs.sci import (
        MultiStakeholderSCI,
        VotingStrategy,
        ConsensusBuilder,
        StakeholderRole,
        VoteChoice,
        ConsensusType,
        create_multi_stakeholder_sci
    )
    
    # Test creation
    sci = create_multi_stakeholder_sci(consensus_type="weighted", timeout_minutes=30.0)
    assert sci is not None
    assert isinstance(sci, MultiStakeholderSCI)
    assert sci.voting_strategy.consensus_type == ConsensusType.WEIGHTED


def test_meta_consciousness_workflow():
    """Test basic Meta-Consciousness workflow."""
    from hlcs.metacognition import create_meta_consciousness
    
    meta = create_meta_consciousness(strategy="adaptive")
    
    # Analyze query context
    meta_state = meta.analyze_query_context(
        query="Create a REST API with JWT authentication",
        context={"user_history": [], "memory_episodes": []},
        available_components=["sarai_mcp", "phi4mini_agi"]
    )
    
    assert meta_state is not None
    assert meta_state.self_doubt is not None
    assert meta_state.ignorance_score is not None
    assert meta_state.temporal_context is not None
    
    # Get composite confidence
    confidence = meta_state.self_doubt.get_composite_confidence()
    assert 0.0 <= confidence <= 1.0
    
    # Decide routing
    routing = meta.decide_component_routing(
        meta_state,
        {
            "sarai_mcp": {"available": True},
            "phi4mini_agi": {"available": True}
        }
    )
    
    assert routing["primary_component"] in ["sarai_mcp", "phi4mini_agi", "ensemble"]
    assert "reasoning" in routing


def test_strategic_planning_workflow():
    """Test basic Strategic Planning workflow."""
    from hlcs.planning import create_strategic_planner, GoalPriority
    
    planner = create_strategic_planner()
    
    # Create a goal
    goal = planner.goal_manager.create_goal(
        title="Test Goal",
        description="Test goal for unit testing",
        priority=GoalPriority.HIGH
    )
    
    assert goal is not None
    assert goal.title == "Test Goal"
    assert goal.priority == GoalPriority.HIGH
    
    # Create a plan
    plan = planner.plan_executor.create_plan_for_goal(
        goal_id=goal.id,
        decomposition_strategy="sequential"
    )
    
    assert plan is not None
    assert plan.goal_id == goal.id
    assert len(plan.steps) > 0


def test_multi_stakeholder_sci_workflow():
    """Test basic Multi-Stakeholder SCI workflow."""
    from hlcs.sci import create_multi_stakeholder_sci, StakeholderRole, VoteChoice
    
    sci = create_multi_stakeholder_sci(consensus_type="weighted")
    
    # Register stakeholders
    user_id = sci.register_stakeholder(
        name="Test User",
        role=StakeholderRole.PRIMARY_USER,
        verified=True
    )
    
    agent_id = sci.register_stakeholder(
        name="Test Agent",
        role=StakeholderRole.AUTONOMOUS_AGENT,
        verified=True
    )
    
    assert user_id in sci.stakeholders
    assert agent_id in sci.stakeholders
    
    # Create decision
    decision = sci.create_decision(
        title="Test Decision",
        description="Test decision for unit testing",
        decision_type="test",
        criticality=0.5
    )
    
    assert decision is not None
    
    # Cast votes
    sci.cast_vote(user_id, decision.decision_id, VoteChoice.APPROVE)
    sci.cast_vote(agent_id, decision.decision_id, VoteChoice.APPROVE)
    
    # Reach consensus
    consensus_reached, rationale = sci.reach_consensus(decision.decision_id)
    
    assert isinstance(consensus_reached, bool)
    assert isinstance(rationale, str)


def test_orchestrator_with_autonomous_systems():
    """Test orchestrator initialization with autonomous systems."""
    from hlcs.orchestrator import HLCSOrchestrator
    from hlcs.mcp_client import SARAiMCPClient
    from hlcs.metacognition import create_meta_consciousness
    from hlcs.planning import create_strategic_planner
    from hlcs.sci import create_multi_stakeholder_sci
    
    # Create systems
    meta = create_meta_consciousness(strategy="adaptive")
    planner = create_strategic_planner()
    sci = create_multi_stakeholder_sci(consensus_type="weighted")
    
    # Create mock SARAi client
    sarai = SARAiMCPClient("http://localhost:3000")
    
    # Create orchestrator with all systems
    orchestrator = HLCSOrchestrator(
        sarai_client=sarai,
        meta_consciousness=meta,
        enable_meta=True,
        strategic_planner=planner,
        enable_planning=True,
        multi_stakeholder_sci=sci,
        enable_sci=True
    )
    
    assert orchestrator.meta_consciousness is not None
    assert orchestrator.strategic_planner is not None
    assert orchestrator.multi_stakeholder_sci is not None
    assert orchestrator.enable_meta is True
    assert orchestrator.enable_planning is True
    assert orchestrator.enable_sci is True


def test_system_statistics():
    """Test that all systems provide statistics."""
    from hlcs.metacognition import create_meta_consciousness
    from hlcs.planning import create_strategic_planner
    from hlcs.sci import create_multi_stakeholder_sci
    
    meta = create_meta_consciousness()
    planner = create_strategic_planner()
    sci = create_multi_stakeholder_sci()
    
    # Meta-consciousness stats
    meta_stats = meta.get_meta_statistics()
    assert "temporal" in meta_stats
    assert "decisions" in meta_stats
    assert "performance" in meta_stats
    
    # Planning stats
    planner_stats = planner.get_system_status()
    assert "goals" in planner_stats
    assert "plans" in planner_stats
    assert "milestones" in planner_stats
    
    # SCI stats
    sci_stats = sci.get_system_statistics()
    assert "stakeholders" in sci_stats
    assert "decisions" in sci_stats
    assert "consensus" in sci_stats


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
