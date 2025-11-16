"""Error recovery and retry mechanism for tool execution"""

import logging
from typing import Dict

# Import ToolError from models for Pydantic validation
from opus.models import ToolError

logger = logging.getLogger(__name__)


class ToolExecutionTracker:
    """
    Tracks tool execution attempts and manages retry logic.

    Maintains per-tool attempt counters and provides retry decisions.
    """

    def __init__(self, max_attempts: int = 2):
        """
        Initialize tracker.

        Args:
            max_attempts: Maximum number of attempts per tool per conversation turn
        """
        self.max_attempts = max_attempts
        self.attempt_counts: Dict[str, int] = {}

    def record_attempt(self, tool_name: str) -> int:
        """
        Record a tool execution attempt.

        Args:
            tool_name: Name of the tool

        Returns:
            Current attempt number (1-indexed)
        """
        if tool_name not in self.attempt_counts:
            self.attempt_counts[tool_name] = 0

        self.attempt_counts[tool_name] += 1

        return self.attempt_counts[tool_name]

    def record_success(self, tool_name: str):
        """
        Record a successful tool execution.

        Resets the attempt counter for the tool.

        Args:
            tool_name: Name of the tool
        """
        if tool_name in self.attempt_counts:
            self.attempt_counts[tool_name] = 0

    def can_retry(self, tool_name: str) -> bool:
        """
        Check if a tool can be retried.

        Args:
            tool_name: Name of the tool

        Returns:
            True if tool can be retried, False otherwise
        """
        attempts = self.attempt_counts.get(tool_name, 0)
        return attempts < self.max_attempts

    def reset(self):
        """Reset all attempt counters (call at start of new conversation turn)"""
        self.attempt_counts.clear()
