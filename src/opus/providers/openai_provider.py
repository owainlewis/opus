"""Native OpenAI provider implementation"""

import logging
import os
from typing import Dict, List, Any

from opus.providers.base import LLMProvider

logger = logging.getLogger(__name__)


class OpenAIProvider(LLMProvider):
    """
    Native OpenAI provider using the official OpenAI SDK.

    Supports both OpenAI APIs:
    - Chat Completions API (default): Standard API, widely compatible
    - Responses API (new): Advanced features, stateful conversations

    Features:
    - Support for any OpenAI model
    - Configurable base_url for OpenAI-compatible APIs
    - Vision/multimodal support
    - Function calling with tools
    - Stateful conversations (Responses API)

    Compatible with:
    - OpenAI: https://api.openai.com/v1
    - Kimi/Moonshot: https://api.moonshot.cn/v1 (Chat Completions)
    - DeepSeek: https://api.deepseek.com/v1 (Chat Completions)
    - Together AI: https://api.together.xyz/v1 (Chat Completions)
    - Groq: https://api.groq.com/openai/v1 (Chat Completions)
    - Any OpenAI-compatible endpoint (Chat Completions)

    Note: The Responses API is OpenAI-specific and not available on compatible endpoints.
    """

    def __init__(self, config, tools: List[Dict], system_prompt: str):
        """
        Initialize OpenAI provider.

        Args:
            config: OpusConfig instance with OpenAI settings
            tools: List of tool definitions in universal format
            system_prompt: System prompt for the agent
        """
        self.config = config
        self.api_key = config.openai_api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = getattr(config, "openai_base_url", None) or os.getenv("OPENAI_BASE_URL")
        self.api_type = getattr(config, "openai_api_type", "chat_completions")
        self.max_tokens = getattr(config, "openai_max_tokens", 4096)

        # For stateful Responses API conversations
        self.previous_response_id = None

        if not self.api_key:
            raise ValueError(
                "OpenAI API key not found. Set OPENAI_API_KEY environment "
                "variable or openai_api_key in config."
            )

        # Call parent constructor
        super().__init__(config.model, tools, system_prompt)

    def _setup(self):
        """Initialize OpenAI client and convert tools"""
        try:
            from openai import AsyncOpenAI
        except ImportError:
            raise ImportError(
                "OpenAI SDK not installed. Install with: pip install opus[openai]"
            )

        # Initialize client with optional custom base_url
        client_params = {"api_key": self.api_key}
        if self.base_url:
            client_params["base_url"] = self.base_url
            logger.info(f"Using custom OpenAI base URL: {self.base_url}")

        self.client = AsyncOpenAI(**client_params)

        # Convert tools to OpenAI function calling format
        self.openai_tools = []
        if self.tools:
            for tool in self.tools:
                self.openai_tools.append({
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool["description"],
                        "parameters": tool["parameters"],
                    }
                })

    def _convert_messages(self, messages: List[Dict]) -> List[Dict]:
        """
        Convert universal message format to OpenAI format.

        OpenAI format is already the universal format, so mostly pass-through.
        Just ensure system prompt is included.

        Args:
            messages: Messages in universal format

        Returns:
            Messages in OpenAI format
        """
        openai_messages = []

        # Add system message if not already present
        has_system = any(msg.get("role") == "system" for msg in messages)
        if not has_system and self.system_prompt:
            openai_messages.append({
                "role": "system",
                "content": self.system_prompt
            })

        # Add all messages
        for msg in messages:
            openai_messages.append(msg)

        return openai_messages

    async def _call_chat_completions(self, messages: List[Dict]) -> Dict:
        """
        Call OpenAI Chat Completions API with conversation messages.

        Args:
            messages: Conversation history in universal format

        Returns:
            Normalized response dict with:
                - message: Text response from model
                - tool_calls: List of tool calls (if any)
                - done: Boolean indicating if conversation is complete
                - raw_message: Original OpenAI response
        """
        # Convert messages to OpenAI format
        openai_messages = self._convert_messages(messages)

        # Build request parameters
        request_params = {
            "model": self.model,
            "messages": openai_messages,
            "max_tokens": self.max_tokens,
        }

        # Add tools if available
        if self.openai_tools:
            request_params["tools"] = self.openai_tools
            request_params["tool_choice"] = "auto"

        # Call OpenAI API
        try:
            response = await self.client.chat.completions.create(**request_params)
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            raise

        # Extract message and tool calls
        choice = response.choices[0]
        message_content = choice.message.content or ""

        # Extract tool calls
        tool_calls = []
        if hasattr(choice.message, "tool_calls") and choice.message.tool_calls:
            for tc in choice.message.tool_calls:
                # Parse arguments (they come as JSON string)
                import json
                try:
                    arguments = json.loads(tc.function.arguments) if isinstance(tc.function.arguments, str) else tc.function.arguments
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse tool call arguments: {tc.function.arguments}")
                    arguments = {}

                tool_calls.append({
                    "id": tc.id,
                    "name": tc.function.name,
                    "arguments": arguments
                })

        # Check if conversation is done
        done = choice.finish_reason == "stop" and not tool_calls

        return {
            "message": message_content,
            "tool_calls": tool_calls,
            "done": done,
            "raw_message": response,
        }

    async def _call_responses(self, messages: List[Dict]) -> Dict:
        """
        Call OpenAI Responses API (new advanced API).

        Args:
            messages: Conversation history in universal format

        Returns:
            Normalized response dict with:
                - message: Text response from model
                - tool_calls: List of tool calls (if any)
                - done: Boolean indicating if conversation is complete
                - raw_message: Original OpenAI response
        """
        import json

        # Build request parameters for Responses API
        request_params = {
            "model": self.model,
        }

        # Extract system prompt (instructions in Responses API)
        system_message = None
        user_messages = []
        for msg in messages:
            if msg.get("role") == "system":
                system_message = msg.get("content", "")
            else:
                user_messages.append(msg)

        # Set instructions (system prompt)
        if system_message or self.system_prompt:
            request_params["instructions"] = system_message or self.system_prompt

        # For multi-turn, use previous_response_id instead of passing all messages
        if self.previous_response_id and len(user_messages) > 0:
            # Use stateful API - only send the latest user message
            latest_message = user_messages[-1]
            if latest_message.get("role") == "user":
                request_params["input"] = latest_message.get("content", "")
            request_params["previous_response_id"] = self.previous_response_id
        else:
            # First turn or no previous response - convert messages to input
            # For now, we'll use the last user message as input
            # The Responses API doesn't directly support multi-message history like chat completions
            if user_messages:
                latest_user_msg = None
                for msg in reversed(user_messages):
                    if msg.get("role") == "user":
                        latest_user_msg = msg
                        break

                if latest_user_msg:
                    request_params["input"] = latest_user_msg.get("content", "")

        # Set max_output_tokens
        request_params["max_output_tokens"] = self.max_tokens

        # Add tools if available
        if self.openai_tools:
            # Convert to Responses API format
            tools = []
            for tool in self.openai_tools:
                tools.append({
                    "type": "function",
                    "function": tool["function"]
                })
            request_params["tools"] = tools

        # Call Responses API
        try:
            response = await self.client.responses.create(**request_params)
        except Exception as e:
            logger.error(f"OpenAI Responses API call failed: {e}")
            raise

        # Store response ID for next turn
        if hasattr(response, "id"):
            self.previous_response_id = response.id

        # Extract output items
        message_content = ""
        tool_calls = []

        if hasattr(response, "output") and response.output:
            for item in response.output:
                item_type = getattr(item, "type", None)

                # Handle message output
                if item_type == "message":
                    if hasattr(item, "content") and item.content:
                        for content_item in item.content:
                            content_type = getattr(content_item, "type", None)

                            if content_type == "output_text":
                                text = getattr(content_item, "text", "")
                                message_content += text
                            elif content_type == "refusal":
                                refusal = getattr(content_item, "refusal", "")
                                message_content += f"[Refusal: {refusal}]"

                # Handle function calls
                elif item_type == "function_call":
                    func_name = getattr(item, "name", "")
                    func_args_str = getattr(item, "arguments", "{}")
                    func_id = getattr(item, "id", f"call_{len(tool_calls)}")

                    try:
                        func_args = json.loads(func_args_str) if isinstance(func_args_str, str) else func_args_str
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse function arguments: {func_args_str}")
                        func_args = {}

                    tool_calls.append({
                        "id": func_id,
                        "name": func_name,
                        "arguments": func_args
                    })

        # Check if conversation is done
        status = getattr(response, "status", "completed")
        done = status == "completed" and not tool_calls

        return {
            "message": message_content,
            "tool_calls": tool_calls,
            "done": done,
            "raw_message": response,
        }

    async def call(self, messages: List[Dict]) -> Dict:
        """
        Call OpenAI API with conversation messages.

        Routes to the appropriate API based on config (chat_completions or responses).

        Args:
            messages: Conversation history in universal format

        Returns:
            Normalized response dict with:
                - message: Text response from model
                - tool_calls: List of tool calls (if any)
                - done: Boolean indicating if conversation is complete
                - raw_message: Original OpenAI response
        """
        if self.api_type == "responses":
            return await self._call_responses(messages)
        else:
            return await self._call_chat_completions(messages)

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

        # Add tool calls if present
        if response["tool_calls"]:
            message["tool_calls"] = response["tool_calls"]

        return message

    def format_tool_result(self, tool_call_id: str, tool_name: str, result: Any) -> Dict:
        """
        Format tool execution result for OpenAI.

        Args:
            tool_call_id: ID of the tool call
            tool_name: Name of the tool
            result: Tool execution result

        Returns:
            Tool result message in OpenAI format
        """
        # Format the result as string
        result_str = self._format_result_for_llm(result)

        # OpenAI format for tool results
        return {
            "role": "tool",
            "tool_call_id": tool_call_id,
            "name": tool_name,
            "content": result_str,
        }
