"""
Emotional Integration Bridge - HLCS v3.0
=========================================

Bridge between EmotionalContextEngine and Meta-Consciousness Layer v0.2.

Provides emotional context for decision-making strategies without modifying
existing Meta-Consciousness logic (avoid regressions).

Integration Pattern:
- EmotionalContextEngine detects emotion + intensity + valence
- Meta-Consciousness consults emotional context via this bridge
- Decision strategies adjust based on emotional state

Example:
--------
>>> from hlcs.emotion import EmotionalContextEngine
>>> from hlcs.emotion.emotional_integration import EmotionalMetaBridge
>>>
>>> emotion_engine = EmotionalContextEngine()
>>> bridge = EmotionalMetaBridge(emotion_engine)
>>>
>>> # Analyze user frustration
>>> strategy = bridge.recommend_decision_strategy(
...     text="No funciona, ayuda por favor!",
...     user_id="user123"
... )
>>>
>>> print(strategy)  # "CONSERVATIVE" (frustrated user needs reliable solutions)

Version: Migration Phase 1
Date: 2025-11-08
Status: COEXIST with Meta-Consciousness v0.2
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional

from .context_engine import EmotionalContextEngine, EmotionalContext, EmotionalResult

logger = logging.getLogger(__name__)


class DecisionStrategy(Enum):
    """
    Decision strategies from Meta-Consciousness Layer v0.2.
    
    DO NOT MODIFY - These match existing Meta-Consciousness API.
    See: src/hlcs/metacognition/meta_consciousness.py
    """
    CONSERVATIVE = "conservative"  # Prioritize known solutions (SARAi MCP)
    EXPLORATORY = "exploratory"    # Try new approaches (AGI-first)
    BALANCED = "balanced"          # Mix of both
    ADAPTIVE = "adaptive"          # Adapt based on context + confidence


@dataclass
class EmotionalDecisionContext:
    """
    Emotional context for decision-making.
    
    Attributes:
        detected_emotion: Primary emotion detected
        confidence: Confidence score (0-1)
        intensity: Emotion intensity (0-1)
        valence: Positive (+1) to Negative (-1)
        recommended_strategy: Suggested decision strategy
        reasoning: Why this strategy was recommended
    """
    detected_emotion: EmotionalContext
    confidence: float
    intensity: float
    valence: float
    recommended_strategy: DecisionStrategy
    reasoning: str


class EmotionalMetaBridge:
    """
    Bridge between Emotional Context and Meta-Consciousness.
    
    Rules (avoid regressions in Meta-Consciousness v0.2):
    1. DO NOT modify Meta-Consciousness code
    2. DO NOT replace existing decision logic
    3. DO add emotional awareness as optional context
    4. DO use feature flags for gradual rollout
    
    Integration:
        Meta-Consciousness can consult this bridge before deciding strategy.
        If emotion detection is disabled (feature flag), returns None gracefully.
    """
    
    def __init__(self, emotion_engine: Optional[EmotionalContextEngine] = None):
        """
        Initialize bridge with optional emotion engine.
        
        Args:
            emotion_engine: EmotionalContextEngine instance (None = disabled)
        """
        self.emotion_engine = emotion_engine or EmotionalContextEngine()
        logger.info("EmotionalMetaBridge initialized")
    
    def recommend_decision_strategy(
        self, 
        text: str, 
        user_id: Optional[str] = None,
        current_confidence: float = 0.5
    ) -> EmotionalDecisionContext:
        """
        Recommend decision strategy based on emotional context.
        
        Strategy Rules:
        - FRUSTRATED + high intensity → CONSERVATIVE (need reliable solutions)
        - EXCITED + positive valence → EXPLORATORY (open to new ideas)
        - CONFUSED + low confidence → CONSERVATIVE (need clear guidance)
        - NEUTRAL + balanced → ADAPTIVE (context-driven)
        - URGENT → CONSERVATIVE (prioritize speed + reliability)
        
        Args:
            text: User input text
            user_id: Optional user identifier for profiling
            current_confidence: Current Meta-Consciousness confidence score
        
        Returns:
            EmotionalDecisionContext with recommended strategy
        """
        # Analyze emotional context
        emotion_result: EmotionalResult = self.emotion_engine.analyze_emotional_context(
            text=text,
            user_id=user_id
        )
        
        # Decision logic based on emotion
        strategy, reasoning = self._decide_strategy(emotion_result, current_confidence)
        
        return EmotionalDecisionContext(
            detected_emotion=emotion_result.detected_emotion,
            confidence=emotion_result.confidence,
            intensity=emotion_result.emotion_intensity,
            valence=emotion_result.valence,
            recommended_strategy=strategy,
            reasoning=reasoning
        )
    
    def _decide_strategy(
        self, 
        emotion: EmotionalResult, 
        current_confidence: float
    ) -> tuple[DecisionStrategy, str]:
        """
        Internal decision logic.
        
        Returns:
            (strategy, reasoning) tuple
        """
        # FRUSTRATED → CONSERVATIVE (user needs reliable solutions)
        if emotion.detected_emotion == EmotionalContext.FRUSTRATED:
            if emotion.emotion_intensity > 0.7:
                return (
                    DecisionStrategy.CONSERVATIVE,
                    f"User frustrated (intensity {emotion.emotion_intensity:.2f}), "
                    "prioritize reliable known solutions"
                )
        
        # URGENT → CONSERVATIVE (prioritize speed)
        if emotion.detected_emotion == EmotionalContext.URGENT:
            return (
                DecisionStrategy.CONSERVATIVE,
                "User urgent, prioritize fast reliable responses"
            )
        
        # CONFUSED → CONSERVATIVE (need clarity)
        if emotion.detected_emotion == EmotionalContext.CONFUSED:
            return (
                DecisionStrategy.CONSERVATIVE,
                "User confused, provide clear structured guidance"
            )
        
        # EXCITED + positive → EXPLORATORY (open to new ideas)
        if emotion.detected_emotion == EmotionalContext.EXCITED:
            if emotion.valence > 0.5:
                return (
                    DecisionStrategy.EXPLORATORY,
                    f"User excited (valence {emotion.valence:.2f}), "
                    "open to exploring new approaches"
                )
        
        # PLAYFUL → EXPLORATORY
        if emotion.detected_emotion == EmotionalContext.PLAYFUL:
            return (
                DecisionStrategy.EXPLORATORY,
                "User playful, can experiment with creative solutions"
            )
        
        # Low confidence → CONSERVATIVE (don't risk)
        if current_confidence < 0.3:
            return (
                DecisionStrategy.CONSERVATIVE,
                f"Low system confidence ({current_confidence:.2f}), "
                "stick to known solutions"
            )
        
        # Default: ADAPTIVE (context-driven)
        return (
            DecisionStrategy.ADAPTIVE,
            f"Emotion {emotion.detected_emotion.value} neutral, "
            f"confidence {emotion.confidence:.2f}, use adaptive strategy"
        )
    
    def get_emotional_context_dict(self, text: str, user_id: Optional[str] = None) -> Dict:
        """
        Get emotional context as dict for Meta-Consciousness metadata.
        
        Returns dict that can be added to Meta-Consciousness state without
        modifying its core structure.
        
        Args:
            text: User input text
            user_id: Optional user identifier
        
        Returns:
            Dict with emotional metadata
        """
        emotion_result = self.emotion_engine.analyze_emotional_context(text, user_id)
        
        return {
            "emotional_context": {
                "emotion": emotion_result.detected_emotion.value,
                "confidence": emotion_result.confidence,
                "intensity": emotion_result.emotion_intensity,
                "valence": emotion_result.valence,
                "empathy_level": emotion_result.empathy_level,
                "cultural_context": emotion_result.cultural_context.value if emotion_result.cultural_context else None,
            }
        }


# Convenience factory
def create_emotional_bridge(enabled: bool = False) -> Optional[EmotionalMetaBridge]:
    """
    Factory to create bridge with feature flag support.
    
    Args:
        enabled: Feature flag enable_emotion_system
    
    Returns:
        EmotionalMetaBridge if enabled, None otherwise
    """
    if not enabled:
        logger.info("Emotional bridge disabled (feature flag)")
        return None
    
    return EmotionalMetaBridge()
