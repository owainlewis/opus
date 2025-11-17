"""Native Anthropic provider implementation with prompt caching support"""

import logging
import os
from typing import Dict, List, Any

from opus.providers.base import LLMProvider

logger = logging.getLogger(__name__)


class AnthropicProvider(LLMProvider):
    """
    Native Anthropic provider using the official Anthropic SDK.

    Features:
    - Prompt caching for system prompts and tools (reduce costs)
    - Extended context windows (up to 200K tokens)
    - Extended thinking mode
    - Vision/multimodal support
    - Direct access to latest Anthropic features

    Models:
    - claude-sonnet-4-5
    - claude-haiku-4-5
    """

    def __init__(self, config, tools: List[Dict], system_prompt: str):
        """
        Initialize Anthropic provider.

        Args:
            config: OpusConfig instance with Anthropic settings
            tools: List of tool definitions in universal format
            system_prompt: System prompt for the agent
        """
        self.config = config
        self.api_key = config.anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")
        self.prompt_caching_enabled = getattr(config, "anthropic_prompt_caching", True)
        self.max_tokens = getattr(config, "anthropic_max_tokens", 4096)

        if not self.api_key:
            raise ValueError(
                "Anthropic API key not found. Set ANTHROPIC_API_KEY environment "
                "variable or anthropic_api_key in config."
            )

        # Call parent constructor
        super().__init__(config.model, tools, system_prompt)

    def _setup(self):
        """Initialize Anthropic client and convert tools"""
        try:
            from anthropic import Anthropic
        except ImportError:
            raise ImportError(
                "Anthropic SDK not installed. Install with: pip install opus[anthropic]"
            )

        self.client = Anthropic(api_key=self.api_key)

        # Convert tools to Anthropic format
        self.anthropic_tools = []
        if self.tools:
            for tool in self.tools:
                self.anthropic_tools.append(
                    {
                        "name": tool["name"],
                        "description": tool["description"],
                        "input_schema": tool["parameters"],
                    }
                )

        # Prepare system prompt with caching if enabled
        self.system_blocks = self._prepare_system_prompt()

    def _prepare_system_prompt(self) -> List[Dict]:
        """
        Prepare system prompt with optional prompt caching.

        Anthropic's prompt caching allows caching of:
        - System prompts
        - Tool definitions
        - Large context documents

        Returns:
            List of system message blocks
        """
        blocks = []

        if self.system_prompt:
            # System prompt block
            system_block = {
                "type": "text",
                "text": self.system_prompt,
            }

            # Enable caching for system prompt if configured
            if self.prompt_caching_enabled:
                system_block["cache_control"] = {"type": "ephemeral"}

            blocks.append(system_block)

        # Note: Tools are cached automatically by Anthropic when using the tools parameter
        # with prompt caching enabled

        return blocks

    def _convert_messages(self, messages: List[Dict]) -> List[Dict]:
        """
        Convert universal message format to Anthropic format.

        Universal format (from agent.py):
        - {"role": "user", "content": "..."}
        - {"role": "assistant", "content": "...", "tool_calls": [...]}
        - {"role": "tool", "tool_call_id": "...", "content": "..."}

        Anthropic format:
        - {"role": "user", "content": "..."}
        - {"role": "assistant", "content": [...]}
        - Tool results go in user messages

        Args:
            messages: Messages in universal format

        Returns:
            Messages in Anthropic format
        """
        anthropic_messages = []
        pending_tool_results = []

        for msg in messages:
            role = msg.get("role")

            if role == "system":
                # System messages are handled separately in Anthropic
                continue

            elif role == "user":
                content = msg.get("content", "")

                # If we have pending tool results, combine them with user content
                if pending_tool_results:
                    # Tool results and user content must be in the SAME user message
                    content_blocks = pending_tool_results.copy()
                    if content:
                        content_blocks.append({"type": "text", "text": content})
                    anthropic_messages.append(
                        {"role": "user", "content": content_blocks}
                    )
                    pending_tool_results = []
                else:
                    # No tool results, just add the user message as plain text
                    anthropic_messages.append({"role": "user", "content": content})

            elif role == "assistant":
                # Extract content and tool calls
                content = msg.get("content", "")
                tool_calls = msg.get("tool_calls", [])

                # Build content blocks
                content_blocks = []

                if content:
                    content_blocks.append({"type": "text", "text": content})

                # Add tool use blocks
                for tool_call in tool_calls:
                    content_blocks.append(
                        {
                            "type": "tool_use",
                            "id": tool_call["id"],
                            "name": tool_call["name"],
                            "input": tool_call["arguments"],
                        }
                    )

                if content_blocks:
                    anthropic_messages.append(
                        {"role": "assistant", "content": content_blocks}
                    )

            elif role == "tool":
                # Tool results are added to pending list
                # They'll be included in the next user message
                tool_call_id = msg.get("tool_call_id")
                content = msg.get("content", "")

                pending_tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_call_id,
                        "content": content,
                    }
                )

        # If there are remaining tool results, add them as a final user message
        if pending_tool_results:
            anthropic_messages.append({"role": "user", "content": pending_tool_results})

        return anthropic_messages

    async def call(self, messages: List[Dict]) -> Dict:
        """
        Call Anthropic API with conversation messages.

        Args:
            messages: Conversation history in universal format

        Returns:
            Normalized response dict with:
                - message: Text response from model
                - tool_calls: List of tool calls (if any)
                - done: Boolean indicating if conversation is complete
                - raw_message: Original Anthropic response
        """
        # Convert messages to Anthropic format
        anthropic_messages = self._convert_messages(messages)

        # Build request parameters
        request_params = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": anthropic_messages,
        }

        # Add system blocks if present
        if self.system_blocks:
            request_params["system"] = self.system_blocks

        # Add tools if available
        if self.anthropic_tools:
            request_params["tools"] = self.anthropic_tools

        # Call Anthropic API
        try:
            response = self.client.messages.create(**request_params)
        except Exception as e:
            logger.error(f"Anthropic API call failed: {e}")
            raise

        # Extract text and tool calls
        message_text = ""
        tool_calls = []

        for block in response.content:
            if block.type == "text":
                message_text += block.text
            elif block.type == "tool_use":
                tool_calls.append(
                    {"id": block.id, "name": block.name, "arguments": block.input}
                )

        # Determine if conversation is done
        done = response.stop_reason == "end_turn" and not tool_calls

        return {
            "message": message_text,
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
            Message in universal format for history
        """
        message = {
            "role": "assistant",
            "content": response["message"],
        }

        if response["tool_calls"]:
            message["tool_calls"] = response["tool_calls"]

        return message

    def format_tool_result(
        self, tool_call_id: str, tool_name: str, result: Any
    ) -> Dict:
        """
        Format tool execution result for Anthropic.

        Args:
            tool_call_id: ID of the tool call
            tool_name: Name of the tool (not used by Anthropic, but kept for interface)
            result: Tool execution result

        Returns:
            Tool result message in universal format
        """
        # Format the result as string
        result_str = self._format_result_for_llm(result)

        # Return in universal format - will be converted in _convert_messages
        return {
            "role": "tool",
            "tool_call_id": tool_call_id,
            "content": result_str,
        }
