# HLCS Integration Infrastructure - User Guide

**Version**: 0.1.0  
**Created**: 8 de noviembre de 2025  
**Purpose**: Infrastructure para migración segura de componentes de sarai-agi

---

## 📋 Overview

Sistema de integración de 3 capas para HLCS v3.0:

1. **Feature Flags**: Control de rollout dinámico
2. **Event Bus**: Comunicación async entre componentes
3. **Integration Contracts**: Interfaces estandarizadas

**Objetivo**: Facilitar estrategia HYBRID APPROACH (MIGRATE/COEXIST/DEFER/MERGE)

---

## 🚩 Feature Flags

### Quick Start

```python
from hlcs.integration import FeatureFlags

# Check if feature is enabled
if FeatureFlags.is_enabled("emotion_system"):
    result = await emotion_engine.analyze(text)

# Enable feature at runtime
FeatureFlags.set("emotion_system", enabled=True)

# Gradual rollout (0% → 25% → 50% → 100%)
FeatureFlags.set_rollout_percentage("emotion_system", 25.0)
```

### Environment Variables

```bash
# Enable feature via environment
export HLCS_FEATURE_EMOTION_SYSTEM=true
export HLCS_FEATURE_META_REASONER=false
```

### Predefined Migration Flags

| Flag | Phase | Strategy | Default |
|------|-------|----------|---------|
| `emotion_system` | 1 | MIGRATE | Disabled |
| `monitoring_enhanced` | 1 | MIGRATE | Disabled |
| `meta_reasoner` | 2 | COEXIST | Disabled |
| `active_learning` | 2 | COEXIST | Disabled |
| `integrated_consciousness` | 4 | MERGE | Disabled |
| `lora_trainer` | 4 | DEFER | Disabled |

### Rollout Strategies

```python
from hlcs.integration.feature_flags import RolloutStrategy

# Enable for everyone
FeatureFlags.set("emotion_system", 
                 enabled=True, 
                 strategy=RolloutStrategy.ALL)

# Enable for 50% of users (hash-based)
FeatureFlags.set("meta_reasoner", 
                 enabled=True,
                 strategy=RolloutStrategy.PERCENTAGE,
                 rollout_percentage=50.0)

# Enable for specific users only
FeatureFlags.set("active_learning",
                 enabled=True,
                 strategy=RolloutStrategy.WHITELIST,
                 whitelist=["user_123", "user_456"])
```

### Migration Status

```python
# Get migration overview
status = FeatureFlags.get_migration_status()
print(status)
# Output:
# {
#   "phase_1_migrate": [
#     {"name": "emotion_system", "enabled": true, "rollout": 25.0},
#     {"name": "monitoring_enhanced", "enabled": true, "rollout": 100.0}
#   ],
#   "phase_2_coexist": [...],
#   "phase_4_deferred": [...],
#   "total_enabled": 2,
#   "total_flags": 6
# }
```

---

## 🚌 Event Bus

### Quick Start

```python
from hlcs.integration import EventBus, Event, EventPriority

# Initialize (once at startup)
await EventBus.initialize()

# Publish event
await EventBus.publish(
    topic="rag.consolidation_completed",
    data={"memories": 10, "stm_to_ltm": 5},
    priority=EventPriority.NORMAL,
    source="knowledge_rag"
)

# Subscribe to events
async def handle_consolidation(event: Event):
    print(f"Consolidation: {event.data}")

EventBus.subscribe("rag.consolidation_completed", handle_consolidation)

# Shutdown (on app exit)
await EventBus.shutdown()
```

### Event Naming Convention

**Format**: `<component>.<action>`

Examples:
- `rag.memory_added`
- `planning.goal_completed`
- `reasoning.hypothesis_validated`
- `learning.feedback_received`
- `emotion.mood_changed`

### Wildcard Subscriptions

```python
# Subscribe to all RAG events
EventBus.subscribe("rag.*", handle_rag_events)

# Subscribe to all events
EventBus.subscribe("**", handle_all_events)
```

### Priority Processing

```python
# High priority handler (processes first)
EventBus.subscribe(
    "critical.alert",
    handle_alert,
    priority=EventPriority.HIGH
)

# Low priority handler (processes last)
EventBus.subscribe(
    "logging.info",
    log_event,
    priority=EventPriority.LOW
)
```

### Event Filtering

```python
# Only process important events
def only_important(event: Event) -> bool:
    return event.data.get("importance") == "high"

EventBus.subscribe(
    "monitoring.*",
    handle_important_metrics,
    filter_func=only_important
)
```

### Predefined Event Topics

```python
from hlcs.integration import EventTopics

# KnowledgeRAG events
await EventBus.publish(EventTopics.RAG_MEMORY_ADDED, {...})
await EventBus.publish(EventTopics.RAG_CONSOLIDATION_COMPLETED, {...})

# Strategic Planning events
await EventBus.publish(EventTopics.PLANNING_GOAL_COMPLETED, {...})
await EventBus.publish(EventTopics.PLANNING_MILESTONE_REACHED, {...})

# Meta-Reasoner events (future)
await EventBus.publish(EventTopics.REASONING_CHAIN_COMPLETED, {...})

# Active Learning events (future)
await EventBus.publish(EventTopics.LEARNING_FEEDBACK_RECEIVED, {...})

# Emotion System events (future)
await EventBus.publish(EventTopics.EMOTION_MOOD_CHANGED, {...})
```

### Statistics & Monitoring

```python
# Get event bus statistics
stats = EventBus.get_stats()
print(stats)
# {
#   "events_published": 1523,
#   "events_dispatched": 1520,
#   "callbacks_succeeded": 4560,
#   "callbacks_failed": 3,
#   "subscribers_total": 12,
#   "queue_size": 0,
#   "history_size": 100,
#   "dead_letter_queue_size": 3
# }

# Get event history
history = EventBus.get_event_history(limit=50)

# Get failed events
failed = EventBus.get_dead_letter_queue()
for event, error in failed:
    print(f"Failed: {event.topic} - {error}")
```

---

## 📜 Integration Contracts

### Quick Start

```python
from hlcs.integration import EmotionIntegrationContract, EmotionResponse

# Implement contract
class MyEmotionSystem(EmotionIntegrationContract):
    async def initialize(self, config):
        self.model = load_model(config["model_path"])
    
    async def analyze_sentiment(self, text, context=None):
        result = self.model.predict(text)
        return EmotionResponse(
            sentiment_polarity=result.polarity,
            sentiment_score=result.score,
            dominant_emotion=result.emotion,
            emotion_scores=result.all_emotions,
            mood=self.get_mood(),
            confidence=result.confidence
        )
    
    async def health_check(self):
        return {"status": "healthy", "model": "loaded"}
    
    # ... implement other methods

# Validate implementation
from hlcs.integration import validate_contract_implementation

system = MyEmotionSystem()
is_valid, errors = validate_contract_implementation(
    system,
    EmotionIntegrationContract
)

if not is_valid:
    print(f"Implementation errors: {errors}")
```

### Available Contracts

#### 1. EmotionIntegrationContract

**Methods**:
- `analyze_sentiment(text, context=None) -> EmotionResponse`
- `get_current_mood(user_id=None) -> Dict`
- `update_mood(interaction_result) -> None`

**Integration Points**:
- Meta-Consciousness: Emotional context for decisions
- SCI: Sentiment analysis for stakeholder inputs
- Planning: Mood-aware goal prioritization

#### 2. MetaReasonerIntegrationContract

**Methods**:
- `generate_reasoning_chain(query, context=None) -> ReasoningChain`
- `validate_hypothesis(hypothesis, evidence) -> Dict`
- `decompose_query(complex_query) -> List[str]`

**Integration Points**:
- Strategic Planning: Feed CoT to ScenarioSimulator
- Meta-Consciousness: Reasoning traces for introspection
- Orchestrator: Complex query decomposition

#### 3. ActiveLearningIntegrationContract

**Methods**:
- `process_feedback(feedback: FeedbackData) -> LearningUpdate`
- `learn_preference(user_id, key, value) -> None`
- `get_learned_preferences(user_id) -> Dict`
- `trigger_consolidation(threshold=0.8) -> Dict`

**Integration Points**:
- KnowledgeRAG: Trigger consolidation
- Meta-Consciousness: Update confidence scores
- Planning: Learn from goal patterns

#### 4. MonitoringIntegrationContract

**Methods**:
- `record_metric(metric: MetricData) -> None`
- `record_latency(operation, duration_ms, labels=None) -> None`
- `increment_counter(counter_name, value=1.0, labels=None) -> None`
- `get_metrics_summary() -> Dict`

**Integration Points**:
- All components: Emit metrics
- Prometheus: Expose metrics endpoint

---

## 🔗 Complete Integration Example

### Emotion System with Feature Flags + Events

```python
from hlcs.integration import (
    FeatureFlags,
    EventBus,
    EventTopics,
    EmotionIntegrationContract,
    EmotionResponse,
    SentimentPolarity
)

class EmotionSystem(EmotionIntegrationContract):
    async def initialize(self, config):
        self.model = load_model(config["model_path"])
        await EventBus.initialize()
    
    async def analyze_sentiment(self, text, context=None):
        # Check feature flag
        if not FeatureFlags.is_enabled("emotion_system"):
            return None
        
        # Analyze
        result = self.model.predict(text)
        
        response = EmotionResponse(
            sentiment_polarity=SentimentPolarity.POSITIVE,
            sentiment_score=result.score,
            dominant_emotion=result.emotion,
            emotion_scores=result.emotions,
            mood=self._get_mood(),
            confidence=result.confidence
        )
        
        # Publish event
        await EventBus.publish(
            EventTopics.EMOTION_SENTIMENT_ANALYZED,
            {
                "sentiment": response.sentiment_polarity.name,
                "score": response.sentiment_score,
                "emotion": response.dominant_emotion,
                "confidence": response.confidence
            },
            source="emotion_system"
        )
        
        return response

# Usage in orchestrator
async def process_with_emotion(query: str):
    emotion_system = EmotionSystem()
    await emotion_system.initialize(config)
    
    # Analyze sentiment
    emotion_result = await emotion_system.analyze_sentiment(query)
    
    if emotion_result and emotion_result.sentiment_score < -0.5:
        # Adjust response style for negative sentiment
        response_style = "empathetic"
    else:
        response_style = "normal"
    
    return await generate_response(query, style=response_style)
```

### Active Learning with KnowledgeRAG Integration

```python
from hlcs.integration import (
    EventBus,
    EventTopics,
    ActiveLearningIntegrationContract,
    FeedbackData
)

class ActiveLearningSystem(ActiveLearningIntegrationContract):
    async def process_feedback(self, feedback: FeedbackData):
        # Process feedback
        updates = self._analyze_feedback(feedback)
        
        # Publish event for KnowledgeRAG
        await EventBus.publish(
            EventTopics.LEARNING_FEEDBACK_RECEIVED,
            {
                "user_id": feedback.user_id,
                "feedback_type": feedback.feedback_type,
                "rating": feedback.rating,
                "memories_affected": updates.memories_updated
            },
            source="active_learning"
        )
        
        # Trigger consolidation if needed
        if updates.consolidation_triggered:
            await EventBus.publish(
                "rag.consolidation_trigger",
                {"confidence_threshold": 0.8},
                source="active_learning"
            )
        
        return updates

# KnowledgeRAG subscribes to learning events
async def handle_feedback_event(event: Event):
    user_id = event.data["user_id"]
    rating = event.data.get("rating", 0)
    
    # Update confidence scores
    if rating >= 4:
        await rag.boost_confidence(user_id, boost=0.1)
    elif rating <= 2:
        await rag.decrease_confidence(user_id, decrease=0.1)

EventBus.subscribe("learning.feedback_received", handle_feedback_event)
```

---

## 🧪 Testing Integration Components

```python
import pytest
from hlcs.integration import (
    FeatureFlags,
    EventBus,
    validate_contract_implementation
)

class TestMyEmotionSystem:
    @pytest.mark.asyncio
    async def test_feature_flag_control(self):
        # Disable feature
        FeatureFlags.set("emotion_system", enabled=False)
        
        system = MyEmotionSystem()
        result = await system.analyze_sentiment("Test")
        
        assert result is None  # Should return None when disabled
        
        # Enable feature
        FeatureFlags.set("emotion_system", enabled=True)
        result = await system.analyze_sentiment("Test")
        
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_event_publishing(self):
        await EventBus.initialize()
        
        events_received = []
        
        async def handler(event):
            events_received.append(event)
        
        EventBus.subscribe("emotion.*", handler)
        
        # Trigger analysis
        system = MyEmotionSystem()
        await system.analyze_sentiment("Happy text!")
        
        await asyncio.sleep(0.1)
        
        assert len(events_received) == 1
        assert events_received[0].topic == "emotion.sentiment_analyzed"
        
        await EventBus.shutdown()
    
    def test_contract_compliance(self):
        system = MyEmotionSystem()
        is_valid, errors = validate_contract_implementation(
            system,
            EmotionIntegrationContract
        )
        
        assert is_valid, f"Contract errors: {errors}"
```

---

## 📊 Monitoring & Debugging

### Feature Flag Status

```bash
# Check all flags in REST API
curl http://localhost:4001/api/v1/integration/flags

# Response:
{
  "emotion_system": {
    "enabled": true,
    "rollout": 25.0,
    "strategy": "PERCENTAGE"
  },
  ...
}
```

### Event Bus Health

```bash
# Check event bus stats
curl http://localhost:4001/api/v1/integration/events/stats

# Response:
{
  "events_published": 1523,
  "subscribers_total": 12,
  "queue_size": 0,
  "dead_letter_queue_size": 0
}
```

### Logging

```python
import logging

# Enable debug logging
logging.getLogger("hlcs.integration.feature_flags").setLevel(logging.DEBUG)
logging.getLogger("hlcs.integration.event_bus").setLevel(logging.DEBUG)

# Output:
# INFO:hlcs.integration.feature_flags:Feature flag 'emotion_system' set to True
# DEBUG:hlcs.integration.event_bus:Event published: rag.consolidation from knowledge_rag
```

---

## 🚀 Next Steps

1. **Phase 1** (Day 3-5): Integrate Emotion System
   - Enable `emotion_system` flag
   - Subscribe to emotion events in Meta-Consciousness
   - Add emotion context to orchestrator

2. **Phase 2** (Day 6-8): Add Enhanced Monitoring
   - Enable `monitoring_enhanced` flag
   - Implement Prometheus metrics
   - Add health checks

3. **Phase 3** (Day 9-11): Integrate Meta-Reasoner (COEXIST)
   - Enable `meta_reasoner` flag
   - Subscribe to reasoning events in Planning
   - Add CoT traces to ScenarioSimulator

4. **Phase 4** (Day 12-14): Integrate Active Learning (COEXIST)
   - Enable `active_learning` flag
   - Subscribe to learning events in KnowledgeRAG
   - Add feedback endpoints to REST API

---

## 📚 References

- [MIGRATION_CONFLICT_ANALYSIS.md](./MIGRATION_CONFLICT_ANALYSIS.md) - Collision analysis
- [ADR-001-MIGRATION-STRATEGY.md](./ADR-001-MIGRATION-STRATEGY.md) - Architecture decision
- [SARAI_AGI_MIGRATION_STATUS.md](./SARAI_AGI_MIGRATION_STATUS.md) - Migration status

---

**Document Version**: 1.0.0  
**Last Updated**: 8 de noviembre de 2025  
**Status**: 🟢 READY FOR USE
