"""
Multi-Stakeholder SCI (Smart Consensus Intelligence) for HLCS v0.4

This module implements a consensus-based decision system with multiple stakeholders:
1. MultiStakeholderSCI: Coordinate decisions across stakeholders
2. VotingStrategy: Flexible voting mechanisms (weighted, majority, unanimous)
3. ConsensusBuilder: Build consensus with configurable thresholds
4. StakeholderContext: Track stakeholder identity, preferences, and history

The SCI enables HLCS to make decisions that consider multiple perspectives:
- Primary user (60% weight)
- System administrator (30% weight)  
- Autonomous agents (10% weight)

This ensures balanced decision-making that respects both user intent and system health.
"""

import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class StakeholderRole(Enum):
    """Role types for stakeholders."""
    PRIMARY_USER = "primary_user"          # The main user (60% weight)
    ADMINISTRATOR = "administrator"         # System admin (30% weight)
    AUTONOMOUS_AGENT = "autonomous_agent"   # AI agents (10% weight)
    OBSERVER = "observer"                   # No voting power, observes only


class VoteChoice(Enum):
    """Vote options."""
    APPROVE = "approve"
    REJECT = "reject"
    ABSTAIN = "abstain"
    DELEGATE = "delegate"  # Delegate vote to another stakeholder


class ConsensusType(Enum):
    """Types of consensus mechanisms."""
    WEIGHTED = "weighted"          # Weighted by stakeholder role
    SIMPLE_MAJORITY = "simple_majority"  # >50% approval
    SUPERMAJORITY = "supermajority"      # ≥2/3 approval
    UNANIMOUS = "unanimous"        # All must approve
    ADAPTIVE = "adaptive"          # Adapt based on decision criticality


@dataclass
class StakeholderIdentity:
    """Identity and authentication info for a stakeholder."""
    stakeholder_id: str
    role: StakeholderRole
    name: str
    
    verified: bool = False
    verification_method: Optional[str] = None
    
    created_at: datetime = field(default_factory=datetime.now)
    last_active: datetime = field(default_factory=datetime.now)
    
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def update_activity(self) -> None:
        """Update last activity timestamp."""
        self.last_active = datetime.now()


@dataclass
class StakeholderPreferences:
    """Preferences and configuration for a stakeholder."""
    risk_tolerance: float = 0.5  # 0=risk-averse, 1=risk-seeking
    decision_speed: str = "balanced"  # "fast", "balanced", "thorough"
    
    preferred_components: List[str] = field(default_factory=list)
    trusted_agents: List[str] = field(default_factory=list)
    
    notification_settings: Dict[str, bool] = field(default_factory=dict)
    delegation_rules: Dict[str, str] = field(default_factory=dict)


@dataclass
class Vote:
    """A single vote from a stakeholder."""
    vote_id: str
    stakeholder_id: str
    decision_id: str
    
    choice: VoteChoice
    weight: float  # Voting weight based on role
    
    cast_at: datetime = field(default_factory=datetime.now)
    rationale: Optional[str] = None
    
    delegated_to: Optional[str] = None  # If vote is delegated
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Decision:
    """A decision requiring consensus."""
    decision_id: str
    title: str
    description: str
    
    decision_type: str  # "component_routing", "resource_allocation", "policy_change", etc.
    criticality: float  # 0=low, 1=critical
    
    created_at: datetime = field(default_factory=datetime.now)
    deadline: Optional[datetime] = None
    
    options: List[Dict[str, Any]] = field(default_factory=list)
    recommended_option: Optional[str] = None
    
    required_roles: List[StakeholderRole] = field(default_factory=list)
    
    votes: List[Vote] = field(default_factory=list)
    final_outcome: Optional[str] = None
    outcome_rationale: Optional[str] = None
    
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_vote(self, vote: Vote) -> None:
        """Add a vote to this decision."""
        # Remove any existing vote from this stakeholder
        self.votes = [v for v in self.votes if v.stakeholder_id != vote.stakeholder_id]
        self.votes.append(vote)
    
    def get_vote_summary(self) -> Dict[str, int]:
        """Get summary of votes."""
        summary = {
            "approve": 0,
            "reject": 0,
            "abstain": 0,
            "delegate": 0
        }
        
        for vote in self.votes:
            summary[vote.choice.value] += 1
        
        return summary
    
    def get_weighted_approval_rate(self) -> float:
        """Calculate weighted approval rate."""
        total_weight = sum(v.weight for v in self.votes if v.choice != VoteChoice.ABSTAIN)
        
        if total_weight == 0:
            return 0.0
        
        approve_weight = sum(v.weight for v in self.votes if v.choice == VoteChoice.APPROVE)
        
        return approve_weight / total_weight


@dataclass
class StakeholderContext:
    """Complete context for a stakeholder."""
    identity: StakeholderIdentity
    preferences: StakeholderPreferences
    
    decision_history: List[str] = field(default_factory=list)  # Decision IDs
    vote_count: int = 0
    agreement_rate: float = 1.0  # Rate of agreement with final outcomes
    
    def record_vote(self, decision_id: str) -> None:
        """Record that stakeholder voted on a decision."""
        self.decision_history.append(decision_id)
        self.vote_count += 1
        self.identity.update_activity()
        
        # Keep only last 100 decisions
        if len(self.decision_history) > 100:
            self.decision_history = self.decision_history[-100:]
    
    def update_agreement_rate(self, agreed: bool) -> None:
        """Update agreement rate based on whether stakeholder agreed with outcome."""
        # Exponential moving average
        alpha = 0.1
        self.agreement_rate = alpha * (1.0 if agreed else 0.0) + (1 - alpha) * self.agreement_rate


class VotingStrategy:
    """
    Implements various voting strategies for consensus building.
    """
    
    def __init__(self, consensus_type: ConsensusType = ConsensusType.WEIGHTED):
        self.consensus_type = consensus_type
        
        # Default weights by role (sums to 1.0)
        self.default_weights = {
            StakeholderRole.PRIMARY_USER: 0.60,
            StakeholderRole.ADMINISTRATOR: 0.30,
            StakeholderRole.AUTONOMOUS_AGENT: 0.10,
            StakeholderRole.OBSERVER: 0.00
        }
    
    def get_stakeholder_weight(self, role: StakeholderRole) -> float:
        """Get voting weight for a stakeholder role."""
        return self.default_weights.get(role, 0.0)
    
    def evaluate_consensus(
        self,
        decision: Decision,
        stakeholders: Dict[str, StakeholderContext]
    ) -> Tuple[bool, str]:
        """
        Evaluate if consensus has been reached.
        
        Args:
            decision: The decision to evaluate
            stakeholders: Dictionary of stakeholder contexts
            
        Returns:
            (consensus_reached, rationale) tuple
        """
        if self.consensus_type == ConsensusType.WEIGHTED:
            return self._evaluate_weighted_consensus(decision)
        elif self.consensus_type == ConsensusType.SIMPLE_MAJORITY:
            return self._evaluate_simple_majority(decision)
        elif self.consensus_type == ConsensusType.SUPERMAJORITY:
            return self._evaluate_supermajority(decision)
        elif self.consensus_type == ConsensusType.UNANIMOUS:
            return self._evaluate_unanimous(decision)
        else:  # ADAPTIVE
            return self._evaluate_adaptive_consensus(decision, stakeholders)
    
    def _evaluate_weighted_consensus(self, decision: Decision) -> Tuple[bool, str]:
        """Evaluate weighted consensus (default 60/30/10 split)."""
        approval_rate = decision.get_weighted_approval_rate()
        threshold = 0.6  # Need >60% weighted approval
        
        reached = approval_rate >= threshold
        rationale = f"Weighted approval: {approval_rate*100:.1f}% (threshold: {threshold*100:.0f}%)"
        
        return reached, rationale
    
    def _evaluate_simple_majority(self, decision: Decision) -> Tuple[bool, str]:
        """Evaluate simple majority (>50%)."""
        summary = decision.get_vote_summary()
        total = sum(summary.values()) - summary["abstain"]
        
        if total == 0:
            return False, "No votes cast"
        
        approval_rate = summary["approve"] / total
        reached = approval_rate > 0.5
        
        rationale = f"Simple majority: {approval_rate*100:.1f}% ({summary['approve']}/{total})"
        
        return reached, rationale
    
    def _evaluate_supermajority(self, decision: Decision) -> Tuple[bool, str]:
        """Evaluate supermajority (≥2/3)."""
        summary = decision.get_vote_summary()
        total = sum(summary.values()) - summary["abstain"]
        
        if total == 0:
            return False, "No votes cast"
        
        approval_rate = summary["approve"] / total
        threshold = 2/3
        reached = approval_rate >= threshold
        
        rationale = f"Supermajority: {approval_rate*100:.1f}% (threshold: {threshold*100:.0f}%)"
        
        return reached, rationale
    
    def _evaluate_unanimous(self, decision: Decision) -> Tuple[bool, str]:
        """Evaluate unanimous consensus."""
        summary = decision.get_vote_summary()
        
        if summary["reject"] > 0:
            return False, f"Rejected: {summary['reject']} votes against"
        
        if summary["approve"] == 0:
            return False, "No approval votes"
        
        # Unanimous if all non-abstaining votes are approve
        total_decisive = summary["approve"] + summary["reject"]
        reached = total_decisive > 0 and summary["reject"] == 0
        
        rationale = "Unanimous approval" if reached else "Not unanimous"
        
        return reached, rationale
    
    def _evaluate_adaptive_consensus(
        self,
        decision: Decision,
        stakeholders: Dict[str, StakeholderContext]
    ) -> Tuple[bool, str]:
        """Adapt consensus mechanism based on decision criticality."""
        criticality = decision.criticality
        
        if criticality >= 0.8:
            # High criticality: require supermajority
            return self._evaluate_supermajority(decision)
        elif criticality >= 0.5:
            # Medium criticality: weighted consensus
            return self._evaluate_weighted_consensus(decision)
        else:
            # Low criticality: simple majority
            return self._evaluate_simple_majority(decision)


class ConsensusBuilder:
    """
    Builds consensus by managing the voting process and resolving conflicts.
    """
    
    def __init__(
        self,
        voting_strategy: VotingStrategy,
        timeout_minutes: float = 30.0
    ):
        self.voting_strategy = voting_strategy
        self.timeout_minutes = timeout_minutes
        
    def solicit_votes(
        self,
        decision: Decision,
        stakeholders: Dict[str, StakeholderContext],
        auto_vote_agents: bool = True
    ) -> None:
        """
        Solicit votes from stakeholders.
        
        Args:
            decision: Decision to vote on
            stakeholders: Available stakeholders
            auto_vote_agents: Whether autonomous agents auto-vote
        """
        logger.info(f"Soliciting votes for decision: {decision.title}")
        
        # Filter stakeholders by required roles
        eligible_stakeholders = stakeholders
        if decision.required_roles:
            eligible_stakeholders = {
                sid: ctx for sid, ctx in stakeholders.items()
                if ctx.identity.role in decision.required_roles
            }
        
        # Auto-vote for autonomous agents if enabled
        if auto_vote_agents:
            for sid, ctx in eligible_stakeholders.items():
                if ctx.identity.role == StakeholderRole.AUTONOMOUS_AGENT:
                    # Agents vote based on recommendation and preferences
                    choice = self._agent_auto_vote(decision, ctx)
                    
                    vote = Vote(
                        vote_id=str(uuid.uuid4()),
                        stakeholder_id=sid,
                        decision_id=decision.decision_id,
                        choice=choice,
                        weight=self.voting_strategy.get_stakeholder_weight(ctx.identity.role),
                        rationale=f"Auto-vote based on system analysis"
                    )
                    
                    decision.add_vote(vote)
                    ctx.record_vote(decision.decision_id)
        
        logger.info(f"Collected {len(decision.votes)} votes")
    
    def _agent_auto_vote(
        self,
        decision: Decision,
        agent_context: StakeholderContext
    ) -> VoteChoice:
        """Determine how an autonomous agent should vote."""
        # Simple heuristic: follow recommendation if present
        if decision.recommended_option:
            return VoteChoice.APPROVE
        
        # Otherwise, approve if low criticality
        if decision.criticality < 0.5:
            return VoteChoice.APPROVE
        
        # For high criticality with no recommendation, abstain
        return VoteChoice.ABSTAIN
    
    def build_consensus(
        self,
        decision: Decision,
        stakeholders: Dict[str, StakeholderContext],
        wait_for_all: bool = False
    ) -> Tuple[bool, str]:
        """
        Build consensus for a decision.
        
        Args:
            decision: Decision to build consensus for
            stakeholders: Available stakeholders
            wait_for_all: Whether to wait for all stakeholders to vote
            
        Returns:
            (consensus_reached, outcome_rationale) tuple
        """
        start_time = time.time()
        
        # Solicit votes
        self.solicit_votes(decision, stakeholders)
        
        # Check if we have minimum participation
        if wait_for_all and len(decision.votes) < len(stakeholders):
            logger.warning(f"Waiting for all {len(stakeholders)} stakeholders to vote")
            # In real implementation, would wait asynchronously
        
        # Evaluate consensus
        consensus_reached, rationale = self.voting_strategy.evaluate_consensus(
            decision, stakeholders
        )
        
        # Finalize decision
        if consensus_reached:
            decision.final_outcome = "approved"
            decision.outcome_rationale = rationale
        else:
            decision.final_outcome = "rejected"
            decision.outcome_rationale = rationale
        
        # Update stakeholder agreement rates
        for vote in decision.votes:
            if vote.stakeholder_id in stakeholders:
                ctx = stakeholders[vote.stakeholder_id]
                approved_outcome = (vote.choice == VoteChoice.APPROVE and consensus_reached) or \
                                   (vote.choice == VoteChoice.REJECT and not consensus_reached)
                ctx.update_agreement_rate(approved_outcome)
        
        elapsed_minutes = (time.time() - start_time) / 60
        logger.info(
            f"Consensus {'reached' if consensus_reached else 'not reached'} "
            f"for '{decision.title}' in {elapsed_minutes:.2f} min"
        )
        
        return consensus_reached, rationale
    
    def resolve_conflict(
        self,
        decision: Decision,
        stakeholders: Dict[str, StakeholderContext]
    ) -> str:
        """
        Resolve conflicts when consensus cannot be reached.
        
        Returns:
            Resolution strategy
        """
        summary = decision.get_vote_summary()
        
        # If primary user voted, follow their choice
        primary_votes = [
            v for v in decision.votes
            if v.stakeholder_id in stakeholders
            and stakeholders[v.stakeholder_id].identity.role == StakeholderRole.PRIMARY_USER
        ]
        
        if primary_votes:
            primary_choice = primary_votes[0].choice
            if primary_choice != VoteChoice.ABSTAIN:
                return f"Defer to primary user vote: {primary_choice.value}"
        
        # If admin voted, follow their choice
        admin_votes = [
            v for v in decision.votes
            if v.stakeholder_id in stakeholders
            and stakeholders[v.stakeholder_id].identity.role == StakeholderRole.ADMINISTRATOR
        ]
        
        if admin_votes:
            admin_choice = admin_votes[0].choice
            if admin_choice != VoteChoice.ABSTAIN:
                return f"Defer to administrator vote: {admin_choice.value}"
        
        # Default: reject if no clear resolution
        return "Default to rejection due to lack of consensus"


class MultiStakeholderSCI:
    """
    Central Multi-Stakeholder Smart Consensus Intelligence system.
    
    Coordinates decision-making across multiple stakeholders with weighted voting.
    This ensures HLCS makes decisions that balance user intent, system health,
    and autonomous agent recommendations.
    """
    
    def __init__(
        self,
        consensus_type: ConsensusType = ConsensusType.WEIGHTED,
        decision_timeout_minutes: float = 30.0
    ):
        self.stakeholders: Dict[str, StakeholderContext] = {}
        
        self.voting_strategy = VotingStrategy(consensus_type)
        self.consensus_builder = ConsensusBuilder(
            self.voting_strategy,
            timeout_minutes=decision_timeout_minutes
        )
        
        self.decisions: Dict[str, Decision] = {}
        self.decision_history: List[str] = []
        
        logger.info(f"MultiStakeholderSCI initialized with {consensus_type.value} consensus")
    
    def register_stakeholder(
        self,
        name: str,
        role: StakeholderRole,
        verified: bool = False,
        preferences: Optional[StakeholderPreferences] = None
    ) -> str:
        """
        Register a new stakeholder.
        
        Args:
            name: Stakeholder name
            role: Stakeholder role
            verified: Whether identity is verified
            preferences: Optional preferences
            
        Returns:
            Stakeholder ID
        """
        stakeholder_id = str(uuid.uuid4())
        
        identity = StakeholderIdentity(
            stakeholder_id=stakeholder_id,
            role=role,
            name=name,
            verified=verified
        )
        
        context = StakeholderContext(
            identity=identity,
            preferences=preferences or StakeholderPreferences()
        )
        
        self.stakeholders[stakeholder_id] = context
        logger.info(f"Registered stakeholder: {name} ({role.value})")
        
        return stakeholder_id
    
    def create_decision(
        self,
        title: str,
        description: str,
        decision_type: str,
        criticality: float = 0.5,
        options: Optional[List[Dict[str, Any]]] = None,
        recommended_option: Optional[str] = None,
        required_roles: Optional[List[StakeholderRole]] = None,
        deadline: Optional[datetime] = None
    ) -> Decision:
        """
        Create a decision requiring consensus.
        
        Args:
            title: Decision title
            description: Decision description
            decision_type: Type of decision
            criticality: How critical (0-1)
            options: Available options
            recommended_option: System recommendation
            required_roles: Roles required to vote
            deadline: Voting deadline
            
        Returns:
            Created Decision object
        """
        decision_id = str(uuid.uuid4())
        
        decision = Decision(
            decision_id=decision_id,
            title=title,
            description=description,
            decision_type=decision_type,
            criticality=criticality,
            options=options or [],
            recommended_option=recommended_option,
            required_roles=required_roles or [],
            deadline=deadline
        )
        
        self.decisions[decision_id] = decision
        logger.info(f"Created decision: {title} (criticality={criticality:.2f})")
        
        return decision
    
    def cast_vote(
        self,
        stakeholder_id: str,
        decision_id: str,
        choice: VoteChoice,
        rationale: Optional[str] = None
    ) -> Vote:
        """
        Cast a vote for a decision.
        
        Args:
            stakeholder_id: ID of voting stakeholder
            decision_id: ID of decision
            choice: Vote choice
            rationale: Optional rationale
            
        Returns:
            Created Vote object
        """
        if stakeholder_id not in self.stakeholders:
            raise ValueError(f"Stakeholder {stakeholder_id} not found")
        
        if decision_id not in self.decisions:
            raise ValueError(f"Decision {decision_id} not found")
        
        stakeholder = self.stakeholders[stakeholder_id]
        decision = self.decisions[decision_id]
        
        vote = Vote(
            vote_id=str(uuid.uuid4()),
            stakeholder_id=stakeholder_id,
            decision_id=decision_id,
            choice=choice,
            weight=self.voting_strategy.get_stakeholder_weight(stakeholder.identity.role),
            rationale=rationale
        )
        
        decision.add_vote(vote)
        stakeholder.record_vote(decision_id)
        
        logger.info(
            f"Vote cast: {stakeholder.identity.name} → {choice.value} "
            f"on '{decision.title}' (weight={vote.weight:.2f})"
        )
        
        return vote
    
    def reach_consensus(
        self,
        decision_id: str,
        wait_for_all: bool = False
    ) -> Tuple[bool, str]:
        """
        Attempt to reach consensus on a decision.
        
        Args:
            decision_id: ID of decision
            wait_for_all: Whether to wait for all stakeholders
            
        Returns:
            (consensus_reached, outcome_rationale) tuple
        """
        if decision_id not in self.decisions:
            raise ValueError(f"Decision {decision_id} not found")
        
        decision = self.decisions[decision_id]
        
        consensus_reached, rationale = self.consensus_builder.build_consensus(
            decision, self.stakeholders, wait_for_all
        )
        
        # If no consensus, try conflict resolution
        if not consensus_reached:
            resolution = self.consensus_builder.resolve_conflict(decision, self.stakeholders)
            rationale += f" | Resolution: {resolution}"
            
            # Apply resolution (for now, just log)
            logger.info(f"Conflict resolution: {resolution}")
        
        self.decision_history.append(decision_id)
        
        return consensus_reached, rationale
    
    def get_stakeholder_summary(self, stakeholder_id: str) -> Dict[str, Any]:
        """Get summary information for a stakeholder."""
        if stakeholder_id not in self.stakeholders:
            return {}
        
        ctx = self.stakeholders[stakeholder_id]
        
        return {
            "id": stakeholder_id,
            "name": ctx.identity.name,
            "role": ctx.identity.role.value,
            "verified": ctx.identity.verified,
            "vote_count": ctx.vote_count,
            "agreement_rate": ctx.agreement_rate,
            "voting_weight": self.voting_strategy.get_stakeholder_weight(ctx.identity.role)
        }
    
    def get_system_statistics(self) -> Dict[str, Any]:
        """Get overall SCI system statistics."""
        total_decisions = len(self.decisions)
        approved = len([d for d in self.decisions.values() if d.final_outcome == "approved"])
        rejected = len([d for d in self.decisions.values() if d.final_outcome == "rejected"])
        pending = total_decisions - approved - rejected
        
        return {
            "stakeholders": {
                "total": len(self.stakeholders),
                "by_role": {
                    role.value: len([
                        s for s in self.stakeholders.values()
                        if s.identity.role == role
                    ])
                    for role in StakeholderRole
                }
            },
            "decisions": {
                "total": total_decisions,
                "approved": approved,
                "rejected": rejected,
                "pending": pending
            },
            "consensus": {
                "type": self.voting_strategy.consensus_type.value,
                "approval_rate": (approved / total_decisions * 100) if total_decisions > 0 else 0
            }
        }


# Factory function
def create_multi_stakeholder_sci(
    consensus_type: str = "weighted",
    timeout_minutes: float = 30.0
) -> MultiStakeholderSCI:
    """
    Create a MultiStakeholderSCI instance.
    
    Args:
        consensus_type: "weighted", "simple_majority", "supermajority", "unanimous", or "adaptive"
        timeout_minutes: Decision timeout in minutes
        
    Returns:
        Configured MultiStakeholderSCI instance
    """
    consensus_enum = ConsensusType(consensus_type.lower())
    return MultiStakeholderSCI(
        consensus_type=consensus_enum,
        decision_timeout_minutes=timeout_minutes
    )
