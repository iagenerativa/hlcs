"""
Strategic Planning System for HLCS v0.5

This module implements goal-oriented planning and execution capabilities:
1. GoalManager: Hierarchical goal tracking with priorities
2. PlanExecutor: Plan decomposition and step-by-step execution
3. ProgressTracker: Milestone tracking and progress monitoring
4. ScenarioSimulator: What-if analysis for decision support
5. HypothesisTester: Hypothesis validation through experimentation

The Strategic Planning System enables HLCS to:
- Set and track long-term goals
- Break down complex tasks into executable plans
- Monitor progress and adapt strategies
- Simulate outcomes before committing
- Learn from hypothesis testing
"""

import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class GoalStatus(Enum):
    """Status of a goal."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class GoalPriority(Enum):
    """Priority levels for goals."""
    CRITICAL = 4
    HIGH = 3
    MEDIUM = 2
    LOW = 1


class PlanStepStatus(Enum):
    """Status of a plan step."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class HypothesisOutcome(Enum):
    """Outcome of hypothesis testing."""
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    INCONCLUSIVE = "inconclusive"
    REQUIRES_MORE_DATA = "requires_more_data"


@dataclass
class Goal:
    """Represents a strategic goal."""
    id: str
    title: str
    description: str
    priority: GoalPriority
    status: GoalStatus = GoalStatus.PENDING
    parent_goal_id: Optional[str] = None  # For hierarchical goals
    subgoals: List[str] = field(default_factory=list)
    
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    deadline: Optional[datetime] = None
    
    success_criteria: List[str] = field(default_factory=list)
    required_resources: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    
    progress: float = 0.0  # 0.0 to 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_blocked(self, completed_goals: set) -> bool:
        """Check if goal is blocked by dependencies."""
        return not all(dep_id in completed_goals for dep_id in self.dependencies)
    
    def is_overdue(self) -> bool:
        """Check if goal is past deadline."""
        if self.deadline is None:
            return False
        return datetime.now() > self.deadline and self.status != GoalStatus.COMPLETED
    
    def update_progress(self, progress: float) -> None:
        """Update goal progress."""
        self.progress = max(0.0, min(1.0, progress))
        self.updated_at = datetime.now()
        
        # Auto-complete if progress reaches 100%
        if self.progress >= 1.0 and self.status != GoalStatus.COMPLETED:
            self.status = GoalStatus.COMPLETED


@dataclass
class PlanStep:
    """A single step in a plan."""
    id: str
    order: int
    description: str
    status: PlanStepStatus = PlanStepStatus.NOT_STARTED
    
    estimated_duration_minutes: float = 30.0
    actual_duration_minutes: Optional[float] = None
    
    required_tools: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)  # Other step IDs
    
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    result: Optional[Any] = None
    error: Optional[str] = None
    
    def can_execute(self, completed_steps: set) -> bool:
        """Check if step can be executed (dependencies met)."""
        return all(dep_id in completed_steps for dep_id in self.dependencies)
    
    def start(self) -> None:
        """Mark step as started."""
        self.status = PlanStepStatus.IN_PROGRESS
        self.start_time = datetime.now()
    
    def complete(self, result: Any = None) -> None:
        """Mark step as completed."""
        self.status = PlanStepStatus.COMPLETED
        self.end_time = datetime.now()
        self.result = result
        
        if self.start_time:
            duration = (self.end_time - self.start_time).total_seconds() / 60
            self.actual_duration_minutes = duration
    
    def fail(self, error: str) -> None:
        """Mark step as failed."""
        self.status = PlanStepStatus.FAILED
        self.end_time = datetime.now()
        self.error = error


@dataclass
class Plan:
    """A strategic plan consisting of ordered steps."""
    id: str
    goal_id: str
    title: str
    steps: List[PlanStep]
    
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    total_estimated_duration: float = 0.0
    actual_duration: Optional[float] = None
    
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_progress(self) -> float:
        """Calculate plan progress."""
        if not self.steps:
            return 0.0
        
        completed = sum(1 for s in self.steps if s.status == PlanStepStatus.COMPLETED)
        return completed / len(self.steps)
    
    def get_next_executable_step(self) -> Optional[PlanStep]:
        """Get the next step that can be executed."""
        completed_ids = {s.id for s in self.steps if s.status == PlanStepStatus.COMPLETED}
        
        for step in sorted(self.steps, key=lambda s: s.order):
            if step.status == PlanStepStatus.NOT_STARTED and step.can_execute(completed_ids):
                return step
        
        return None
    
    def is_complete(self) -> bool:
        """Check if all steps are completed."""
        return all(s.status == PlanStepStatus.COMPLETED for s in self.steps)
    
    def has_failures(self) -> bool:
        """Check if any step failed."""
        return any(s.status == PlanStepStatus.FAILED for s in self.steps)


@dataclass
class Milestone:
    """A tracking milestone for progress monitoring."""
    id: str
    goal_id: str
    title: str
    target_date: datetime
    criteria: List[str]
    
    achieved: bool = False
    achieved_at: Optional[datetime] = None
    
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Scenario:
    """A what-if scenario for simulation."""
    id: str
    title: str
    description: str
    
    assumptions: Dict[str, Any]
    predicted_outcomes: List[str]
    confidence: float  # 0.0 to 1.0
    
    created_at: datetime = field(default_factory=datetime.now)
    
    simulation_results: Optional[Dict[str, Any]] = None


@dataclass
class Hypothesis:
    """A testable hypothesis."""
    id: str
    statement: str
    rationale: str
    
    test_procedure: List[str]
    success_criteria: List[str]
    
    outcome: Optional[HypothesisOutcome] = None
    evidence: List[str] = field(default_factory=list)
    confidence: float = 0.5  # Prior confidence
    
    tested_at: Optional[datetime] = None
    test_duration_minutes: Optional[float] = None


class GoalManager:
    """
    Manages hierarchical goals with priorities and dependencies.
    """
    
    def __init__(self):
        self.goals: Dict[str, Goal] = {}
        self.completed_goals: set = set()
        
    def create_goal(
        self,
        title: str,
        description: str,
        priority: GoalPriority,
        parent_goal_id: Optional[str] = None,
        deadline: Optional[datetime] = None,
        success_criteria: Optional[List[str]] = None,
        dependencies: Optional[List[str]] = None
    ) -> Goal:
        """Create a new goal."""
        goal_id = str(uuid.uuid4())
        
        goal = Goal(
            id=goal_id,
            title=title,
            description=description,
            priority=priority,
            parent_goal_id=parent_goal_id,
            deadline=deadline,
            success_criteria=success_criteria or [],
            dependencies=dependencies or []
        )
        
        self.goals[goal_id] = goal
        
        # Add to parent's subgoals
        if parent_goal_id and parent_goal_id in self.goals:
            self.goals[parent_goal_id].subgoals.append(goal_id)
        
        logger.info(f"Created goal: {title} (priority={priority.name})")
        return goal
    
    def get_goal(self, goal_id: str) -> Optional[Goal]:
        """Retrieve a goal by ID."""
        return self.goals.get(goal_id)
    
    def update_goal_status(self, goal_id: str, status: GoalStatus) -> None:
        """Update goal status."""
        if goal_id in self.goals:
            goal = self.goals[goal_id]
            old_status = goal.status
            goal.status = status
            goal.updated_at = datetime.now()
            
            if status == GoalStatus.COMPLETED:
                self.completed_goals.add(goal_id)
                # Update parent progress
                self._update_parent_progress(goal_id)
            
            logger.info(f"Goal {goal.title}: {old_status.value} → {status.value}")
    
    def _update_parent_progress(self, goal_id: str) -> None:
        """Update parent goal progress based on subgoals."""
        goal = self.goals.get(goal_id)
        if not goal or not goal.parent_goal_id:
            return
        
        parent = self.goals.get(goal.parent_goal_id)
        if not parent or not parent.subgoals:
            return
        
        # Calculate parent progress from subgoals
        subgoal_progress = [
            self.goals[sg_id].progress 
            for sg_id in parent.subgoals 
            if sg_id in self.goals
        ]
        
        if subgoal_progress:
            avg_progress = sum(subgoal_progress) / len(subgoal_progress)
            parent.update_progress(avg_progress)
    
    def get_prioritized_goals(
        self,
        status_filter: Optional[List[GoalStatus]] = None
    ) -> List[Goal]:
        """Get goals sorted by priority."""
        goals = list(self.goals.values())
        
        if status_filter:
            goals = [g for g in goals if g.status in status_filter]
        
        # Sort by priority (descending), then by deadline
        goals.sort(
            key=lambda g: (
                -g.priority.value,
                g.deadline if g.deadline else datetime.max
            )
        )
        
        return goals
    
    def get_executable_goals(self) -> List[Goal]:
        """Get goals that can be started (dependencies met)."""
        pending_goals = [
            g for g in self.goals.values()
            if g.status == GoalStatus.PENDING
        ]
        
        return [g for g in pending_goals if not g.is_blocked(self.completed_goals)]
    
    def get_goal_tree(self, root_goal_id: str, depth: int = 0) -> str:
        """Generate a visual tree of goals."""
        goal = self.goals.get(root_goal_id)
        if not goal:
            return ""
        
        indent = "  " * depth
        status_icon = {
            GoalStatus.PENDING: "⏸",
            GoalStatus.IN_PROGRESS: "▶",
            GoalStatus.COMPLETED: "✓",
            GoalStatus.FAILED: "✗",
            GoalStatus.PAUSED: "⏸",
            GoalStatus.CANCELLED: "⊗"
        }.get(goal.status, "?")
        
        tree = f"{indent}{status_icon} {goal.title} ({goal.progress*100:.0f}%)\n"
        
        for subgoal_id in goal.subgoals:
            tree += self.get_goal_tree(subgoal_id, depth + 1)
        
        return tree


class PlanExecutor:
    """
    Decomposes goals into plans and executes them step-by-step.
    """
    
    def __init__(self, goal_manager: GoalManager):
        self.goal_manager = goal_manager
        self.plans: Dict[str, Plan] = {}
        self.active_plan_id: Optional[str] = None
        
    def create_plan_for_goal(
        self,
        goal_id: str,
        decomposition_strategy: str = "sequential"
    ) -> Plan:
        """
        Create an execution plan for a goal.
        
        Args:
            goal_id: ID of the goal to plan for
            decomposition_strategy: "sequential", "parallel", or "hybrid"
        """
        goal = self.goal_manager.get_goal(goal_id)
        if not goal:
            raise ValueError(f"Goal {goal_id} not found")
        
        plan_id = str(uuid.uuid4())
        steps = self._decompose_goal_into_steps(goal, decomposition_strategy)
        
        total_duration = sum(s.estimated_duration_minutes for s in steps)
        
        plan = Plan(
            id=plan_id,
            goal_id=goal_id,
            title=f"Plan for: {goal.title}",
            steps=steps,
            total_estimated_duration=total_duration
        )
        
        self.plans[plan_id] = plan
        logger.info(f"Created plan with {len(steps)} steps (est. {total_duration:.0f} min)")
        
        return plan
    
    def _decompose_goal_into_steps(
        self,
        goal: Goal,
        strategy: str
    ) -> List[PlanStep]:
        """Decompose a goal into executable steps."""
        steps = []
        
        # Simple heuristic decomposition based on goal characteristics
        if "implement" in goal.description.lower() or "create" in goal.description.lower():
            steps = self._create_implementation_steps(goal)
        elif "analyze" in goal.description.lower():
            steps = self._create_analysis_steps(goal)
        elif "debug" in goal.description.lower() or "fix" in goal.description.lower():
            steps = self._create_debugging_steps(goal)
        else:
            steps = self._create_generic_steps(goal)
        
        # Assign order
        for i, step in enumerate(steps):
            step.order = i
        
        return steps
    
    def _create_implementation_steps(self, goal: Goal) -> List[PlanStep]:
        """Create steps for implementation goals."""
        return [
            PlanStep(
                id=str(uuid.uuid4()),
                order=0,
                description="Research and gather requirements",
                estimated_duration_minutes=15,
                required_tools=["rag.search", "saul.synthesize"]
            ),
            PlanStep(
                id=str(uuid.uuid4()),
                order=1,
                description="Design solution architecture",
                estimated_duration_minutes=20,
                required_tools=["phi4mini_agi"]
            ),
            PlanStep(
                id=str(uuid.uuid4()),
                order=2,
                description="Implement core functionality",
                estimated_duration_minutes=45,
                required_tools=["code_agent", "phi4mini_agi"]
            ),
            PlanStep(
                id=str(uuid.uuid4()),
                order=3,
                description="Test and validate",
                estimated_duration_minutes=20,
                required_tools=["code_agent"]
            ),
            PlanStep(
                id=str(uuid.uuid4()),
                order=4,
                description="Document and finalize",
                estimated_duration_minutes=15,
                required_tools=["saul.synthesize"]
            )
        ]
    
    def _create_analysis_steps(self, goal: Goal) -> List[PlanStep]:
        """Create steps for analysis goals."""
        return [
            PlanStep(
                id=str(uuid.uuid4()),
                order=0,
                description="Gather relevant data",
                estimated_duration_minutes=10,
                required_tools=["rag.search"]
            ),
            PlanStep(
                id=str(uuid.uuid4()),
                order=1,
                description="Perform analysis",
                estimated_duration_minutes=30,
                required_tools=["phi4mini_agi", "saul.respond"]
            ),
            PlanStep(
                id=str(uuid.uuid4()),
                order=2,
                description="Synthesize insights",
                estimated_duration_minutes=20,
                required_tools=["saul.synthesize"]
            )
        ]
    
    def _create_debugging_steps(self, goal: Goal) -> List[PlanStep]:
        """Create steps for debugging goals."""
        return [
            PlanStep(
                id=str(uuid.uuid4()),
                order=0,
                description="Reproduce and identify issue",
                estimated_duration_minutes=15,
                required_tools=["code_agent"]
            ),
            PlanStep(
                id=str(uuid.uuid4()),
                order=1,
                description="Analyze root cause",
                estimated_duration_minutes=25,
                required_tools=["phi4mini_agi", "rag.search"]
            ),
            PlanStep(
                id=str(uuid.uuid4()),
                order=2,
                description="Implement fix",
                estimated_duration_minutes=30,
                required_tools=["code_agent"]
            ),
            PlanStep(
                id=str(uuid.uuid4()),
                order=3,
                description="Verify fix",
                estimated_duration_minutes=15,
                required_tools=["code_agent"]
            )
        ]
    
    def _create_generic_steps(self, goal: Goal) -> List[PlanStep]:
        """Create generic steps."""
        return [
            PlanStep(
                id=str(uuid.uuid4()),
                order=0,
                description="Understand requirements",
                estimated_duration_minutes=10,
                required_tools=["saul.respond"]
            ),
            PlanStep(
                id=str(uuid.uuid4()),
                order=1,
                description="Execute main task",
                estimated_duration_minutes=30,
                required_tools=["phi4mini_agi"]
            ),
            PlanStep(
                id=str(uuid.uuid4()),
                order=2,
                description="Review and finalize",
                estimated_duration_minutes=10,
                required_tools=["saul.synthesize"]
            )
        ]
    
    async def execute_plan(
        self,
        plan_id: str,
        executor_callback: Callable[[PlanStep], Any]
    ) -> Dict[str, Any]:
        """
        Execute a plan step-by-step.
        
        Args:
            plan_id: ID of the plan to execute
            executor_callback: Async function to execute each step
            
        Returns:
            Execution results summary
        """
        plan = self.plans.get(plan_id)
        if not plan:
            raise ValueError(f"Plan {plan_id} not found")
        
        self.active_plan_id = plan_id
        plan.started_at = datetime.now()
        
        logger.info(f"Starting plan execution: {plan.title}")
        
        results = {
            "plan_id": plan_id,
            "steps_executed": 0,
            "steps_succeeded": 0,
            "steps_failed": 0,
            "total_duration_minutes": 0.0,
            "step_results": []
        }
        
        while True:
            next_step = plan.get_next_executable_step()
            
            if next_step is None:
                if plan.is_complete():
                    logger.info("Plan execution completed successfully")
                    break
                elif plan.has_failures():
                    logger.warning("Plan execution stopped due to failures")
                    break
                else:
                    logger.warning("Plan execution blocked (no executable steps)")
                    break
            
            # Execute step
            logger.info(f"Executing step {next_step.order + 1}: {next_step.description}")
            next_step.start()
            
            try:
                result = await executor_callback(next_step)
                next_step.complete(result)
                results["steps_succeeded"] += 1
                
                step_result = {
                    "step_id": next_step.id,
                    "description": next_step.description,
                    "status": "success",
                    "duration_minutes": next_step.actual_duration_minutes,
                    "result": str(result)[:200] if result else None
                }
                
            except Exception as e:
                error_msg = str(e)
                next_step.fail(error_msg)
                results["steps_failed"] += 1
                
                step_result = {
                    "step_id": next_step.id,
                    "description": next_step.description,
                    "status": "failed",
                    "error": error_msg
                }
                
                logger.error(f"Step failed: {error_msg}")
            
            results["steps_executed"] += 1
            results["step_results"].append(step_result)
        
        plan.completed_at = datetime.now()
        if plan.started_at:
            duration = (plan.completed_at - plan.started_at).total_seconds() / 60
            plan.actual_duration = duration
            results["total_duration_minutes"] = duration
        
        # Update goal progress
        goal = self.goal_manager.get_goal(plan.goal_id)
        if goal:
            goal.update_progress(plan.get_progress())
            
            if plan.is_complete():
                self.goal_manager.update_goal_status(plan.goal_id, GoalStatus.COMPLETED)
            elif plan.has_failures():
                self.goal_manager.update_goal_status(plan.goal_id, GoalStatus.FAILED)
        
        self.active_plan_id = None
        return results


class ProgressTracker:
    """
    Tracks progress towards goals via milestones.
    """
    
    def __init__(self, goal_manager: GoalManager):
        self.goal_manager = goal_manager
        self.milestones: Dict[str, Milestone] = {}
        
    def create_milestone(
        self,
        goal_id: str,
        title: str,
        target_date: datetime,
        criteria: List[str]
    ) -> Milestone:
        """Create a tracking milestone."""
        milestone_id = str(uuid.uuid4())
        
        milestone = Milestone(
            id=milestone_id,
            goal_id=goal_id,
            title=title,
            target_date=target_date,
            criteria=criteria
        )
        
        self.milestones[milestone_id] = milestone
        logger.info(f"Created milestone: {title} (target: {target_date.strftime('%Y-%m-%d')})")
        
        return milestone
    
    def check_milestone(self, milestone_id: str, context: Dict[str, Any]) -> bool:
        """Check if a milestone has been achieved."""
        milestone = self.milestones.get(milestone_id)
        if not milestone or milestone.achieved:
            return milestone.achieved if milestone else False
        
        # Simple heuristic checking (in real implementation, would be more sophisticated)
        criteria_met = 0
        for criterion in milestone.criteria:
            # Check if criterion appears in context or goal status
            if any(criterion.lower() in str(v).lower() for v in context.values()):
                criteria_met += 1
        
        threshold = len(milestone.criteria) * 0.7  # 70% criteria must be met
        
        if criteria_met >= threshold:
            milestone.achieved = True
            milestone.achieved_at = datetime.now()
            logger.info(f"Milestone achieved: {milestone.title}")
            return True
        
        return False
    
    def get_progress_report(self, goal_id: str) -> Dict[str, Any]:
        """Generate a progress report for a goal."""
        goal = self.goal_manager.get_goal(goal_id)
        if not goal:
            return {}
        
        goal_milestones = [
            m for m in self.milestones.values()
            if m.goal_id == goal_id
        ]
        
        achieved = [m for m in goal_milestones if m.achieved]
        pending = [m for m in goal_milestones if not m.achieved]
        overdue = [m for m in pending if m.target_date < datetime.now()]
        
        return {
            "goal_id": goal_id,
            "goal_title": goal.title,
            "goal_status": goal.status.value,
            "goal_progress": goal.progress,
            "milestones": {
                "total": len(goal_milestones),
                "achieved": len(achieved),
                "pending": len(pending),
                "overdue": len(overdue)
            },
            "is_on_track": len(overdue) == 0 and goal.progress >= 0.5
        }


class ScenarioSimulator:
    """
    Simulates what-if scenarios for decision support.
    """
    
    def __init__(self):
        self.scenarios: Dict[str, Scenario] = {}
        
    def create_scenario(
        self,
        title: str,
        description: str,
        assumptions: Dict[str, Any]
    ) -> Scenario:
        """Create a new scenario."""
        scenario_id = str(uuid.uuid4())
        
        scenario = Scenario(
            id=scenario_id,
            title=title,
            description=description,
            assumptions=assumptions,
            predicted_outcomes=[],
            confidence=0.5
        )
        
        self.scenarios[scenario_id] = scenario
        logger.info(f"Created scenario: {title}")
        
        return scenario
    
    def simulate(
        self,
        scenario_id: str,
        simulation_function: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Run a scenario simulation.
        
        Args:
            scenario_id: ID of scenario to simulate
            simulation_function: Optional custom simulation logic
            
        Returns:
            Simulation results
        """
        scenario = self.scenarios.get(scenario_id)
        if not scenario:
            raise ValueError(f"Scenario {scenario_id} not found")
        
        logger.info(f"Simulating scenario: {scenario.title}")
        
        if simulation_function:
            results = simulation_function(scenario)
        else:
            # Default simple simulation
            results = self._default_simulation(scenario)
        
        scenario.simulation_results = results
        
        return results
    
    def _default_simulation(self, scenario: Scenario) -> Dict[str, Any]:
        """Default simulation logic (heuristic-based)."""
        
        # Extract key assumptions
        complexity = scenario.assumptions.get("complexity", "medium")
        resources = scenario.assumptions.get("available_resources", [])
        constraints = scenario.assumptions.get("constraints", [])
        
        # Estimate outcomes
        success_probability = 0.7  # Base
        
        if complexity == "high":
            success_probability -= 0.2
        elif complexity == "low":
            success_probability += 0.1
        
        if len(resources) < 2:
            success_probability -= 0.15
        
        if len(constraints) > 3:
            success_probability -= 0.1
        
        success_probability = max(0.1, min(0.95, success_probability))
        
        return {
            "success_probability": success_probability,
            "estimated_duration": scenario.assumptions.get("estimated_duration", "unknown"),
            "risk_factors": constraints,
            "recommended_approach": "adaptive" if success_probability < 0.6 else "direct",
            "confidence": success_probability
        }
    
    def compare_scenarios(self, scenario_ids: List[str]) -> List[Dict[str, Any]]:
        """Compare multiple scenarios."""
        comparisons = []
        
        for sid in scenario_ids:
            scenario = self.scenarios.get(sid)
            if not scenario or not scenario.simulation_results:
                continue
            
            comparisons.append({
                "scenario_id": sid,
                "title": scenario.title,
                "success_probability": scenario.simulation_results.get("success_probability", 0),
                "confidence": scenario.confidence
            })
        
        # Sort by success probability
        comparisons.sort(key=lambda x: x["success_probability"], reverse=True)
        
        return comparisons


class HypothesisTester:
    """
    Tests hypotheses through experimentation.
    """
    
    def __init__(self):
        self.hypotheses: Dict[str, Hypothesis] = {}
        
    def create_hypothesis(
        self,
        statement: str,
        rationale: str,
        test_procedure: List[str],
        success_criteria: List[str],
        prior_confidence: float = 0.5
    ) -> Hypothesis:
        """Create a testable hypothesis."""
        hypothesis_id = str(uuid.uuid4())
        
        hypothesis = Hypothesis(
            id=hypothesis_id,
            statement=statement,
            rationale=rationale,
            test_procedure=test_procedure,
            success_criteria=success_criteria,
            confidence=prior_confidence
        )
        
        self.hypotheses[hypothesis_id] = hypothesis
        logger.info(f"Created hypothesis: {statement}")
        
        return hypothesis
    
    async def test_hypothesis(
        self,
        hypothesis_id: str,
        test_executor: Callable
    ) -> HypothesisOutcome:
        """
        Test a hypothesis by executing the test procedure.
        
        Args:
            hypothesis_id: ID of hypothesis to test
            test_executor: Async function to execute tests
            
        Returns:
            Outcome of the test
        """
        hypothesis = self.hypotheses.get(hypothesis_id)
        if not hypothesis:
            raise ValueError(f"Hypothesis {hypothesis_id} not found")
        
        logger.info(f"Testing hypothesis: {hypothesis.statement}")
        start_time = time.time()
        
        hypothesis.tested_at = datetime.now()
        
        try:
            # Execute test procedure
            test_results = await test_executor(hypothesis.test_procedure)
            
            # Evaluate against success criteria
            criteria_met = 0
            for criterion in hypothesis.success_criteria:
                # Check if criterion is met in results
                if criterion.lower() in str(test_results).lower():
                    criteria_met += 1
                    hypothesis.evidence.append(f"Met: {criterion}")
                else:
                    hypothesis.evidence.append(f"Not met: {criterion}")
            
            # Determine outcome
            criteria_ratio = criteria_met / len(hypothesis.success_criteria)
            
            if criteria_ratio >= 0.8:
                outcome = HypothesisOutcome.CONFIRMED
                hypothesis.confidence = min(0.95, hypothesis.confidence + 0.3)
            elif criteria_ratio >= 0.4:
                outcome = HypothesisOutcome.INCONCLUSIVE
                hypothesis.confidence = hypothesis.confidence
            else:
                outcome = HypothesisOutcome.REJECTED
                hypothesis.confidence = max(0.05, hypothesis.confidence - 0.3)
            
        except Exception as e:
            logger.error(f"Hypothesis test failed: {e}")
            outcome = HypothesisOutcome.REQUIRES_MORE_DATA
            hypothesis.evidence.append(f"Test error: {str(e)}")
        
        hypothesis.outcome = outcome
        hypothesis.test_duration_minutes = (time.time() - start_time) / 60
        
        logger.info(f"Hypothesis outcome: {outcome.value} (confidence={hypothesis.confidence:.2f})")
        
        return outcome


class StrategicPlanningSystem:
    """
    Central strategic planning system that integrates all planning components.
    
    This enables HLCS to:
    - Set and manage hierarchical goals
    - Create and execute plans
    - Track progress via milestones
    - Simulate scenarios for decision-making
    - Test hypotheses to validate strategies
    """
    
    def __init__(self):
        self.goal_manager = GoalManager()
        self.plan_executor = PlanExecutor(self.goal_manager)
        self.progress_tracker = ProgressTracker(self.goal_manager)
        self.scenario_simulator = ScenarioSimulator()
        self.hypothesis_tester = HypothesisTester()
        
        logger.info("StrategicPlanningSystem initialized")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status."""
        all_goals = list(self.goal_manager.goals.values())
        
        return {
            "goals": {
                "total": len(all_goals),
                "pending": len([g for g in all_goals if g.status == GoalStatus.PENDING]),
                "in_progress": len([g for g in all_goals if g.status == GoalStatus.IN_PROGRESS]),
                "completed": len([g for g in all_goals if g.status == GoalStatus.COMPLETED]),
                "failed": len([g for g in all_goals if g.status == GoalStatus.FAILED])
            },
            "plans": {
                "total": len(self.plan_executor.plans),
                "active": self.plan_executor.active_plan_id is not None
            },
            "milestones": {
                "total": len(self.progress_tracker.milestones),
                "achieved": len([m for m in self.progress_tracker.milestones.values() if m.achieved])
            },
            "scenarios": len(self.scenario_simulator.scenarios),
            "hypotheses": {
                "total": len(self.hypothesis_tester.hypotheses),
                "confirmed": len([h for h in self.hypothesis_tester.hypotheses.values() if h.outcome == HypothesisOutcome.CONFIRMED])
            }
        }


# Factory function
def create_strategic_planner() -> StrategicPlanningSystem:
    """Create a StrategicPlanningSystem instance."""
    return StrategicPlanningSystem()
