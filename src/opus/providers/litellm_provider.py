"""LiteLLM unified provider implementation"""

import logging
import os
from typing import Dict, List, Any
import litellm

from opus.providers.base import LLMProvider

logger = logging.getLogger(__name__)

# Enable litellm logging for debugging if needed
# litellm.set_verbose = True


class LiteLLMProvider(LLMProvider):
    """
    Universal LLM provider using LiteLLM.

    Supports 100+ LLM providers including:
    - Anthropic Claude
    - OpenAI GPT
    - Google Gemini
    - AWS Bedrock
    - Azure OpenAI
    - Cohere
    - Oracle GenAI
    - And many more...

    Model naming follows litellm conventions:
    - anthropic/claude-3-5-sonnet-20241022
    - gpt-4o (OpenAI models can omit provider prefix)
    - gemini/gemini-1.5-pro
    - bedrock/anthropic.claude-v2
    - oci/cohere.command-r-plus (Oracle GenAI)
    """

    def _setup(self):
        """Initialize litellm - no client needed, uses global configuration"""
        # Convert universal tool format to OpenAI function calling format
        # (litellm uses OpenAI format internally for all providers)
        self.litellm_tools = []

        if self.tools:
            for tool in self.tools:
                self.litellm_tools.append({
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool["description"],
                        "parameters": tool["parameters"],
                    }
                })

        # Set default timeout
        litellm.request_timeout = 600  # 10 minutes for long-running operations

        # Disable telemetry by default
        os.environ.setdefault("LITELLM_TELEMETRY", "False")

    async def call(self, messages: List[Dict]) -> Dict:
        """
        Call LLM via litellm with conversation messages.

        Args:
            messages: Conversation history in OpenAI format

        Returns:
            Normalized response with message, tool_calls, and done flag
        """
        # Prepare messages - litellm expects OpenAI format
        litellm_messages = self._prepare_messages(messages)

        # Build request parameters
        request_params = {
            "model": self.model,
            "messages": litellm_messages,
            "max_tokens": 4096,
        }

        # Add tools if available
        if self.litellm_tools:
            request_params["tools"] = self.litellm_tools

            # Only add tool_choice for providers that support it
            # OCI (Oracle GenAI) doesn't support tool_choice parameter
            if not self.model.startswith("oci/"):
                request_params["tool_choice"] = "auto"

        # Call litellm
        try:
            response = await litellm.acompletion(**request_params)
        except Exception as e:
            logger.error(f"LiteLLM call failed: {e}")
            raise

        # Extract response
        choice = response.choices[0]
        message = choice.message

        # Extract text content
        text_content = message.content or ""

        # Extract tool calls
        tool_calls = []
        if hasattr(message, "tool_calls") and message.tool_calls:
            for tool_call in message.tool_calls:
                # Parse arguments if they're a string
                import json
                arguments = tool_call.function.arguments
                if isinstance(arguments, str):
                    try:
                        arguments = json.loads(arguments)
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse tool arguments: {arguments}")
                        arguments = {}

                tool_calls.append({
                    "id": tool_call.id,
                    "name": tool_call.function.name,
                    "arguments": arguments,
                })

        # Check if conversation is done (no tool calls)
        done = len(tool_calls) == 0

        return {
            "message": text_content,
            "tool_calls": tool_calls,
            "done": done,
            "raw_message": response,
        }

    def _prepare_messages(self, messages: List[Dict]) -> List[Dict]:
        """
        Prepare messages for litellm (OpenAI format).

        Handles system prompt injection for providers that use it.
        """
        litellm_messages = []

        # Add system message if not present
        has_system = any(msg.get("role") == "system" for msg in messages)
        if not has_system and self.system_prompt:
            litellm_messages.append({
                "role": "system",
                "content": self.system_prompt
            })

        # Add all other messages
        for msg in messages:
            # Skip system messages if we already added one
            if msg.get("role") == "system":
                continue
            litellm_messages.append(msg)

        return litellm_messages

    def format_assistant_message(self, response: Dict) -> Dict:
        """
        Format assistant response for message history.

        Args:
            response: The response dict from call() method

        Returns:
            OpenAI-formatted assistant message
        """
        raw_message = response.get("raw_message")

        if not raw_message:
            return {"role": "assistant", "content": response["message"]}

        # Extract the message object from litellm response
        choice = raw_message.choices[0]
        message = choice.message

        # Build message dict
        msg_dict = {
            "role": "assistant",
            "content": message.content,
        }

        # Add tool calls if present
        if hasattr(message, "tool_calls") and message.tool_calls:
            msg_dict["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": tc.type,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    }
                }
                for tc in message.tool_calls
            ]

        return msg_dict

    def format_tool_result(self, tool_call_id: str, tool_name: str, result: Any) -> Dict:
        """
        Format tool execution result for litellm (OpenAI format).

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
