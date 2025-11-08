"""
Meta-Consciousness Layer for HLCS v0.2

This module implements a meta-cognitive system that allows HLCS to:
1. Monitor its own decision-making processes
2. Track uncertainty and ignorance
3. Build temporal awareness of context evolution
4. Score confidence in its outputs
5. Make uncertainty-aware decisions with ensemble voting

The MetaConsciousnessLayer acts as HLCS's "introspection engine" that decides
when to use SARAi components based on strategic self-awareness.
"""

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


class DecisionStrategy(Enum):
    """Strategies for making decisions under uncertainty."""
    CONSERVATIVE = "conservative"  # Prefer known-good solutions
    EXPLORATORY = "exploratory"    # Try new approaches
    BALANCED = "balanced"           # Mix both
    ADAPTIVE = "adaptive"           # Adapt based on context


class IgnoranceType(Enum):
    """Types of ignorance the system can be aware of."""
    KNOWN_UNKNOWNS = "known_unknowns"      # "I know I don't know this"
    UNKNOWN_UNKNOWNS = "unknown_unknowns"  # "I don't know what I don't know"
    EPISTEMIC = "epistemic"                # Lack of knowledge
    ALEATORY = "aleatory"                  # Inherent randomness


@dataclass
class TemporalContext:
    """Represents temporal awareness of a context window."""
    start_time: datetime
    last_update: datetime
    interaction_count: int = 0
    context_drift: float = 0.0  # How much context has changed (0-1)
    session_duration: timedelta = field(default_factory=lambda: timedelta(0))
    
    def update(self) -> None:
        """Update temporal tracking."""
        now = datetime.now()
        self.last_update = now
        self.interaction_count += 1
        self.session_duration = now - self.start_time
    
    def calculate_context_freshness(self) -> float:
        """Calculate how fresh/stale the context is (0=stale, 1=fresh)."""
        minutes_since_update = (datetime.now() - self.last_update).total_seconds() / 60
        # Exponential decay: fresh for ~5 min, stale after ~30 min
        freshness = np.exp(-minutes_since_update / 10)
        return float(freshness)


@dataclass
class IgnoranceScore:
    """Quantifies what the system doesn't know."""
    ignorance_type: IgnoranceType
    confidence: float  # How confident we are about our ignorance (0-1)
    knowledge_gaps: List[str] = field(default_factory=list)
    uncertainty_sources: List[str] = field(default_factory=list)
    
    def should_seek_knowledge(self, threshold: float = 0.6) -> bool:
        """Decide if ignorance warrants knowledge-seeking behavior."""
        return self.confidence > threshold and len(self.knowledge_gaps) > 0


@dataclass
class SelfDoubtScore:
    """Quantifies self-doubt in decision-making."""
    confidence_score: float  # Overall confidence (0-1)
    reasoning_clarity: float  # How clear the reasoning is (0-1)
    evidence_strength: float  # How strong the evidence is (0-1)
    alternative_count: int  # Number of plausible alternatives
    uncertainty_level: float  # Epistemic uncertainty (0-1)
    
    def get_composite_confidence(self) -> float:
        """Calculate weighted composite confidence."""
        weights = {
            'confidence': 0.35,
            'reasoning': 0.25,
            'evidence': 0.25,
            'uncertainty': 0.15
        }
        
        # Penalize for too many alternatives
        alternative_penalty = min(0.2, self.alternative_count * 0.05)
        
        composite = (
            weights['confidence'] * self.confidence_score +
            weights['reasoning'] * self.reasoning_clarity +
            weights['evidence'] * self.evidence_strength +
            weights['uncertainty'] * (1 - self.uncertainty_level) -
            alternative_penalty
        )
        
        return max(0.0, min(1.0, composite))


@dataclass
class MetaCognitiveState:
    """Complete meta-cognitive state of the system."""
    temporal_context: TemporalContext
    ignorance_score: IgnoranceScore
    self_doubt: SelfDoubtScore
    decision_strategy: DecisionStrategy
    meta_reflections: List[str] = field(default_factory=list)
    
    def add_reflection(self, reflection: str) -> None:
        """Add a meta-cognitive reflection."""
        self.meta_reflections.append(f"[{datetime.now().isoformat()}] {reflection}")
        # Keep only last 20 reflections
        if len(self.meta_reflections) > 20:
            self.meta_reflections = self.meta_reflections[-20:]


class IgnoranceConsciousness:
    """
    System for tracking and reasoning about ignorance.
    
    Implements the philosophy: "Knowing what you don't know is wisdom."
    """
    
    def __init__(self, knowledge_domains: Optional[List[str]] = None):
        self.knowledge_domains = knowledge_domains or [
            "code_generation", "data_analysis", "multimodal_processing",
            "reasoning", "planning", "domain_knowledge"
        ]
        self.known_gaps: Dict[str, List[str]] = {domain: [] for domain in self.knowledge_domains}
        self.uncertainty_history: List[Tuple[str, float, datetime]] = []
        
    def assess_ignorance(
        self,
        query: str,
        context: Dict[str, Any],
        available_tools: List[str]
    ) -> IgnoranceScore:
        """
        Assess what we don't know about handling this query.
        
        Args:
            query: The user query
            context: Current context information
            available_tools: Tools we have access to
            
        Returns:
            IgnoranceScore quantifying our ignorance
        """
        knowledge_gaps = []
        uncertainty_sources = []
        
        # Check for missing context
        if not context.get("user_history"):
            knowledge_gaps.append("No user history available")
            uncertainty_sources.append("cold_start")
        
        # Check for tool coverage
        query_lower = query.lower()
        
        # Multimodal gaps
        if any(word in query_lower for word in ["image", "video", "audio"]):
            if "vision.analyze" not in available_tools and "audio.transcribe" not in available_tools:
                knowledge_gaps.append("Multimodal tools not available")
                uncertainty_sources.append("tool_limitation")
        
        # Code execution gaps
        if any(word in query_lower for word in ["run", "execute", "test", "debug"]):
            if "code_agent" not in [t.split(".")[0] for t in available_tools]:
                knowledge_gaps.append("Code execution capability limited")
                uncertainty_sources.append("capability_gap")
        
        # Domain knowledge gaps
        specialized_domains = ["medical", "legal", "financial", "scientific"]
        if any(domain in query_lower for domain in specialized_domains):
            knowledge_gaps.append(f"Specialized domain knowledge may be incomplete")
            uncertainty_sources.append("domain_expertise")
        
        # Determine ignorance type
        if len(knowledge_gaps) > 0:
            ignorance_type = IgnoranceType.KNOWN_UNKNOWNS
            confidence = 0.8
        elif len(uncertainty_sources) > 0:
            ignorance_type = IgnoranceType.EPISTEMIC
            confidence = 0.6
        else:
            ignorance_type = IgnoranceType.UNKNOWN_UNKNOWNS
            confidence = 0.3
        
        score = IgnoranceScore(
            ignorance_type=ignorance_type,
            confidence=confidence,
            knowledge_gaps=knowledge_gaps,
            uncertainty_sources=uncertainty_sources
        )
        
        # Track history
        self.uncertainty_history.append((query, confidence, datetime.now()))
        if len(self.uncertainty_history) > 100:
            self.uncertainty_history = self.uncertainty_history[-100:]
        
        return score
    
    def get_learning_recommendations(self, ignorance_score: IgnoranceScore) -> List[str]:
        """Generate recommendations for filling knowledge gaps."""
        recommendations = []
        
        if "Multimodal tools" in str(ignorance_score.knowledge_gaps):
            recommendations.append("Route to SARAi Vision/Audio MCP tools")
        
        if "Code execution" in str(ignorance_score.knowledge_gaps):
            recommendations.append("Activate Phi4MiniAGI CodeAgent")
        
        if "domain knowledge" in str(ignorance_score.knowledge_gaps):
            recommendations.append("Use RAG to retrieve specialized knowledge")
        
        if ignorance_score.ignorance_type == IgnoranceType.UNKNOWN_UNKNOWNS:
            recommendations.append("Perform exploratory analysis with SAUL")
        
        return recommendations


class NarrativeConsciousness:
    """
    Constructs narrative understanding of episodic memory.
    
    Transforms raw episodic memories into coherent narratives that help
    the system understand context and patterns over time.
    """
    
    def __init__(self, max_narrative_length: int = 10):
        self.narratives: List[str] = []
        self.max_length = max_narrative_length
        self.episode_counter = 0
        
    def construct_narrative(
        self,
        episodes: List[Dict[str, Any]],
        focus: str = "learning"
    ) -> str:
        """
        Build a narrative from episodic memories.
        
        Args:
            episodes: List of memory episodes
            focus: Narrative focus ("learning", "goals", "patterns")
            
        Returns:
            Narrative string
        """
        if not episodes:
            return "No previous context available."
        
        if focus == "learning":
            narrative = self._construct_learning_narrative(episodes)
        elif focus == "goals":
            narrative = self._construct_goal_narrative(episodes)
        else:
            narrative = self._construct_pattern_narrative(episodes)
        
        self.narratives.append(narrative)
        if len(self.narratives) > self.max_length:
            self.narratives = self.narratives[-self.max_length:]
        
        self.episode_counter += len(episodes)
        
        return narrative
    
    def _construct_learning_narrative(self, episodes: List[Dict[str, Any]]) -> str:
        """Focus on learning progression."""
        learnings = []
        for ep in episodes:
            if ep.get("type") == "query_response":
                query = ep.get("query", "")
                success = ep.get("success", False)
                if success:
                    learnings.append(f"✓ Handled: {query[:60]}...")
                else:
                    learnings.append(f"✗ Struggled with: {query[:60]}...")
        
        if learnings:
            narrative = "Recent learning trajectory:\n" + "\n".join(learnings[-5:])
        else:
            narrative = "No clear learning pattern yet."
        
        return narrative
    
    def _construct_goal_narrative(self, episodes: List[Dict[str, Any]]) -> str:
        """Focus on goal progression."""
        goals_mentioned = []
        for ep in episodes:
            query = ep.get("query", "").lower()
            if any(word in query for word in ["create", "build", "implement", "develop"]):
                goals_mentioned.append(query[:80])
        
        if goals_mentioned:
            narrative = f"User is working on {len(goals_mentioned)} implementation tasks"
        else:
            narrative = "Exploratory phase, no clear implementation goals yet"
        
        return narrative
    
    def _construct_pattern_narrative(self, episodes: List[Dict[str, Any]]) -> str:
        """Focus on behavioral patterns."""
        query_types = {"technical": 0, "conceptual": 0, "debug": 0}
        
        for ep in episodes:
            query = ep.get("query", "").lower()
            if any(word in query for word in ["error", "bug", "fix", "debug"]):
                query_types["debug"] += 1
            elif any(word in query for word in ["how", "why", "what", "explain"]):
                query_types["conceptual"] += 1
            else:
                query_types["technical"] += 1
        
        dominant = max(query_types, key=query_types.get)
        return f"User query pattern: {dominant} ({query_types[dominant]}/{len(episodes)})"


class MetaConsciousnessLayer:
    """
    Central meta-cognitive system for HLCS.
    
    This layer monitors all HLCS operations and provides strategic guidance
    on when to use which components (SARAi, SAUL, Phi4MiniAGI, etc.).
    """
    
    def __init__(
        self,
        decision_strategy: DecisionStrategy = DecisionStrategy.ADAPTIVE,
        confidence_threshold: float = 0.7
    ):
        self.decision_strategy = decision_strategy
        self.confidence_threshold = confidence_threshold
        
        self.ignorance_system = IgnoranceConsciousness()
        self.narrative_system = NarrativeConsciousness()
        
        self.temporal_context = TemporalContext(
            start_time=datetime.now(),
            last_update=datetime.now()
        )
        
        self.decision_history: List[Dict[str, Any]] = []
        self.performance_metrics: Dict[str, List[float]] = {
            "confidence_scores": [],
            "latencies": [],
            "success_rates": []
        }
        
        logger.info(f"MetaConsciousnessLayer initialized with strategy={decision_strategy}")
    
    def analyze_query_context(
        self,
        query: str,
        context: Dict[str, Any],
        available_components: List[str]
    ) -> MetaCognitiveState:
        """
        Perform meta-cognitive analysis of query context.
        
        Args:
            query: User query
            context: Current context (history, session, etc.)
            available_components: Available SARAi components
            
        Returns:
            Complete meta-cognitive state
        """
        start_time = time.time()
        
        # Update temporal tracking
        self.temporal_context.update()
        
        # Assess ignorance
        ignorance_score = self.ignorance_system.assess_ignorance(
            query, context, available_components
        )
        
        # Calculate self-doubt
        self_doubt = self._calculate_self_doubt(
            query, context, ignorance_score, available_components
        )
        
        # Build narrative from memory
        if context.get("memory_episodes"):
            narrative = self.narrative_system.construct_narrative(
                context["memory_episodes"],
                focus="learning"
            )
        else:
            narrative = "First interaction, no context yet"
        
        # Create meta-cognitive state
        state = MetaCognitiveState(
            temporal_context=self.temporal_context,
            ignorance_score=ignorance_score,
            self_doubt=self_doubt,
            decision_strategy=self.decision_strategy
        )
        
        # Add meta-reflection
        composite_confidence = self_doubt.get_composite_confidence()
        state.add_reflection(
            f"Query analysis: confidence={composite_confidence:.2f}, "
            f"gaps={len(ignorance_score.knowledge_gaps)}, "
            f"narrative={narrative[:50]}..."
        )
        
        analysis_time = time.time() - start_time
        logger.debug(f"Meta-cognitive analysis took {analysis_time*1000:.0f}ms")
        
        return state
    
    def _calculate_self_doubt(
        self,
        query: str,
        context: Dict[str, Any],
        ignorance_score: IgnoranceScore,
        available_components: List[str]
    ) -> SelfDoubtScore:
        """Calculate self-doubt score for current situation."""
        
        # Base confidence from ignorance
        base_confidence = 1.0 - (len(ignorance_score.knowledge_gaps) * 0.15)
        base_confidence = max(0.2, base_confidence)
        
        # Reasoning clarity (do we understand the query?)
        query_length = len(query.split())
        reasoning_clarity = min(1.0, 0.5 + (query_length / 100))  # Longer = clearer intent
        
        # Evidence strength (do we have context?)
        evidence_strength = 0.5
        if context.get("user_history"):
            evidence_strength += 0.3
        if context.get("memory_episodes"):
            evidence_strength += 0.2
        
        # Alternative count (how many ways could we handle this?)
        alternatives = len(available_components)
        
        # Uncertainty level
        uncertainty = 1.0 - ignorance_score.confidence
        
        return SelfDoubtScore(
            confidence_score=base_confidence,
            reasoning_clarity=reasoning_clarity,
            evidence_strength=evidence_strength,
            alternative_count=alternatives,
            uncertainty_level=uncertainty
        )
    
    def decide_component_routing(
        self,
        state: MetaCognitiveState,
        available_components: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Decide which component(s) to use based on meta-cognitive state.
        
        This is the key decision point where HLCS autonomously chooses
        between SARAi MCP, Phi4MiniAGI, or hybrid approaches.
        
        Args:
            state: Current meta-cognitive state
            available_components: Dict of {component_name: component_info}
            
        Returns:
            Routing decision with component selection and reasoning
        """
        decision_start = time.time()
        
        composite_confidence = state.self_doubt.get_composite_confidence()
        
        # Get ignorance-based recommendations
        recommendations = self.ignorance_system.get_learning_recommendations(
            state.ignorance_score
        )
        
        # Decision logic based on strategy and confidence
        routing = self._apply_decision_strategy(
            state, composite_confidence, recommendations, available_components
        )
        
        # Track decision
        decision_record = {
            "timestamp": datetime.now().isoformat(),
            "confidence": composite_confidence,
            "strategy": self.decision_strategy.value,
            "routing": routing,
            "recommendations": recommendations,
            "latency_ms": (time.time() - decision_start) * 1000
        }
        self.decision_history.append(decision_record)
        
        # Keep only last 100 decisions
        if len(self.decision_history) > 100:
            self.decision_history = self.decision_history[-100:]
        
        logger.info(f"Routing decision: {routing['primary_component']} (confidence={composite_confidence:.2f})")
        
        return routing
    
    def _apply_decision_strategy(
        self,
        state: MetaCognitiveState,
        confidence: float,
        recommendations: List[str],
        available_components: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply decision strategy to choose components."""
        
        routing = {
            "primary_component": None,
            "fallback_components": [],
            "reasoning": [],
            "use_ensemble": False,
            "confidence": confidence
        }
        
        # Parse recommendations
        use_sarai = any("SARAi" in rec for rec in recommendations)
        use_agi = any("AGI" in rec or "CodeAgent" in rec for rec in recommendations)
        use_rag = any("RAG" in rec for rec in recommendations)
        
        # Strategy-based routing
        if self.decision_strategy == DecisionStrategy.CONSERVATIVE:
            # Prefer known-good SAUL for simple queries
            if confidence > self.confidence_threshold:
                routing["primary_component"] = "sarai_mcp"
                routing["reasoning"].append("High confidence, using proven SARAi MCP")
            else:
                routing["primary_component"] = "phi4mini_agi"
                routing["fallback_components"].append("sarai_mcp")
                routing["reasoning"].append("Lower confidence, trying local AGI first")
        
        elif self.decision_strategy == DecisionStrategy.EXPLORATORY:
            # Prefer trying AGI for learning
            routing["primary_component"] = "phi4mini_agi"
            routing["fallback_components"].append("sarai_mcp")
            routing["reasoning"].append("Exploratory mode: testing AGI capabilities")
        
        elif self.decision_strategy == DecisionStrategy.BALANCED:
            # Use ensemble voting
            routing["use_ensemble"] = True
            routing["primary_component"] = "ensemble"
            routing["fallback_components"] = ["sarai_mcp", "phi4mini_agi"]
            routing["reasoning"].append("Balanced mode: using ensemble voting")
        
        else:  # ADAPTIVE
            # Adapt based on recommendations and context
            if use_sarai and not use_agi:
                routing["primary_component"] = "sarai_mcp"
                routing["reasoning"].append("Recommendations favor SARAi tools")
            elif use_agi and not use_sarai:
                routing["primary_component"] = "phi4mini_agi"
                routing["reasoning"].append("Recommendations favor local AGI")
            elif use_rag:
                routing["primary_component"] = "phi4mini_agi"
                routing["reasoning"].append("RAG retrieval needed, using AGI")
            else:
                # Default to confidence-based
                if confidence > 0.75:
                    routing["primary_component"] = "sarai_mcp"
                elif confidence > 0.5:
                    routing["primary_component"] = "phi4mini_agi"
                else:
                    routing["use_ensemble"] = True
                    routing["primary_component"] = "ensemble"
                    routing["fallback_components"] = ["sarai_mcp", "phi4mini_agi"]
                routing["reasoning"].append(f"Adaptive routing based on confidence={confidence:.2f}")
        
        return routing
    
    def evaluate_response_quality(
        self,
        response: str,
        expected_criteria: Optional[List[str]] = None
    ) -> Tuple[float, List[str]]:
        """
        Evaluate the quality of a response using meta-cognitive assessment.
        
        Args:
            response: The response to evaluate
            expected_criteria: Optional quality criteria to check
            
        Returns:
            (quality_score, issues) tuple
        """
        quality_score = 0.5  # Base score
        issues = []
        
        # Length check
        if len(response) < 50:
            issues.append("Response too short")
            quality_score -= 0.2
        elif len(response) > 5000:
            issues.append("Response may be too verbose")
            quality_score -= 0.1
        else:
            quality_score += 0.1
        
        # Coherence check (basic)
        if response.strip():
            sentences = response.split(".")
            if len(sentences) > 2:
                quality_score += 0.1
        else:
            issues.append("Empty response")
            quality_score = 0.0
        
        # Criteria check
        if expected_criteria:
            met_criteria = sum(1 for criterion in expected_criteria if criterion.lower() in response.lower())
            criteria_ratio = met_criteria / len(expected_criteria)
            quality_score += 0.3 * criteria_ratio
            
            if criteria_ratio < 0.5:
                issues.append(f"Only {met_criteria}/{len(expected_criteria)} criteria met")
        
        # Clamp score
        quality_score = max(0.0, min(1.0, quality_score))
        
        # Track metrics
        self.performance_metrics["confidence_scores"].append(quality_score)
        if len(self.performance_metrics["confidence_scores"]) > 100:
            self.performance_metrics["confidence_scores"] = self.performance_metrics["confidence_scores"][-100:]
        
        return quality_score, issues
    
    def get_meta_statistics(self) -> Dict[str, Any]:
        """Get meta-cognitive statistics for monitoring."""
        return {
            "temporal": {
                "session_duration_minutes": self.temporal_context.session_duration.total_seconds() / 60,
                "interactions": self.temporal_context.interaction_count,
                "context_freshness": self.temporal_context.calculate_context_freshness()
            },
            "decisions": {
                "total_decisions": len(self.decision_history),
                "avg_confidence": np.mean([d["confidence"] for d in self.decision_history]) if self.decision_history else 0,
                "strategy": self.decision_strategy.value
            },
            "performance": {
                "avg_quality_score": np.mean(self.performance_metrics["confidence_scores"]) if self.performance_metrics["confidence_scores"] else 0,
                "recent_scores": self.performance_metrics["confidence_scores"][-10:]
            },
            "ignorance": {
                "recent_uncertainty": self.ignorance_system.uncertainty_history[-5:] if self.ignorance_system.uncertainty_history else []
            },
            "narratives": {
                "total_constructed": self.narrative_system.episode_counter,
                "recent_narrative": self.narrative_system.narratives[-1] if self.narrative_system.narratives else None
            }
        }


# Factory function for easy instantiation
def create_meta_consciousness(
    strategy: str = "adaptive",
    confidence_threshold: float = 0.7
) -> MetaConsciousnessLayer:
    """
    Create a MetaConsciousnessLayer with specified configuration.
    
    Args:
        strategy: "conservative", "exploratory", "balanced", or "adaptive"
        confidence_threshold: Minimum confidence for autonomous decisions
        
    Returns:
        Configured MetaConsciousnessLayer instance
    """
    strategy_enum = DecisionStrategy(strategy.lower())
    return MetaConsciousnessLayer(
        decision_strategy=strategy_enum,
        confidence_threshold=confidence_threshold
    )
