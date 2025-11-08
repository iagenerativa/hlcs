"""
Integration Contracts for HLCS Component Integration

Base classes and interfaces for integrating sarai-agi components with HLCS v3.0.
Each contract defines the expected interface, data formats, and integration points.

These contracts serve as:
1. Base classes for actual implementations
2. Documentation of integration requirements
3. Validation interfaces for testing
4. Reference for API_*_INTEGRATION.md documents

Usage:
    # Implement contract
    class MyEmotionSystem(EmotionIntegrationContract):
        async def analyze_sentiment(self, text: str) -> EmotionResponse:
            # Implementation
            pass
    
    # Validate implementation
    system = MyEmotionSystem()
    assert isinstance(system, EmotionIntegrationContract)
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


# ==================== Base Contract ====================

class IntegrationContract(ABC):
    """
    Base contract for all HLCS integrations.
    
    All integration contracts must:
    1. Implement async interfaces (async-first design)
    2. Return structured responses (not raw strings)
    3. Handle errors gracefully (no exceptions to caller)
    4. Support health checks and stats
    """
    
    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the component with configuration"""
        pass
    
    @abstractmethod
    async def shutdown(self) -> None:
        """Gracefully shutdown the component"""
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """
        Check component health.
        
        Returns:
            {
                "status": "healthy" | "degraded" | "unhealthy",
                "details": {...},
                "timestamp": "..."
            }
        """
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """Get component statistics"""
        pass


# ==================== Emotion System Contract ====================

class SentimentPolarity(Enum):
    """Sentiment polarity levels"""
    VERY_NEGATIVE = -2
    NEGATIVE = -1
    NEUTRAL = 0
    POSITIVE = 1
    VERY_POSITIVE = 2


@dataclass
class EmotionResponse:
    """Standardized emotion analysis response"""
    sentiment_polarity: SentimentPolarity
    sentiment_score: float  # -1.0 to 1.0
    dominant_emotion: str  # e.g., "joy", "anger", "sadness"
    emotion_scores: Dict[str, float]  # Multiple emotions with confidence
    mood: str  # Current mood state
    confidence: float  # 0.0 to 1.0
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


class EmotionIntegrationContract(IntegrationContract):
    """
    Contract for Emotion System v0.3 integration.
    
    Integration points:
    - Meta-Consciousness: Emotional context for decision-making
    - SCI: Sentiment analysis for stakeholder inputs
    - Planning: Mood-aware goal prioritization
    
    Event topics:
    - emotion.sentiment_analyzed
    - emotion.mood_changed
    """
    
    @abstractmethod
    async def analyze_sentiment(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None
    ) -> EmotionResponse:
        """
        Analyze sentiment and emotions in text.
        
        Args:
            text: Input text to analyze
            context: Optional context (user_id, session_id, etc.)
        
        Returns:
            EmotionResponse with sentiment and emotion analysis
        """
        pass
    
    @abstractmethod
    async def get_current_mood(
        self,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get current mood state.
        
        Returns:
            {
                "mood": "calm" | "excited" | "stressed" | ...,
                "mood_score": 0.7,
                "recent_trends": [...],
                "factors": {...}
            }
        """
        pass
    
    @abstractmethod
    async def update_mood(
        self,
        interaction_result: Dict[str, Any]
    ) -> None:
        """Update mood based on interaction result"""
        pass


# ==================== Meta-Reasoner Contract ====================

@dataclass
class ReasoningStep:
    """Single step in chain-of-thought reasoning"""
    step_number: int
    thought: str
    reasoning_type: str  # "deduction", "induction", "abduction", "analogy"
    confidence: float
    supporting_evidence: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)


@dataclass
class ReasoningChain:
    """Complete chain-of-thought reasoning result"""
    query: str
    steps: List[ReasoningStep]
    conclusion: str
    overall_confidence: float
    reasoning_path: str  # "linear", "branching", "iterative"
    validation_result: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=datetime.now)


class MetaReasonerIntegrationContract(IntegrationContract):
    """
    Contract for Meta-Reasoner v0.2 integration.
    
    Integration points:
    - Strategic Planning: Feed CoT reasoning to ScenarioSimulator
    - Meta-Consciousness: Provide reasoning traces for introspection
    - Orchestrator: Complex query decomposition
    
    Event topics:
    - reasoning.chain_started
    - reasoning.chain_completed
    - reasoning.hypothesis_proposed
    - reasoning.hypothesis_validated
    """
    
    @abstractmethod
    async def generate_reasoning_chain(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ReasoningChain:
        """
        Generate chain-of-thought reasoning for query.
        
        Args:
            query: Question or problem to reason about
            context: Optional context (prior knowledge, constraints)
        
        Returns:
            ReasoningChain with step-by-step reasoning
        """
        pass
    
    @abstractmethod
    async def validate_hypothesis(
        self,
        hypothesis: str,
        evidence: List[str]
    ) -> Dict[str, Any]:
        """
        Validate hypothesis against evidence.
        
        Returns:
            {
                "valid": True | False,
                "confidence": 0.85,
                "supporting_evidence": [...],
                "contradicting_evidence": [...],
                "reasoning": "..."
            }
        """
        pass
    
    @abstractmethod
    async def decompose_query(
        self,
        complex_query: str
    ) -> List[str]:
        """
        Decompose complex query into simpler sub-queries.
        
        Returns:
            List of sub-queries in execution order
        """
        pass


# ==================== Active Learning Contract ====================

@dataclass
class FeedbackData:
    """User feedback data structure"""
    user_id: str
    feedback_type: str  # "thumbs_up", "thumbs_down", "rating", "correction"
    rating: Optional[float] = None  # 0.0 to 5.0
    correction: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class LearningUpdate:
    """Learning system update result"""
    memories_updated: int
    confidence_changes: Dict[str, float]
    preferences_learned: Dict[str, Any]
    consolidation_triggered: bool
    timestamp: datetime = field(default_factory=datetime.now)


class ActiveLearningIntegrationContract(IntegrationContract):
    """
    Contract for Active Learning v0.4 integration.
    
    Integration points:
    - KnowledgeRAG: Trigger consolidation based on feedback
    - Meta-Consciousness: Update confidence scores
    - Planning: Learn from goal success/failure patterns
    
    Event topics:
    - learning.feedback_received
    - learning.preference_updated
    - learning.model_updated
    """
    
    @abstractmethod
    async def process_feedback(
        self,
        feedback: FeedbackData
    ) -> LearningUpdate:
        """
        Process user feedback and update system.
        
        Args:
            feedback: User feedback data
        
        Returns:
            LearningUpdate with changes made
        """
        pass
    
    @abstractmethod
    async def learn_preference(
        self,
        user_id: str,
        preference_key: str,
        preference_value: Any
    ) -> None:
        """
        Learn user preference.
        
        Example:
            learn_preference("user_123", "response_style", "concise")
        """
        pass
    
    @abstractmethod
    async def get_learned_preferences(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Get all learned preferences for user.
        
        Returns:
            {
                "response_style": "concise",
                "technical_level": "advanced",
                "topics_of_interest": ["AI", "quantum"],
                ...
            }
        """
        pass
    
    @abstractmethod
    async def trigger_consolidation(
        self,
        confidence_threshold: float = 0.8
    ) -> Dict[str, Any]:
        """
        Trigger memory consolidation based on learned patterns.
        
        Returns:
            {
                "memories_consolidated": 15,
                "stm_to_ltm": 10,
                "removed_low_confidence": 5
            }
        """
        pass


# ==================== Monitoring Contract ====================

@dataclass
class MetricData:
    """Metric data point"""
    name: str
    value: float
    unit: str
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


class MonitoringIntegrationContract(IntegrationContract):
    """
    Contract for Enhanced Monitoring & Observability.
    
    Integration points:
    - All components: Emit metrics and traces
    - Prometheus: Expose metrics endpoint
    - Logging: Structured logging
    
    Event topics:
    - monitoring.metric_recorded
    - monitoring.alert_triggered
    """
    
    @abstractmethod
    async def record_metric(
        self,
        metric: MetricData
    ) -> None:
        """Record a metric data point"""
        pass
    
    @abstractmethod
    async def record_latency(
        self,
        operation: str,
        duration_ms: float,
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Record operation latency"""
        pass
    
    @abstractmethod
    async def increment_counter(
        self,
        counter_name: str,
        value: float = 1.0,
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Increment a counter metric"""
        pass
    
    @abstractmethod
    def get_metrics_summary(self) -> Dict[str, Any]:
        """
        Get summary of all metrics.
        
        Returns:
            {
                "counters": {...},
                "gauges": {...},
                "histograms": {...}
            }
        """
        pass


# ==================== Contract Validation ====================

def validate_contract_implementation(
    instance: Any,
    contract_class: type
) -> tuple[bool, List[str]]:
    """
    Validate that an instance correctly implements a contract.
    
    Args:
        instance: Instance to validate
        contract_class: Contract class to validate against
    
    Returns:
        (is_valid, list_of_errors)
    """
    errors = []
    
    # Check inheritance
    if not isinstance(instance, contract_class):
        errors.append(f"Instance does not inherit from {contract_class.__name__}")
        return False, errors
    
    # Check abstract methods are implemented
    abstract_methods = contract_class.__abstractmethods__
    for method_name in abstract_methods:
        if not hasattr(instance, method_name):
            errors.append(f"Missing required method: {method_name}")
        elif not callable(getattr(instance, method_name)):
            errors.append(f"Required method is not callable: {method_name}")
    
    is_valid = len(errors) == 0
    return is_valid, errors
