"""Error recovery and retry mechanism for tool execution"""

import logging
from typing import Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ToolError:
    """Structured error information for tool failures"""

    tool_name: str
    error_message: str
    arguments: Dict
    recovery_hints: str

    @classmethod
    def from_exception(cls, tool_name: str, exception: Exception, arguments: Dict) -> "ToolError":
        """
        Create a ToolError from an exception.

        Args:
            tool_name: Name of the tool that failed
            exception: The exception that was raised
            arguments: Arguments that were passed to the tool

        Returns:
            ToolError instance with recovery hints
        """
        error_msg = str(exception)

        # Generate recovery hints based on error type
        hints = cls._generate_recovery_hints(tool_name, error_msg, arguments)

        return cls(
            tool_name=tool_name,
            error_message=error_msg,
            arguments=arguments,
            recovery_hints=hints,
        )

    @staticmethod
    def _generate_recovery_hints(tool_name: str, error_msg: str, arguments: Dict) -> str:
        """
        Generate recovery hints based on error patterns.

        Args:
            tool_name: Name of the tool
            error_msg: Error message
            arguments: Tool arguments

        Returns:
            Recovery hints as string
        """
        hints = []

        # Command not found
        if "Command not found" in error_msg or "command not found" in error_msg.lower():
            hints.append("- The command is not installed or not in PATH")
            hints.append("- Check if the tool needs to be installed")
            hints.append("- Try using an alternative tool or command")

        # Permission denied
        elif "Permission denied" in error_msg:
            hints.append("- The tool doesn't have permission to access the resource")
            hints.append("- Check file/directory permissions")
            hints.append("- Try with a different path or ask the user for access")

        # File not found
        elif "No such file or directory" in error_msg or "File not found" in error_msg:
            hints.append("- The specified file or directory doesn't exist")
            hints.append("- Check the path is correct")
            hints.append("- Use bash tool to list directory contents first")

        # Timeout
        elif "timed out" in error_msg.lower():
            hints.append("- The tool took too long to execute")
            hints.append("- Try breaking the task into smaller steps")
            hints.append("- Consider if the operation is genuinely long-running")

        # Invalid syntax
        elif "Invalid command syntax" in error_msg or "SyntaxError" in error_msg:
            hints.append("- The command syntax is invalid")
            hints.append("- Check the parameter format")
            hints.append("- Review the tool's parameter requirements")

        # Missing parameter
        elif "Missing required parameter" in error_msg:
            hints.append("- A required parameter is missing")
            hints.append("- Check the tool definition for required parameters")
            hints.append("- Provide all required parameters")

        # Generic hints if no specific pattern matched
        if not hints:
            hints.append("- Review the error message for clues")
            hints.append("- Check if the parameters are correct")
            hints.append("- Try a different approach or tool")

        return "\n".join(hints)

    def to_llm_message(self, attempt: int, max_attempts: int) -> str:
        """
        Format error for LLM with recovery guidance.

        Args:
            attempt: Current attempt number
            max_attempts: Maximum number of attempts allowed

        Returns:
            Formatted error message for LLM
        """
        can_retry = attempt < max_attempts

        message_parts = [
            f"Tool '{self.tool_name}' failed (attempt {attempt}/{max_attempts})",
            "",
            "Error:",
            self.error_message,
            "",
            "Arguments used:",
            str(self.arguments),
        ]

        if can_retry:
            message_parts.extend([
                "",
                "Recovery hints:",
                self.recovery_hints,
                "",
                f"You have {max_attempts - attempt} more attempt(s) to fix this.",
                "Please adjust your approach based on the error and hints above.",
            ])
        else:
            message_parts.extend([
                "",
                "Maximum retry attempts reached.",
                "Consider:",
                "- Asking the user for help",
                "- Trying a completely different approach",
                "- Breaking down the task into simpler steps",
            ])

        return "\n".join(message_parts)


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
