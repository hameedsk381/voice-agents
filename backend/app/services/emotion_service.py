"""
Multi-signal emotional state tracking for voice agents.
Combines sentiment text analysis, silence duration, interrupt frequency,
turn cadence, and response length into a unified EmotionalState.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple


@dataclass
class EmotionalState:
    """Aggregated emotional state from all signals."""
    sentiment_score: float = 0.5       # 0.0 (negative) to 1.0 (positive)
    frustration_level: float = 0.0      # 0.0 to 1.0
    hesitation_level: float = 0.0       # 0.0 to 1.0
    urgency_level: float = 0.0          # 0.0 to 1.0
    engagement_level: float = 0.5       # 0.0 (disengaged) to 1.0 (highly engaged)

    # Adaptation hints for the agent
    suggested_pace: str = "normal"      # slow, normal, fast
    suggested_tone: str = "professional"  # empathetic, calm, professional, energetic

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sentiment": round(self.sentiment_score, 2),
            "frustration": round(self.frustration_level, 2),
            "hesitation": round(self.hesitation_level, 2),
            "urgency": round(self.urgency_level, 2),
            "engagement": round(self.engagement_level, 2),
            "pace": self.suggested_pace,
            "tone": self.suggested_tone,
        }


# Negation-aware keyword lists (mirrors agent_orchestrator.analyze_sentiment)
POSITIVE_WORDS = {"thank", "good", "great", "excellent", "happy", "yes", "correct",
                  "perfect", "love", "awesome", "wonderful", "satisfied", "fine"}
NEGATIVE_WORDS = {"bad", "angry", "frustrated", "wrong", "no", "stop", "terrible",
                  "worst", "unhappy", "broke", "fail", "hate", "dissatisfied", "error"}
NEGATIONS = {"not", "no", "never", "none", "without", "n't"}
FRUSTRATION_MARKERS = {"ugh", "seriously", "again", "still", "how many times",
                       "frustrated", "annoying", "useless", "waste", "fix this now"}
HESITATION_MARKERS = {"um", "uh", "er", "hmm", "i guess", "maybe", "i think so",
                      "not sure", "well", "let me see", "i don't know"}


def _analyze_sentiment(text: str) -> float:
    """Negation-aware sentiment scoring. 0.0 = negative, 1.0 = positive."""
    text_lower = text.lower().strip()
    if not text_lower:
        return 0.5
    words = [w.strip(".,?!;:") for w in text_lower.split()]
    words = [w for w in words if w]
    pos_score = 0
    neg_score = 0
    for i, word in enumerate(words):
        is_pos = word in POSITIVE_WORDS
        is_neg = word in NEGATIVE_WORDS
        if is_pos or is_neg:
            is_negated = any(
                words[j] in NEGATIONS or words[j].endswith("n't")
                for j in range(max(0, i - 2), i)
            )
            if is_pos:
                if is_negated:
                    neg_score += 1.2
                else:
                    pos_score += 1.0
            elif is_neg:
                if is_negated:
                    pos_score += 1.0
                else:
                    neg_score += 1.2
    if pos_score > neg_score:
        return min(1.0, 0.5 + (pos_score - neg_score) * 0.25)
    elif neg_score > pos_score:
        return max(0.0, 0.5 - (neg_score - pos_score) * 0.25)
    return 0.5


def _count_markers(text: str, markers: set) -> int:
    text_lower = text.lower()
    return sum(1 for m in markers if m in text_lower)


def _detect_phrases(text: str, phrases: set) -> int:
    text_lower = text.lower()
    return sum(1 for p in phrases if p in text_lower)


class EmotionTracker:
    """
    Tracks emotional state across turns using multiple signals.
    """

    def __init__(self, window_size: int = 5):
        self.window_size = window_size
        self.turn_history: List[Dict[str, Any]] = []
        self.silence_samples: List[float] = []
        self.turn_timestamps: List[float] = []

    def analyze_turn(
        self,
        text: str,
        silence_duration: float = 0.0,
        interrupt_frequency: float = 0.0,
        turn_cadence: float = 1.0,
    ) -> EmotionalState:
        """
        Analyze a single turn and produce an EmotionalState.
        """
        sentiment = _analyze_sentiment(text)
        
        frustration_markers = _count_markers(text, FRUSTRATION_MARKERS)
        hesitation_markers = _detect_phrases(text, HESITATION_MARKERS)

        self.silence_samples.append(silence_duration)
        if len(self.silence_samples) > self.window_size:
            self.silence_samples.pop(0)

        avg_silence = (
            sum(self.silence_samples) / len(self.silence_samples)
            if self.silence_samples
            else 0.0
        )
        silence_factor = min(1.0, avg_silence / 5.0)
        frustration_factor = min(1.0, frustration_markers * 0.25 + interrupt_frequency)
        hesitation_factor = min(1.0, hesitation_markers * 0.2 + silence_factor * 0.3)

        self.turn_history.append({
            "sentiment": sentiment,
            "frustration": frustration_factor,
            "hesitation": hesitation_factor,
            "silence": avg_silence,
        })
        if len(self.turn_history) > self.window_size:
            self.turn_history.pop(0)

        # Compute trend across window
        recent = self.turn_history
        if len(recent) >= 2:
            sentiment_trend = recent[-1]["sentiment"] - recent[0]["sentiment"]
        else:
            sentiment_trend = 0.0

        # Build state
        state = EmotionalState(
            sentiment_score=sentiment,
            frustration_level=frustration_factor,
            hesitation_level=hesitation_factor,
            urgency_level=min(1.0, interrupt_frequency + frustration_factor * 0.5),
            engagement_level=0.5 + 0.5 * (1.0 - silence_factor) if sentiment > 0.3 else 0.3,
        )

        state.suggested_pace, state.suggested_tone = self._should_adapt()

        return state

    def _should_adapt(self) -> Tuple[str, str]:
        """
        Determine pace and tone adjustments based on multi-turn history.
        """
        if len(self.turn_history) < 1:
            return "normal", "professional"

        recent = self.turn_history
        avg_frustration = sum(t["frustration"] for t in recent) / len(recent)
        avg_hesitation = sum(t["hesitation"] for t in recent) / len(recent)
        avg_sentiment = sum(t["sentiment"] for t in recent) / len(recent)

        # Frustration/anger → calmer, shorter
        if avg_frustration > 0.5:
            return "slow", "calm, empathetic"

        # Confusion/hesitation → slower, supportive
        if avg_hesitation > 0.4:
            return "slow", "supportive, patient"

        # Very negative sentiment → soft, empathetic
        if avg_sentiment < 0.3:
            return "slow", "empathetic, soft"

        # Positive/engaged → normal, energetic
        if avg_sentiment > 0.7:
            return "normal", "warm, energetic"

        return "normal", "professional, clear"

    def get_adaptation_hint(self) -> Dict[str, str]:
        """Return adaptation hints for TTS and response generation."""
        pace, tone = self._should_adapt()
        return {
            "pace": pace,
            "tone": tone,
            "instruct": tone,
        }
