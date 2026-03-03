"""Scorer module for Zorgnieuws."""
from .claude_scorer import ClaudeScorer
from .fallback_scorer import FallbackScorer

__all__ = ["ClaudeScorer", "FallbackScorer"]
