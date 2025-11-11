"""Anthropic Claude provider implementation"""

import logging
import os
from typing import Dict, List, Any
from anthropic import AsyncAnthropic

from opus.providers.base import LLMProvider

logger = logging.getLogger(__name__)


class AnthropicProvider(LLMProvider):
    """
    Anthropic Claude provider with tool calling support.

    Uses the native Anthropic tool format (similar to universal format).
    """

    def _setup(self):
        """Initialize Anthropic client"""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is required")

        self.client = AsyncAnthropic(api_key=api_key)

        # Anthropic uses similar format to our universal format, minimal conversion needed
        self.anthropic_tools = self.tools

    async def call(self, messages: List[Dict]) -> Dict:
        """
        Call Anthropic API with conversation messages.

        Args:
            messages: Conversation history

        Returns:
            Normalized response with message, tool_calls, and done flag
        """
        # Filter out system messages (handled separately in Anthropic)
        anthropic_messages = [msg for msg in messages if msg.get("role") != "system"]

        # Call Anthropic API
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=self.system_prompt,
            messages=anthropic_messages,
            tools=self.anthropic_tools if self.anthropic_tools else None,
        )

        # Extract text content
        text_content = ""
        tool_calls = []

        for block in response.content:
            if block.type == "text":
                text_content += block.text
            elif block.type == "tool_use":
                tool_calls.append({
                    "id": block.id,
                    "name": block.name,
                    "arguments": block.input,
                })

        # Check if conversation is done (no tool calls)
        done = len(tool_calls) == 0

        return {
            "message": text_content,
            "tool_calls": tool_calls,
            "done": done,
            "raw_message": response,
        }

    def format_assistant_message(self, response: Dict) -> Dict:
        """
        Format assistant response for message history.

        Args:
            response: The response dict from call() method

        Returns:
            Anthropic formatted assistant message
        """
        raw_message = response.get("raw_message")

        if not raw_message:
            return {"role": "assistant", "content": response["message"]}

        # Use Anthropic's native content format
        return {
            "role": "assistant",
            "content": raw_message.content,
        }

    def format_tool_result(self, tool_call_id: str, tool_name: str, result: Any) -> Dict:
        """
        Format tool execution result for Anthropic.

        Args:
            tool_call_id: ID of the tool call
            tool_name: Name of the tool
            result: Tool execution result

        Returns:
            Anthropic tool_result message format
        """
        # Check if result contains an error
        is_error = isinstance(result, dict) and "error" in result

        return {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": tool_call_id,
                    "content": self._format_result_for_llm(result),
                    "is_error": is_error,
                }
            ],
        }
