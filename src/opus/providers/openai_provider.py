"""OpenAI provider implementation"""

import json
import logging
import os
from typing import Dict, List, Any
from openai import AsyncOpenAI

from opus.providers.base import LLMProvider

logger = logging.getLogger(__name__)


class OpenAIProvider(LLMProvider):
    """
    OpenAI provider with function calling support.

    Converts universal tool schema to OpenAI's function format and
    handles response normalization.
    """

    def _setup(self):
        """Initialize OpenAI client and convert tools to OpenAI format"""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")

        self.client = AsyncOpenAI(api_key=api_key)

        # Convert tools to OpenAI function format
        self.openai_tools = []
        for tool in self.tools:
            self.openai_tools.append({
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["parameters"],
                }
            })

    async def call(self, messages: List[Dict]) -> Dict:
        """
        Call OpenAI API with conversation messages.

        Args:
            messages: Conversation history

        Returns:
            Normalized response with message, tool_calls, and done flag
        """
        # Add system message at the beginning if not present
        openai_messages = []
        has_system = any(msg.get("role") == "system" for msg in messages)

        if not has_system:
            openai_messages.append({
                "role": "system",
                "content": self.system_prompt
            })

        openai_messages.extend(messages)

        # Call OpenAI API
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=openai_messages,
            tools=self.openai_tools if self.openai_tools else None,
        )

        message = response.choices[0].message

        # Extract text content
        text_content = message.content or ""

        # Extract tool calls
        tool_calls = []
        if message.tool_calls:
            for tool_call in message.tool_calls:
                # Parse arguments JSON
                try:
                    arguments = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse tool arguments: {tool_call.function.arguments}")
                    arguments = {}

                tool_calls.append({
                    "id": tool_call.id,
                    "name": tool_call.function.name,
                    "arguments": arguments,
                })

        # Check if conversation is done
        done = len(tool_calls) == 0

        return {
            "message": text_content,
            "tool_calls": tool_calls,
            "done": done,
            "raw_message": message,
        }

    def format_assistant_message(self, response: Dict) -> Dict:
        """
        Format assistant response for message history.

        Args:
            response: The response dict from call() method

        Returns:
            OpenAI formatted assistant message
        """
        raw_message = response.get("raw_message")

        if not raw_message:
            return {"role": "assistant", "content": response["message"]}

        # Build message in OpenAI format
        msg = {
            "role": "assistant",
            "content": raw_message.content,
        }

        # Add tool calls if present
        if raw_message.tool_calls:
            msg["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    }
                }
                for tc in raw_message.tool_calls
            ]

        return msg

    def format_tool_result(self, tool_call_id: str, tool_name: str, result: Any) -> Dict:
        """
        Format tool execution result for OpenAI.

        Args:
            tool_call_id: ID of the tool call
            tool_name: Name of the tool
            result: Tool execution result

        Returns:
            OpenAI tool message format
        """
        return {
            "role": "tool",
            "tool_call_id": tool_call_id,
            "name": tool_name,
            "content": self._format_result_for_llm(result),
        }
