"""
Event Bus for HLCS Component Integration

Async event-driven architecture for loose coupling between HLCS components
and migrated sarai-agi systems. Enables COEXIST strategy where components
communicate via events without tight coupling.

Key Use Cases:
1. Meta-Reasoner → Strategic Planning (reasoning events feed scenarios)
2. Active Learning → KnowledgeRAG (consolidation triggers)
3. Emotion System → Meta-Consciousness (emotional context for decisions)
4. Monitoring → All components (telemetry collection)

Example:
    # Publisher (Active Learning)
    await EventBus.publish("learning.feedback_received", {
        "user_id": "user_123",
        "feedback": "positive",
        "memory_id": "mem_456"
    })
    
    # Subscriber (KnowledgeRAG)
    async def handle_feedback(event: Event):
        memory_id = event.data["memory_id"]
        await rag.update_confidence(memory_id, boost=0.1)
    
    EventBus.subscribe("learning.feedback_received", handle_feedback)
"""

import asyncio
import logging
from enum import Enum
from typing import Dict, Any, Callable, Awaitable, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)


class EventPriority(Enum):
    """Event priority levels for processing order"""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


@dataclass
class Event:
    """
    Event data structure for inter-component communication.
    
    Event naming convention: <component>.<action>
    Examples:
    - rag.consolidation_completed
    - planning.goal_achieved
    - reasoning.hypothesis_validated
    - learning.feedback_received
    - emotion.mood_changed
    """
    topic: str
    data: Dict[str, Any]
    priority: EventPriority = EventPriority.NORMAL
    source: str = "unknown"
    timestamp: datetime = field(default_factory=datetime.now)
    event_id: str = field(default_factory=lambda: f"evt_{datetime.now().timestamp()}")
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate event structure"""
        if not self.topic:
            raise ValueError("Event topic cannot be empty")
        if not isinstance(self.data, dict):
            raise ValueError("Event data must be a dictionary")


@dataclass
class EventSubscriber:
    """Subscriber configuration"""
    callback: Callable[[Event], Awaitable[None]]
    topic_pattern: str
    priority: EventPriority = EventPriority.NORMAL
    filter_func: Optional[Callable[[Event], bool]] = None
    subscriber_id: str = field(default_factory=lambda: f"sub_{datetime.now().timestamp()}")


class EventBus:
    """
    Async event bus for component integration.
    
    Features:
    - Topic-based pub/sub
    - Priority-based processing
    - Wildcard topic patterns (e.g., "rag.*")
    - Event filtering
    - Dead letter queue for failed events
    - Event replay for debugging
    
    Thread-safe and async-first design.
    """
    
    _subscribers: Dict[str, List[EventSubscriber]] = defaultdict(list)
    _event_history: List[Event] = []
    _max_history: int = 1000
    _dead_letter_queue: List[tuple[Event, Exception]] = []
    _event_queue: asyncio.Queue = asyncio.Queue()
    _processing_task: Optional[asyncio.Task] = None
    _initialized: bool = False
    _stats: Dict[str, int] = defaultdict(int)
    
    @classmethod
    async def initialize(cls) -> None:
        """Initialize event bus and start processing"""
        if cls._initialized:
            return
        
        cls._event_queue = asyncio.Queue()
        cls._processing_task = asyncio.create_task(cls._process_events())
        cls._initialized = True
        logger.info("EventBus initialized and processing started")
    
    @classmethod
    async def shutdown(cls) -> None:
        """Gracefully shutdown event bus"""
        if not cls._initialized:
            return
        
        logger.info("Shutting down EventBus...")
        
        # Wait for queue to drain
        await cls._event_queue.join()
        
        # Cancel processing task
        if cls._processing_task:
            cls._processing_task.cancel()
            try:
                await cls._processing_task
            except asyncio.CancelledError:
                pass
        
        cls._initialized = False
        logger.info(f"EventBus shutdown complete. Stats: {dict(cls._stats)}")
    
    @classmethod
    async def publish(
        cls,
        topic: str,
        data: Dict[str, Any],
        priority: EventPriority = EventPriority.NORMAL,
        source: str = "unknown",
        **metadata
    ) -> None:
        """
        Publish an event to the bus.
        
        Args:
            topic: Event topic (e.g., "rag.consolidation")
            data: Event payload
            priority: Processing priority
            source: Source component name
            **metadata: Additional metadata
        """
        if not cls._initialized:
            await cls.initialize()
        
        event = Event(
            topic=topic,
            data=data,
            priority=priority,
            source=source,
            metadata=metadata
        )
        
        # Add to history
        cls._event_history.append(event)
        if len(cls._event_history) > cls._max_history:
            cls._event_history.pop(0)
        
        # Queue for processing
        await cls._event_queue.put(event)
        cls._stats["events_published"] += 1
        
        logger.debug(f"Event published: {topic} from {source} (priority={priority.name})")
    
    @classmethod
    def subscribe(
        cls,
        topic_pattern: str,
        callback: Callable[[Event], Awaitable[None]],
        priority: EventPriority = EventPriority.NORMAL,
        filter_func: Optional[Callable[[Event], bool]] = None
    ) -> str:
        """
        Subscribe to events matching topic pattern.
        
        Args:
            topic_pattern: Topic pattern (supports wildcards: "rag.*")
            callback: Async function to call on event
            priority: Subscriber priority
            filter_func: Optional filter function
        
        Returns:
            Subscriber ID for unsubscribing
        """
        subscriber = EventSubscriber(
            callback=callback,
            topic_pattern=topic_pattern,
            priority=priority,
            filter_func=filter_func
        )
        
        cls._subscribers[topic_pattern].append(subscriber)
        cls._stats["subscribers_total"] += 1
        
        logger.info(f"Subscriber registered: {topic_pattern} (id={subscriber.subscriber_id})")
        return subscriber.subscriber_id
    
    @classmethod
    def unsubscribe(cls, subscriber_id: str) -> bool:
        """
        Unsubscribe a subscriber by ID.
        
        Returns:
            True if unsubscribed, False if not found
        """
        for topic_pattern, subscribers in cls._subscribers.items():
            for subscriber in subscribers:
                if subscriber.subscriber_id == subscriber_id:
                    subscribers.remove(subscriber)
                    cls._stats["subscribers_total"] -= 1
                    logger.info(f"Subscriber unsubscribed: {subscriber_id}")
                    return True
        
        logger.warning(f"Subscriber not found: {subscriber_id}")
        return False
    
    @classmethod
    async def _process_events(cls) -> None:
        """Background task to process events from queue"""
        logger.info("Event processing task started")
        
        while True:
            try:
                event = await cls._event_queue.get()
                await cls._dispatch_event(event)
                cls._event_queue.task_done()
            except asyncio.CancelledError:
                logger.info("Event processing task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in event processing loop: {e}", exc_info=True)
    
    @classmethod
    async def _dispatch_event(cls, event: Event) -> None:
        """Dispatch event to matching subscribers"""
        matched_subscribers: List[EventSubscriber] = []
        
        # Find matching subscribers
        for topic_pattern, subscribers in cls._subscribers.items():
            if cls._matches_pattern(event.topic, topic_pattern):
                for subscriber in subscribers:
                    # Apply filter if provided
                    if subscriber.filter_func and not subscriber.filter_func(event):
                        continue
                    matched_subscribers.append(subscriber)
        
        if not matched_subscribers:
            logger.debug(f"No subscribers for event: {event.topic}")
            return
        
        # Sort by priority
        matched_subscribers.sort(key=lambda s: s.priority.value, reverse=True)
        
        # Dispatch to all subscribers
        cls._stats["events_dispatched"] += 1
        for subscriber in matched_subscribers:
            try:
                await subscriber.callback(event)
                cls._stats["callbacks_succeeded"] += 1
            except Exception as e:
                cls._stats["callbacks_failed"] += 1
                logger.error(
                    f"Error in subscriber callback for {event.topic}: {e}",
                    exc_info=True
                )
                cls._dead_letter_queue.append((event, e))
    
    @classmethod
    def _matches_pattern(cls, topic: str, pattern: str) -> bool:
        """
        Check if topic matches pattern.
        
        Supports:
        - Exact match: "rag.consolidation" == "rag.consolidation"
        - Wildcard: "rag.*" matches "rag.consolidation", "rag.search", etc.
        - Multi-level wildcard: "**" matches all topics
        """
        if pattern == "**":
            return True
        
        if "*" not in pattern:
            return topic == pattern
        
        # Simple wildcard matching
        pattern_parts = pattern.split(".")
        topic_parts = topic.split(".")
        
        if len(pattern_parts) != len(topic_parts):
            return False
        
        for pattern_part, topic_part in zip(pattern_parts, topic_parts):
            if pattern_part == "*":
                continue
            if pattern_part != topic_part:
                return False
        
        return True
    
    @classmethod
    def get_stats(cls) -> Dict[str, Any]:
        """Get event bus statistics"""
        return {
            "initialized": cls._initialized,
            "events_published": cls._stats["events_published"],
            "events_dispatched": cls._stats["events_dispatched"],
            "callbacks_succeeded": cls._stats["callbacks_succeeded"],
            "callbacks_failed": cls._stats["callbacks_failed"],
            "subscribers_total": cls._stats["subscribers_total"],
            "queue_size": cls._event_queue.qsize(),
            "history_size": len(cls._event_history),
            "dead_letter_queue_size": len(cls._dead_letter_queue),
        }
    
    @classmethod
    def get_event_history(cls, limit: int = 100) -> List[Event]:
        """Get recent event history"""
        return cls._event_history[-limit:]
    
    @classmethod
    def get_dead_letter_queue(cls) -> List[tuple[Event, Exception]]:
        """Get failed events from dead letter queue"""
        return cls._dead_letter_queue.copy()
    
    @classmethod
    def clear_dead_letter_queue(cls) -> None:
        """Clear dead letter queue"""
        cls._dead_letter_queue.clear()
        logger.info("Dead letter queue cleared")


# Predefined event topics for migration components
class EventTopics:
    """Standard event topics for HLCS integration"""
    
    # KnowledgeRAG events
    RAG_MEMORY_ADDED = "rag.memory_added"
    RAG_CONSOLIDATION_STARTED = "rag.consolidation_started"
    RAG_CONSOLIDATION_COMPLETED = "rag.consolidation_completed"
    RAG_SEARCH_PERFORMED = "rag.search_performed"
    
    # Strategic Planning events
    PLANNING_GOAL_CREATED = "planning.goal_created"
    PLANNING_GOAL_COMPLETED = "planning.goal_completed"
    PLANNING_GOAL_FAILED = "planning.goal_failed"
    PLANNING_PLAN_EXECUTED = "planning.plan_executed"
    PLANNING_MILESTONE_REACHED = "planning.milestone_reached"
    
    # Meta-Consciousness events
    META_DECISION_MADE = "meta.decision_made"
    META_IGNORANCE_DETECTED = "meta.ignorance_detected"
    META_CONFIDENCE_CHANGED = "meta.confidence_changed"
    META_NARRATIVE_CREATED = "meta.narrative_created"
    
    # SCI events
    SCI_VOTE_CAST = "sci.vote_cast"
    SCI_CONSENSUS_REACHED = "sci.consensus_reached"
    SCI_CONFLICT_DETECTED = "sci.conflict_detected"
    
    # Meta-Reasoner events (future)
    REASONING_CHAIN_STARTED = "reasoning.chain_started"
    REASONING_CHAIN_COMPLETED = "reasoning.chain_completed"
    REASONING_HYPOTHESIS_PROPOSED = "reasoning.hypothesis_proposed"
    REASONING_HYPOTHESIS_VALIDATED = "reasoning.hypothesis_validated"
    
    # Active Learning events (future)
    LEARNING_FEEDBACK_RECEIVED = "learning.feedback_received"
    LEARNING_PREFERENCE_UPDATED = "learning.preference_updated"
    LEARNING_MODEL_UPDATED = "learning.model_updated"
    
    # Emotion System events (future)
    EMOTION_MOOD_CHANGED = "emotion.mood_changed"
    EMOTION_SENTIMENT_ANALYZED = "emotion.sentiment_analyzed"
    
    # Monitoring events
    MONITORING_METRIC_RECORDED = "monitoring.metric_recorded"
    MONITORING_ALERT_TRIGGERED = "monitoring.alert_triggered"
