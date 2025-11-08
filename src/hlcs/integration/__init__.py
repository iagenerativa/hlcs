"""
HLCS Integration Infrastructure

Provides feature flags, event bus, and integration contracts for connecting
HLCS v3.0 with external components (sarai-agi migration, future systems).

Usage:
    from hlcs.integration import FeatureFlags, EventBus, IntegrationContract
    
    # Check feature availability
    if FeatureFlags.is_enabled("emotion_system"):
        emotion_engine.process()
    
    # Publish integration events
    await EventBus.publish("rag.consolidation", {"memories": 10})
    
    # Subscribe to events
    EventBus.subscribe("planning.goal_completed", handle_goal)
"""

from .feature_flags import FeatureFlags, FeatureFlag
from .event_bus import EventBus, Event, EventPriority, EventSubscriber, EventTopics
from .contracts import (
    IntegrationContract,
    EmotionIntegrationContract,
    MetaReasonerIntegrationContract,
    ActiveLearningIntegrationContract,
    MonitoringIntegrationContract,
    EmotionResponse,
    SentimentPolarity,
    ReasoningChain,
    ReasoningStep,
    FeedbackData,
    LearningUpdate,
    MetricData,
    validate_contract_implementation,
)

__all__ = [
    "FeatureFlags",
    "FeatureFlag",
    "EventBus",
    "Event",
    "EventPriority",
    "EventSubscriber",
    "EventTopics",
    "IntegrationContract",
    "EmotionIntegrationContract",
    "MetaReasonerIntegrationContract",
    "ActiveLearningIntegrationContract",
    "MonitoringIntegrationContract",
    "EmotionResponse",
    "SentimentPolarity",
    "ReasoningChain",
    "ReasoningStep",
    "FeedbackData",
    "LearningUpdate",
    "MetricData",
    "validate_contract_implementation",
]

__version__ = "0.1.0"
