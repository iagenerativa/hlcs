"""
Feature Flags System for HLCS Integration

Runtime toggles for safe rollout of new components from sarai-agi migration.
Supports:
- Environment-based configuration
- Dynamic runtime updates
- Rollback without code changes
- A/B testing for component selection

Example:
    # In code
    if FeatureFlags.is_enabled("emotion_system"):
        emotion_result = await emotion_engine.analyze(text)
    
    # Environment variable
    export HLCS_FEATURE_EMOTION_SYSTEM=true
    
    # Runtime toggle
    FeatureFlags.set("emotion_system", enabled=False)
"""

import os
import logging
from enum import Enum
from typing import Dict, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


class RolloutStrategy(Enum):
    """Feature rollout strategies"""
    ALL = "all"  # Enabled for all users
    NONE = "none"  # Disabled for all users
    PERCENTAGE = "percentage"  # Enable for X% of users
    WHITELIST = "whitelist"  # Enable for specific user_ids
    GRADUAL = "gradual"  # Gradually increase percentage over time


@dataclass
class FeatureFlag:
    """Individual feature flag configuration"""
    name: str
    enabled: bool = False
    description: str = ""
    strategy: RolloutStrategy = RolloutStrategy.ALL
    rollout_percentage: float = 100.0  # 0-100
    whitelist: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_enabled_for_user(self, user_id: Optional[str] = None) -> bool:
        """Check if feature is enabled for specific user"""
        if not self.enabled:
            return False
        
        if self.strategy == RolloutStrategy.NONE:
            return False
        
        if self.strategy == RolloutStrategy.ALL:
            return True
        
        if self.strategy == RolloutStrategy.WHITELIST:
            return user_id in self.whitelist if user_id else False
        
        if self.strategy == RolloutStrategy.PERCENTAGE:
            # Simple hash-based percentage rollout
            if user_id:
                user_hash = hash(user_id) % 100
                return user_hash < self.rollout_percentage
            return False
        
        return self.enabled


class FeatureFlags:
    """
    Global feature flags registry for HLCS integration components.
    
    Predefined flags for sarai-agi migration:
    - emotion_system: Emotion System v0.3
    - meta_reasoner: Meta-Reasoner v0.2 (CoT reasoning)
    - active_learning: Active Learning v0.4 (feedback loops)
    - monitoring_enhanced: Enhanced Monitoring & Observability
    - integrated_consciousness: IntegratedConsciousness v0.3 (future)
    - lora_trainer: LoRA Fine-tuning Trainer (future)
    """
    
    _flags: Dict[str, FeatureFlag] = {}
    _initialized: bool = False
    
    # Default flags for migration components
    _MIGRATION_FLAGS = {
        "emotion_system": FeatureFlag(
            name="emotion_system",
            enabled=False,  # Start disabled, enable after Phase 1
            description="Emotion System v0.3 from sarai-agi (MIGRATE strategy)",
            strategy=RolloutStrategy.PERCENTAGE,
            rollout_percentage=0.0,  # Gradual rollout 0→25→50→100
            metadata={"phase": 1, "risk": "LOW", "strategy": "MIGRATE"}
        ),
        "meta_reasoner": FeatureFlag(
            name="meta_reasoner",
            enabled=False,
            description="Meta-Reasoner v0.2 CoT reasoning (COEXIST strategy)",
            strategy=RolloutStrategy.PERCENTAGE,
            rollout_percentage=0.0,
            metadata={"phase": 2, "risk": "MEDIUM", "strategy": "COEXIST"}
        ),
        "active_learning": FeatureFlag(
            name="active_learning",
            enabled=False,
            description="Active Learning v0.4 feedback loops (COEXIST strategy)",
            strategy=RolloutStrategy.PERCENTAGE,
            rollout_percentage=0.0,
            metadata={"phase": 2, "risk": "MEDIUM", "strategy": "COEXIST"}
        ),
        "monitoring_enhanced": FeatureFlag(
            name="monitoring_enhanced",
            enabled=False,
            description="Enhanced Monitoring & Observability (MIGRATE strategy)",
            strategy=RolloutStrategy.ALL,
            metadata={"phase": 1, "risk": "LOW", "strategy": "MIGRATE"}
        ),
        "integrated_consciousness": FeatureFlag(
            name="integrated_consciousness",
            enabled=False,
            description="IntegratedConsciousness v0.3 (DEFER to v0.4)",
            strategy=RolloutStrategy.NONE,
            metadata={"phase": 4, "risk": "HIGH", "strategy": "MERGE", "defer_until": "v0.4"}
        ),
        "lora_trainer": FeatureFlag(
            name="lora_trainer",
            enabled=False,
            description="LoRA Fine-tuning Trainer (DEFER to v0.4)",
            strategy=RolloutStrategy.NONE,
            metadata={"phase": 4, "risk": "CRITICAL", "strategy": "DEFER", "defer_until": "v0.4"}
        ),
    }
    
    @classmethod
    def initialize(cls) -> None:
        """Initialize feature flags from environment and defaults"""
        if cls._initialized:
            return
        
        # Load default migration flags (make a deep copy)
        import copy
        cls._flags = copy.deepcopy(cls._MIGRATION_FLAGS)
        
        # Override from environment variables
        # Format: HLCS_FEATURE_<FLAG_NAME>=true|false
        for flag_name in cls._flags.keys():
            env_var = f"HLCS_FEATURE_{flag_name.upper()}"
            env_value = os.getenv(env_var)
            
            if env_value is not None:
                enabled = env_value.lower() in ("true", "1", "yes", "on")
                cls._flags[flag_name].enabled = enabled
                logger.info(f"Feature flag '{flag_name}' set to {enabled} from {env_var}")
        
        cls._initialized = True
        logger.info(f"Feature flags initialized: {len(cls._flags)} flags loaded")
    
    @classmethod
    def is_enabled(cls, flag_name: str, user_id: Optional[str] = None) -> bool:
        """
        Check if a feature flag is enabled.
        
        Args:
            flag_name: Name of the feature flag
            user_id: Optional user ID for user-specific rollout
        
        Returns:
            True if enabled, False otherwise
        """
        if not cls._initialized:
            cls.initialize()
        
        flag = cls._flags.get(flag_name)
        if not flag:
            logger.warning(f"Unknown feature flag: {flag_name}")
            return False
        
        return flag.is_enabled_for_user(user_id)
    
    @classmethod
    def set(cls, flag_name: str, enabled: bool, **kwargs) -> None:
        """
        Update a feature flag at runtime.
        
        Args:
            flag_name: Name of the feature flag
            enabled: New enabled state
            **kwargs: Additional flag properties to update
        """
        if not cls._initialized:
            cls.initialize()
        
        if flag_name not in cls._flags:
            logger.error(f"Cannot set unknown feature flag: {flag_name}")
            return
        
        flag = cls._flags[flag_name]
        flag.enabled = enabled
        flag.updated_at = datetime.now()
        
        # Update additional properties
        for key, value in kwargs.items():
            if hasattr(flag, key):
                setattr(flag, key, value)
        
        logger.info(f"Feature flag '{flag_name}' updated: enabled={enabled}, kwargs={kwargs}")
    
    @classmethod
    def set_rollout_percentage(cls, flag_name: str, percentage: float) -> None:
        """
        Update rollout percentage for gradual rollout.
        
        Example:
            # Start at 0%
            FeatureFlags.set_rollout_percentage("emotion_system", 0.0)
            # Increase to 25%
            FeatureFlags.set_rollout_percentage("emotion_system", 25.0)
            # Full rollout
            FeatureFlags.set_rollout_percentage("emotion_system", 100.0)
        """
        if not cls._initialized:
            cls.initialize()
        
        if flag_name not in cls._flags:
            logger.error(f"Cannot set rollout for unknown flag: {flag_name}")
            return
        
        cls._flags[flag_name].rollout_percentage = max(0.0, min(100.0, percentage))
        cls._flags[flag_name].updated_at = datetime.now()
        logger.info(f"Feature flag '{flag_name}' rollout set to {percentage}%")
    
    @classmethod
    def get(cls, flag_name: str) -> Optional[FeatureFlag]:
        """Get feature flag details"""
        if not cls._initialized:
            cls.initialize()
        return cls._flags.get(flag_name)
    
    @classmethod
    def list_all(cls) -> Dict[str, FeatureFlag]:
        """Get all feature flags"""
        if not cls._initialized:
            cls.initialize()
        return cls._flags.copy()
    
    @classmethod
    def get_migration_status(cls) -> Dict[str, Any]:
        """
        Get status of all migration-related feature flags.
        
        Returns:
            Dict with migration phase breakdown and enabled flags
        """
        if not cls._initialized:
            cls.initialize()
        
        phase_1 = []
        phase_2 = []
        deferred = []
        
        for flag_name, flag in cls._flags.items():
            phase = flag.metadata.get("phase", 0)
            status = {
                "name": flag_name,
                "enabled": flag.enabled,
                "strategy": flag.metadata.get("strategy", "UNKNOWN"),
                "rollout": flag.rollout_percentage,
            }
            
            if phase == 1:
                phase_1.append(status)
            elif phase == 2:
                phase_2.append(status)
            elif phase == 4:
                deferred.append(status)
        
        return {
            "phase_1_migrate": phase_1,
            "phase_2_coexist": phase_2,
            "phase_4_deferred": deferred,
            "total_enabled": sum(1 for f in cls._flags.values() if f.enabled),
            "total_flags": len(cls._flags),
        }


# Auto-initialize on import
FeatureFlags.initialize()
