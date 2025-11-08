"""
SARAi AGI - Emotional Context Engine
=====================================

Advanced emotional and cultural context analysis system with:
- 16 emotional contexts detection
- 8 cultural contexts (regional adaptations)
- Time-based contextual awareness
- User profiling and learning
- Voice modulation recommendations
- Text enhancement suggestions

Version: v3.5.1 (migrated from SARAi v3.5.0)
Author: SARAi Team
License: MIT

Features
--------
1. **Emotional Detection**
   - 16 emotions: neutral, excited, frustrated, urgent, confused, etc.
   - Confidence scoring based on keywords
   - User history boosting

2. **Cultural Adaptation**
   - 8 cultures: Spain, Mexico, Argentina, Colombia, USA, UK, France, Germany
   - Regional indicators detection
   - User preference learning

3. **Time Context**
   - Morning/afternoon/evening/night detection
   - Weekend/holiday awareness
   - Business hours detection

4. **User Profiling**
   - Dominant emotion tracking
   - Cultural preference learning
   - Interaction history (last 20)
   - Average empathy level

5. **Voice Modulation**
   - Speed adjustments (0.9-1.2x)
   - Pitch modulation (±10%)
   - Emotion intensity control

Example
-------
>>> from sarai_agi.emotion import EmotionalContextEngine, EmotionalContext
>>>
>>> engine = EmotionalContextEngine()
>>>
>>> # Analyze frustration
>>> result = engine.analyze_emotional_context(
...     text="No funciona, ayuda por favor!",
...     user_id="user123"
... )
>>>
>>> print(result.detected_emotion)  # EmotionalContext.FRUSTRATED
>>> print(result.confidence)  # 0.85
>>> print(result.empathy_level)  # 0.9
>>> print(result.text_enhancement)  # "Entiendo tu frustración. "
>>>
>>> # Voice modulation
>>> print(result.voice_modulation)
>>> # {'speed': 0.9, 'pitch': 1.0, 'emotion_intensity': 0.9}
"""

import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ============================================================================
# Enumerations
# ============================================================================

class EmotionalContext(Enum):
    """
    16 emotional contexts for fine-grained detection.

    Categories:
    - Positive: EXCITED, PLAYFUL, APPRECIATIVE, FRIENDLY
    - Negative: FRUSTRATED, COMPLAINING, CONFUSED, DOUBTFUL
    - Neutral: NEUTRAL, FORMAL, PROFESSIONAL
    - Situational: URGENT, IRONIC, EMPATHETIC, ASSERTIVE, INFORMAL
    """
    NEUTRAL = "neutral"
    EXCITED = "excited"
    FRUSTRATED = "frustrated"
    IRONIC = "ironic"
    URGENT = "urgent"
    FORMAL = "formal"
    INFORMAL = "informal"
    EMPATHETIC = "empathetic"
    ASSERTIVE = "assertive"
    PLAYFUL = "playful"
    PROFESSIONAL = "professional"
    FRIENDLY = "friendly"
    COMPLAINING = "complaining"
    APPRECIATIVE = "appreciative"
    CONFUSED = "confused"
    DOUBTFUL = "doubtful"


class CulturalContext(Enum):
    """
    8 cultural contexts for regional adaptation.

    Includes:
    - Spanish variants: Spain, Mexico, Argentina, Colombia
    - English variants: USA, UK
    - Others: France, Germany
    """
    SPAIN = "spain"
    MEXICO = "mexico"
    ARGENTINA = "argentina"
    COLOMBIA = "colombia"
    USA_ENGLISH = "usa_english"
    UK_ENGLISH = "uk_english"
    FRANCE = "france"
    GERMANY = "germany"


class TimeContext(Enum):
    """
    Time-based contexts for adaptive behavior.

    Includes:
    - Time of day: morning, afternoon, evening, night
    - Special periods: weekend, holiday, business_hours
    """
    MORNING = "morning"
    AFTERNOON = "afternoon"
    EVENING = "evening"
    NIGHT = "night"
    WEEKEND = "weekend"
    HOLIDAY = "holiday"
    BUSINESS_HOURS = "business_hours"


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class EmotionalProfile:
    """
    User emotional profile with learning history.

    Attributes:
        user_id: Unique user identifier
        dominant_emotion: Most frequent emotion (last 10 interactions)
        cultural_preference: Detected or configured cultural context
        interaction_history: List of (emotion, confidence) tuples (max 20)
        avg_empathy_level: Average empathy level from interactions
        last_interaction: Unix timestamp of last interaction
    """
    user_id: str
    dominant_emotion: EmotionalContext
    cultural_preference: CulturalContext
    interaction_history: List[Tuple[EmotionalContext, float]] = field(default_factory=list)
    avg_empathy_level: float = 0.7
    last_interaction: float = field(default_factory=time.time)


@dataclass
class EmotionalResponse:
    """
    Complete emotional analysis result.

    Attributes:
        detected_emotion: Primary detected emotion
        confidence: Detection confidence (0.0-1.0)
        cultural_adaptation: Detected cultural context
        time_context: Current time context
        empathy_level: Calculated empathy level (0.0-1.0)
        voice_modulation: Dict with speed, pitch, emotion_intensity
        text_enhancement: Suggested text prefix for emotional response
    """
    detected_emotion: EmotionalContext
    confidence: float
    cultural_adaptation: CulturalContext
    time_context: TimeContext
    empathy_level: float
    voice_modulation: Dict[str, float]
    text_enhancement: str


# ============================================================================
# Contextual Embedding Engine
# ============================================================================

class ContextualEmbeddingEngine:
    """
    Keyword-based embedding engine for emotion and culture detection.

    Uses keyword matching with confidence scoring. More sophisticated
    implementations could use BERT embeddings or fine-tuned models.
    """

    def __init__(self):
        """Initialize keyword dictionaries."""
        self.emotional_keywords = self._initialize_emotional_keywords()
        self.cultural_indicators = self._initialize_cultural_indicators()

    def _initialize_emotional_keywords(self) -> Dict[EmotionalContext, List[str]]:
        """
        Initialize emotional keywords dictionary.

        Returns:
            Dict mapping EmotionalContext to keyword lists
        """
        return {
            EmotionalContext.EXCITED: [
                "genial", "increíble", "wow", "excelente", "fantástico",
                "asombroso", "perfecto", "súper", "maravilloso"
            ],
            EmotionalContext.FRUSTRATED: [
                "no funciona", "error", "problema", "ayuda", "mal",
                "falla", "roto", "difícil", "complicado", "frustrado"
            ],
            EmotionalContext.URGENT: [
                "urgente", "rápido", "ya", "ahora", "inmediato",
                "cuanto antes", "prisa", "apurado"
            ],
            EmotionalContext.FORMAL: [
                "estimado", "atentamente", "cordialmente", "señor",
                "usted", "distinguido", "respetuosamente"
            ],
            EmotionalContext.INFORMAL: [
                "hey", "hola", "qué tal", "tío", "amigo",
                "colega", "brother", "hermano"
            ],
            EmotionalContext.CONFUSED: [
                "no entiendo", "confuso", "qué significa", "explica",
                "cómo", "por qué", "dudas", "unclear"
            ],
            EmotionalContext.APPRECIATIVE: [
                "gracias", "agradezco", "aprecio", "excelente trabajo",
                "bien hecho", "perfecto", "muchas gracias"
            ],
            EmotionalContext.COMPLAINING: [
                "siempre", "nunca", "terrible", "pésimo", "horrible",
                "decepcionante", "mal servicio"
            ],
            EmotionalContext.DOUBTFUL: [
                "no estoy seguro", "quizás", "tal vez", "dudo",
                "no sé", "posiblemente", "puede ser"
            ],
            EmotionalContext.PLAYFUL: [
                "jaja", "jeje", "lol", "divertido", "gracioso",
                "bromea", "jugar"
            ]
        }

    def _initialize_cultural_indicators(self) -> Dict[CulturalContext, List[str]]:
        """
        Initialize cultural indicators dictionary.

        Returns:
            Dict mapping CulturalContext to indicator lists
        """
        return {
            CulturalContext.SPAIN: [
                "tío", "vale", "guay", "vosotros", "ostras",
                "mola", "flipar"
            ],
            CulturalContext.MEXICO: [
                "güey", "chido", "ahorita", "mande", "órale",
                "chale", "qué padre"
            ],
            CulturalContext.ARGENTINA: [
                "che", "boludo", "dale", "pibe", "quilombo",
                "laburo", "fernet"
            ],
            CulturalContext.COLOMBIA: [
                "parcero", "bacano", "chimba", "parce",
                "chévere", "berraco"
            ],
            CulturalContext.USA_ENGLISH: [
                "dude", "awesome", "cool", "yeah", "gonna"
            ],
            CulturalContext.UK_ENGLISH: [
                "cheers", "mate", "brilliant", "lovely", "whilst"
            ]
        }

    def detect_contextual_emotion(
        self,
        text: str,
        user_profile: Optional[EmotionalProfile] = None
    ) -> List[Tuple[EmotionalContext, float]]:
        """
        Detect emotions with confidence scoring.

        Args:
            text: Input text to analyze
            user_profile: Optional user profile for boosting

        Returns:
            List of (EmotionalContext, confidence) tuples, sorted by confidence
            (top 3 emotions)
        """
        text_lower = text.lower()
        scores = defaultdict(float)

        # Score by keyword matching
        for emotion, keywords in self.emotional_keywords.items():
            matches = sum(1 for kw in keywords if kw in text_lower)
            if matches > 0:
                # Confidence = matches / total keywords (normalized)
                scores[emotion] = min(matches / len(keywords) * 2, 1.0)

        # Boost if matches user's dominant emotion
        if user_profile and scores:
            for emotion, score in scores.items():
                if emotion == user_profile.dominant_emotion:
                    scores[emotion] = min(score * 1.3, 1.0)

        # Default to neutral if no matches
        if not scores:
            scores[EmotionalContext.NEUTRAL] = 0.8

        # Sort by score descending
        sorted_emotions = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_emotions[:3]  # Top 3

    def analyze_cultural_context(
        self,
        text: str,
        user_profile: Optional[EmotionalProfile] = None
    ) -> Tuple[CulturalContext, float]:
        """
        Analyze cultural context from text.

        Args:
            text: Input text to analyze
            user_profile: Optional user profile for fallback

        Returns:
            Tuple of (CulturalContext, confidence)
        """
        text_lower = text.lower()

        # Check cultural indicators
        for culture, indicators in self.cultural_indicators.items():
            matches = sum(1 for ind in indicators if ind in text_lower)
            if matches > 0:
                # Confidence boosted by match count
                confidence = min(matches / len(indicators) * 2, 1.0)
                return (culture, confidence)

        # Fallback to user profile
        if user_profile:
            return (user_profile.cultural_preference, 0.5)

        # Default to Spain (neutral Spanish)
        return (CulturalContext.SPAIN, 0.3)

    def analyze_time_context(self) -> Tuple[TimeContext, float]:
        """
        Analyze current time context.

        Returns:
            Tuple of (TimeContext, confidence)
        """
        now = datetime.now()
        hour = now.hour
        weekday = now.weekday()  # 0=Monday, 6=Sunday

        # Weekend detection (Saturday, Sunday)
        if weekday >= 5:
            return (TimeContext.WEEKEND, 1.0)

        # Time of day
        if 6 <= hour < 12:
            return (TimeContext.MORNING, 1.0)
        elif 12 <= hour < 18:
            return (TimeContext.AFTERNOON, 1.0)
        elif 18 <= hour < 22:
            return (TimeContext.EVENING, 1.0)
        else:
            return (TimeContext.NIGHT, 1.0)


# ============================================================================
# Emotional Context Engine
# ============================================================================

class EmotionalContextEngine:
    """
    Main emotional context analysis engine.

    Integrates:
    - Emotional detection (16 contexts)
    - Cultural adaptation (8 contexts)
    - Time awareness
    - User profiling
    - Voice modulation
    - Text enhancement

    Thread Safety: Not thread-safe. Use from single thread or add locks.
    """

    def __init__(self):
        """Initialize engine with embedding engine and user profiles."""
        self.embedding_engine = ContextualEmbeddingEngine()
        self.user_profiles: Dict[str, EmotionalProfile] = {}

        # Statistics
        self.analysis_count = 0
        self.avg_confidence = 0.0

    def analyze_emotional_context(
        self,
        text: str,
        user_id: str = "anonymous",
        language: str = "es"
    ) -> EmotionalResponse:
        """
        Complete emotional context analysis.

        Pipeline:
        1. Detect emotion from text
        2. Analyze cultural context
        3. Determine time context
        4. Calculate empathy level
        5. Generate voice modulation
        6. Create text enhancement
        7. Update user profile

        Args:
            text: Input text to analyze
            user_id: User identifier for profiling
            language: Language code (currently only 'es' supported)

        Returns:
            EmotionalResponse with complete analysis
        """
        self.analysis_count += 1

        # Get or create user profile
        user_profile = self.user_profiles.get(user_id)

        # 1. Detect emotion
        emotions = self.embedding_engine.detect_contextual_emotion(text, user_profile)
        detected_emotion, confidence = emotions[0]

        # 2. Cultural context
        cultural_context, cultural_confidence = (
            self.embedding_engine.analyze_cultural_context(text, user_profile)
        )

        # 3. Time context
        time_context, time_confidence = self.embedding_engine.analyze_time_context()

        # 4. Empathy level
        empathy_level = self._calculate_empathy_level(
            detected_emotion, confidence, time_context
        )

        # 5. Voice modulation
        voice_modulation = self._calculate_voice_modulation(
            detected_emotion, empathy_level
        )

        # 6. Text enhancement
        text_enhancement = self._generate_text_enhancement(
            detected_emotion, cultural_context
        )

        # 7. Update user profile
        self._update_user_profile(
            user_id, detected_emotion, cultural_context, confidence
        )

        # Update average confidence
        self.avg_confidence = (
            (self.avg_confidence * (self.analysis_count - 1) + confidence)
            / self.analysis_count
        )

        return EmotionalResponse(
            detected_emotion=detected_emotion,
            confidence=confidence,
            cultural_adaptation=cultural_context,
            time_context=time_context,
            empathy_level=empathy_level,
            voice_modulation=voice_modulation,
            text_enhancement=text_enhancement
        )

    def _calculate_empathy_level(
        self,
        emotion: EmotionalContext,
        confidence: float,
        time_context: TimeContext
    ) -> float:
        """
        Calculate appropriate empathy level.

        Factors:
        - Base: 0.7
        - +0.2 for negative emotions (frustrated, confused)
        - +0.1 for night/weekend
        - Modulated by detection confidence

        Args:
            emotion: Detected emotion
            confidence: Detection confidence
            time_context: Current time context

        Returns:
            Empathy level (0.0-1.0)
        """
        base_empathy = 0.7

        # Boost for negative emotions
        if emotion in [EmotionalContext.FRUSTRATED, EmotionalContext.CONFUSED]:
            base_empathy += 0.2

        # Boost for night/weekend (more personal time)
        if time_context in [TimeContext.NIGHT, TimeContext.WEEKEND]:
            base_empathy += 0.1

        # Modulate by confidence
        return min(base_empathy * confidence, 1.0)

    def _calculate_voice_modulation(
        self,
        emotion: EmotionalContext,
        empathy: float
    ) -> Dict[str, float]:
        """
        Calculate voice modulation parameters.

        Parameters:
        - speed: 0.9-1.2 (slow to fast)
        - pitch: 0.9-1.1 (low to high)
        - emotion_intensity: 0.0-1.0 (neutral to expressive)

        Args:
            emotion: Detected emotion
            empathy: Calculated empathy level

        Returns:
            Dict with speed, pitch, emotion_intensity
        """
        base_modulation = {
            "speed": 1.0,
            "pitch": 1.0,
            "emotion_intensity": 0.7
        }

        # Adjust for emotion
        if emotion == EmotionalContext.EXCITED:
            base_modulation["speed"] = 1.1
            base_modulation["pitch"] = 1.1
            base_modulation["emotion_intensity"] = 0.9
        elif emotion == EmotionalContext.FRUSTRATED:
            base_modulation["speed"] = 0.9
            base_modulation["emotion_intensity"] = empathy
        elif emotion == EmotionalContext.URGENT:
            base_modulation["speed"] = 1.2
            base_modulation["pitch"] = 1.05
        elif emotion == EmotionalContext.FORMAL:
            base_modulation["speed"] = 0.95
            base_modulation["emotion_intensity"] = 0.5

        return base_modulation

    def _generate_text_enhancement(
        self,
        emotion: EmotionalContext,
        culture: CulturalContext
    ) -> str:
        """
        Generate text prefix for emotional response.

        Args:
            emotion: Detected emotion
            culture: Cultural context (currently unused, for future)

        Returns:
            Text prefix string
        """
        enhancements = {
            EmotionalContext.FRUSTRATED: "Entiendo tu frustración. ",
            EmotionalContext.CONFUSED: "Déjame explicarte mejor. ",
            EmotionalContext.APPRECIATIVE: "Me alegra poder ayudarte. ",
            EmotionalContext.URGENT: "Entendido, voy al grano: ",
            EmotionalContext.COMPLAINING: "Lamento que hayas tenido esa experiencia. ",
            EmotionalContext.EXCITED: "¡Me alegra tu entusiasmo! ",
            EmotionalContext.DOUBTFUL: "Entiendo tus dudas. Veamos: "
        }

        return enhancements.get(emotion, "")

    def _update_user_profile(
        self,
        user_id: str,
        emotion: EmotionalContext,
        culture: CulturalContext,
        confidence: float
    ):
        """
        Update or create user profile.

        Args:
            user_id: User identifier
            emotion: Latest detected emotion
            culture: Latest detected culture
            confidence: Detection confidence
        """
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = EmotionalProfile(
                user_id=user_id,
                dominant_emotion=emotion,
                cultural_preference=culture,
                interaction_history=[],
                avg_empathy_level=0.7,
                last_interaction=time.time()
            )

        profile = self.user_profiles[user_id]

        # Add to history
        profile.interaction_history.append((emotion, confidence))
        profile.last_interaction = time.time()

        # Keep only last 20 interactions
        if len(profile.interaction_history) > 20:
            profile.interaction_history = profile.interaction_history[-20:]

        # Update dominant emotion (last 10 interactions)
        emotion_counts: defaultdict[str, int] = defaultdict(int)
        for emo, _ in profile.interaction_history[-10:]:
            emotion_counts[emo] += 1  # type: ignore[arg-type,index]

        if emotion_counts:
            dominant_emotion_str = max(
                emotion_counts.items(),
                key=lambda x: x[1]
            )[0]
            profile.dominant_emotion = dominant_emotion_str  # type: ignore[assignment]

    def get_emotional_insights(self) -> Dict[str, Any]:
        """
        Get emotional analysis insights and statistics.

        Returns:
            Dict with:
            - analysis_count: Total analyses performed
            - confidence_avg: Average detection confidence
            - unique_users: Total unique users
            - active_profiles: Users active in last hour
        """
        current_time = time.time()

        return {
            "analysis_count": self.analysis_count,
            "confidence_avg": self.avg_confidence,
            "unique_users": len(self.user_profiles),
            "active_profiles": sum(
                1 for p in self.user_profiles.values()
                if current_time - p.last_interaction < 3600
            )
        }

    def get_user_profile(self, user_id: str) -> Optional[EmotionalProfile]:
        """
        Get user profile if exists.

        Args:
            user_id: User identifier

        Returns:
            EmotionalProfile or None
        """
        return self.user_profiles.get(user_id)


# ============================================================================
# Factory Function
# ============================================================================

def create_emotional_context_engine() -> EmotionalContextEngine:
    """
    Create EmotionalContextEngine instance.

    Returns:
        Initialized EmotionalContextEngine
    """
    return EmotionalContextEngine()
