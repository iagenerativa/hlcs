"""
Tests for HLCS Integration Infrastructure

Tests feature flags, event bus, and integration contracts.
"""

import pytest
import asyncio
from datetime import datetime
from typing import Dict, Any

from src.hlcs.integration import (
    FeatureFlags,
    FeatureFlag,
    EventBus,
    Event,
    EventPriority,
    EventTopics,
    IntegrationContract,
    EmotionIntegrationContract,
    EmotionResponse,
    SentimentPolarity,
    validate_contract_implementation,
)
from src.hlcs.integration.feature_flags import RolloutStrategy


# ==================== Feature Flags Tests ====================

class TestFeatureFlags:
    """Test feature flags system"""
    
    def setup_method(self):
        """Reset feature flags before each test"""
        # Reset singleton state completely
        FeatureFlags._initialized = False
        FeatureFlags._flags = {}
        # Force reinitialization
        FeatureFlags.initialize()
    
    def test_feature_flags_initialization(self):
        """Test feature flags are initialized with defaults"""
        FeatureFlags.initialize()
        
        flags = FeatureFlags.list_all()
        assert len(flags) > 0
        
        # Check migration flags exist
        assert "emotion_system" in flags
        assert "meta_reasoner" in flags
        assert "active_learning" in flags
        assert "monitoring_enhanced" in flags
        assert "integrated_consciousness" in flags
        assert "lora_trainer" in flags
    
    def test_feature_flag_default_disabled(self):
        """Test all migration flags start disabled"""
        FeatureFlags.initialize()
        
        assert not FeatureFlags.is_enabled("emotion_system")
        assert not FeatureFlags.is_enabled("meta_reasoner")
        assert not FeatureFlags.is_enabled("active_learning")
    
    def test_feature_flag_set_enabled(self):
        """Test enabling feature flag at runtime"""
        FeatureFlags.initialize()
        
        # Start disabled
        assert not FeatureFlags.is_enabled("emotion_system")
        
        # Enable with full rollout
        FeatureFlags.set("emotion_system", enabled=True, strategy=RolloutStrategy.ALL)
        assert FeatureFlags.is_enabled("emotion_system")
        
        # Disable again
        FeatureFlags.set("emotion_system", enabled=False)
        assert not FeatureFlags.is_enabled("emotion_system")
    
    def test_feature_flag_rollout_percentage(self):
        """Test gradual rollout with percentage"""
        FeatureFlags.initialize()
        
        # Set 50% rollout
        FeatureFlags.set("emotion_system", enabled=True)
        FeatureFlags.set_rollout_percentage("emotion_system", 50.0)
        
        flag = FeatureFlags.get("emotion_system")
        assert flag.rollout_percentage == 50.0
        
        # Test user-specific rollout
        enabled_count = 0
        for i in range(100):
            user_id = f"user_{i}"
            if FeatureFlags.is_enabled("emotion_system", user_id=user_id):
                enabled_count += 1
        
        # Should be approximately 50% (allow 20% variance)
        assert 30 <= enabled_count <= 70
    
    def test_feature_flag_metadata(self):
        """Test feature flag metadata"""
        FeatureFlags.initialize()
        
        flag = FeatureFlags.get("emotion_system")
        assert flag.metadata["phase"] == 1
        assert flag.metadata["risk"] == "LOW"
        assert flag.metadata["strategy"] == "MIGRATE"
        
        flag = FeatureFlags.get("lora_trainer")
        assert flag.metadata["strategy"] == "DEFER"
        assert flag.metadata["defer_until"] == "v0.4"
    
    def test_migration_status(self):
        """Test migration status summary"""
        FeatureFlags.initialize()
        
        status = FeatureFlags.get_migration_status()
        
        assert "phase_1_migrate" in status
        assert "phase_2_coexist" in status
        assert "phase_4_deferred" in status
        assert status["total_flags"] == 6
        assert status["total_enabled"] == 0  # All start disabled


# ==================== Event Bus Tests ====================

class TestEventBus:
    """Test event bus system"""
    
    @pytest.mark.asyncio
    async def test_event_bus_initialization(self):
        """Test event bus initializes correctly"""
        await EventBus.initialize()
        
        stats = EventBus.get_stats()
        assert stats["initialized"] is True
        
        await EventBus.shutdown()
    
    @pytest.mark.asyncio
    async def test_publish_and_subscribe(self):
        """Test basic pub/sub functionality"""
        await EventBus.initialize()
        
        received_events = []
        
        async def handler(event: Event):
            received_events.append(event)
        
        # Subscribe
        sub_id = EventBus.subscribe("test.event", handler)
        
        # Publish
        await EventBus.publish("test.event", {"message": "hello"}, source="test")
        
        # Wait for processing
        await asyncio.sleep(0.1)
        
        # Verify
        assert len(received_events) == 1
        assert received_events[0].topic == "test.event"
        assert received_events[0].data["message"] == "hello"
        
        # Cleanup
        EventBus.unsubscribe(sub_id)
        await EventBus.shutdown()
    
    @pytest.mark.asyncio
    async def test_wildcard_subscription(self):
        """Test wildcard topic patterns"""
        await EventBus.initialize()
        
        received_events = []
        
        async def handler(event: Event):
            received_events.append(event)
        
        # Subscribe to wildcard
        EventBus.subscribe("rag.*", handler)
        
        # Publish multiple matching events
        await EventBus.publish("rag.consolidation", {}, source="test")
        await EventBus.publish("rag.search", {}, source="test")
        await EventBus.publish("planning.goal", {}, source="test")  # Should NOT match
        
        await asyncio.sleep(0.1)
        
        # Should receive only "rag.*" events
        assert len(received_events) == 2
        assert all(e.topic.startswith("rag.") for e in received_events)
        
        await EventBus.shutdown()
    
    @pytest.mark.asyncio
    async def test_event_priority(self):
        """Test priority-based event processing"""
        await EventBus.initialize()
        
        processing_order = []
        
        async def high_priority_handler(event: Event):
            processing_order.append("high")
        
        async def low_priority_handler(event: Event):
            processing_order.append("low")
        
        # Subscribe with different priorities
        EventBus.subscribe("test.priority", high_priority_handler, priority=EventPriority.HIGH)
        EventBus.subscribe("test.priority", low_priority_handler, priority=EventPriority.LOW)
        
        # Publish event
        await EventBus.publish("test.priority", {}, source="test")
        await asyncio.sleep(0.2)
        
        # High priority should process first
        assert processing_order[0] == "high"
        
        await EventBus.shutdown()
    
    @pytest.mark.asyncio
    async def test_event_filter(self):
        """Test event filtering"""
        await EventBus.initialize()
        
        received_events = []
        
        async def handler(event: Event):
            received_events.append(event)
        
        # Subscribe with filter
        def only_important(event: Event) -> bool:
            return event.data.get("important", False)
        
        EventBus.subscribe("test.filtered", handler, filter_func=only_important)
        
        # Publish events
        await EventBus.publish("test.filtered", {"important": True}, source="test")
        await EventBus.publish("test.filtered", {"important": False}, source="test")
        await EventBus.publish("test.filtered", {}, source="test")
        
        await asyncio.sleep(0.2)
        
        # Should receive only filtered events
        assert len(received_events) == 1
        assert received_events[0].data["important"] is True
        
        await EventBus.shutdown()
    
    @pytest.mark.asyncio
    async def test_event_statistics(self):
        """Test event bus statistics tracking"""
        await EventBus.initialize()
        
        async def handler(event: Event):
            pass
        
        EventBus.subscribe("test.stats", handler)
        
        await EventBus.publish("test.stats", {}, source="test")
        await EventBus.publish("test.stats", {}, source="test")
        await asyncio.sleep(0.2)
        
        stats = EventBus.get_stats()
        assert stats["events_published"] >= 2
        assert stats["events_dispatched"] >= 2
        assert stats["subscribers_total"] >= 1
        
        await EventBus.shutdown()
    
    @pytest.mark.asyncio
    async def test_event_history(self):
        """Test event history tracking"""
        await EventBus.initialize()
        
        await EventBus.publish("test.history", {"value": 1}, source="test")
        await EventBus.publish("test.history", {"value": 2}, source="test")
        
        history = EventBus.get_event_history(limit=10)
        assert len(history) >= 2
        
        recent_events = [e for e in history if e.topic == "test.history"]
        assert len(recent_events) >= 2
        
        await EventBus.shutdown()


# ==================== Integration Contracts Tests ====================

class MockEmotionSystem(EmotionIntegrationContract):
    """Mock implementation for testing"""
    
    async def initialize(self, config: Dict[str, Any]) -> None:
        self.config = config
    
    async def shutdown(self) -> None:
        pass
    
    async def health_check(self) -> Dict[str, Any]:
        return {"status": "healthy", "timestamp": datetime.now().isoformat()}
    
    def get_stats(self) -> Dict[str, Any]:
        return {"total_analyses": 100}
    
    async def analyze_sentiment(self, text: str, context=None) -> EmotionResponse:
        return EmotionResponse(
            sentiment_polarity=SentimentPolarity.POSITIVE,
            sentiment_score=0.8,
            dominant_emotion="joy",
            emotion_scores={"joy": 0.8, "excitement": 0.6},
            mood="happy",
            confidence=0.9
        )
    
    async def get_current_mood(self, user_id=None) -> Dict[str, Any]:
        return {"mood": "calm", "mood_score": 0.7}
    
    async def update_mood(self, interaction_result: Dict[str, Any]) -> None:
        pass


class TestIntegrationContracts:
    """Test integration contracts"""
    
    @pytest.mark.asyncio
    async def test_emotion_contract_implementation(self):
        """Test emotion contract implementation"""
        system = MockEmotionSystem()
        
        # Initialize
        await system.initialize({"model": "test"})
        assert system.config["model"] == "test"
        
        # Analyze sentiment
        result = await system.analyze_sentiment("I love this!")
        assert isinstance(result, EmotionResponse)
        assert result.sentiment_polarity == SentimentPolarity.POSITIVE
        assert result.sentiment_score == 0.8
        assert result.dominant_emotion == "joy"
        assert result.confidence == 0.9
        
        # Get mood
        mood = await system.get_current_mood()
        assert mood["mood"] == "calm"
        
        # Health check
        health = await system.health_check()
        assert health["status"] == "healthy"
        
        # Stats
        stats = system.get_stats()
        assert "total_analyses" in stats
        
        await system.shutdown()
    
    def test_contract_validation(self):
        """Test contract validation"""
        system = MockEmotionSystem()
        
        is_valid, errors = validate_contract_implementation(
            system,
            EmotionIntegrationContract
        )
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_contract_validation_failure(self):
        """Test contract validation with invalid implementation"""
        
        class IncompleteSystem:
            pass
        
        system = IncompleteSystem()
        
        is_valid, errors = validate_contract_implementation(
            system,
            EmotionIntegrationContract
        )
        
        assert is_valid is False
        assert len(errors) > 0


# ==================== Integration Tests ====================

class TestIntegrationInfrastructure:
    """Test integration between feature flags, event bus, and contracts"""
    
    def setup_method(self):
        """Reset state before each test"""
        FeatureFlags._initialized = False
        FeatureFlags._flags = {}
    
    @pytest.mark.asyncio
    async def test_feature_flag_with_event_bus(self):
        """Test feature flag control with event bus"""
        # Initialize fresh EventBus for this test
        if EventBus._initialized:
            await EventBus.shutdown()
        
        await EventBus.initialize()
        FeatureFlags.initialize()
        
        events_received = []
        
        async def handler(event: Event):
            events_received.append(event)
        
        EventBus.subscribe("emotion.*", handler)
        
        # Feature disabled - should not publish
        if FeatureFlags.is_enabled("emotion_system"):
            await EventBus.publish("emotion.analyzed", {}, source="test")
        
        await asyncio.sleep(0.2)
        assert len(events_received) == 0
        
        # Enable feature with ALL strategy
        FeatureFlags.set("emotion_system", enabled=True, strategy=RolloutStrategy.ALL)
        
        # Feature enabled - should publish
        if FeatureFlags.is_enabled("emotion_system"):
            await EventBus.publish("emotion.analyzed", {}, source="test")
        
        await asyncio.sleep(0.2)
        assert len(events_received) == 1
        
        await EventBus.shutdown()
    
    @pytest.mark.asyncio
    async def test_contract_with_event_bus(self):
        """Test integration contract publishing events"""
        # Initialize fresh EventBus
        if EventBus._initialized:
            await EventBus.shutdown()
        
        await EventBus.initialize()
        
        events_received = []
        
        async def handler(event: Event):
            events_received.append(event)
        
        EventBus.subscribe("emotion.sentiment_analyzed", handler)
        
        # Use mock system
        system = MockEmotionSystem()
        await system.initialize({})
        
        # Analyze and publish event
        result = await system.analyze_sentiment("Test text")
        await EventBus.publish(
            EventTopics.EMOTION_SENTIMENT_ANALYZED,
            {
                "sentiment": result.sentiment_polarity.name,
                "score": result.sentiment_score,
                "confidence": result.confidence
            },
            source="emotion_system"
        )
        
        await asyncio.sleep(0.2)
        
        assert len(events_received) == 1
        assert events_received[0].data["sentiment"] == "POSITIVE"
        assert events_received[0].data["score"] == 0.8
        
        await system.shutdown()
        await EventBus.shutdown()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
