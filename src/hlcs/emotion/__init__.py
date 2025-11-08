"""
HLCS Emotion System
===================

Migrated from sarai-agi as part of HYBRID APPROACH strategy.
See: /home/noel/hlcs/docs/ADR-001-MIGRATION-STRATEGY.md

Features:
- 16 emotional contexts detection
- 8 cultural contexts (regional adaptations)
- Time-based contextual awareness
- User profiling and learning
- Voice modulation recommendations

Integration with HLCS v3.0:
- Meta-Consciousness: Emotional context for decision strategies
- SCI: Emotional awareness for stakeholder consensus
- Planning: Mood-aware goal prioritization

Version: Migrated from sarai-agi v3.5.1
Status: Phase 1 - MIGRATE strategy
"""

from .context_engine import (
    EmotionalContext,
    CulturalContext,
    EmotionalContextEngine,
    EmotionalResult,
)

__all__ = [
    "EmotionalContext",
    "CulturalContext",
    "EmotionalContextEngine",
    "EmotionalResult",
]
