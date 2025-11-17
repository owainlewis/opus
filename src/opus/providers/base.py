"""Base LLM provider interface"""

import inspect
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    """
    Abstract base class for LLM providers.

    Defines the interface that all LLM providers must implement.
    Handles tool/function calling in a provider-agnostic way.

    IMPORTANT: All providers MUST use async clients to avoid blocking the event loop.
    Using synchronous API clients will block async operations like status spinners.

    Example:
        ✓ CORRECT:   from anthropic import AsyncAnthropic
        ✓ CORRECT:   from openai import AsyncOpenAI
        ✗ INCORRECT: from anthropic import Anthropic (blocks event loop)
        ✗ INCORRECT: from openai import OpenAI (blocks event loop)
    """

    def __init__(self, model: str, tools: List[Dict], system_prompt: str):
        """
        Initialize the provider.

        Args:
            model: Model identifier
            tools: List of tool definitions in universal format
            system_prompt: System prompt for the agent
        """
        self.model = model
        self.tools = tools
        self.system_prompt = system_prompt
        self._setup()
        self._validate_async_client()

    @abstractmethod
    def _setup(self):
        """
        Provider-specific setup.

        Called after __init__ to initialize clients and convert tools
        to provider-specific format.

        CRITICAL: You MUST initialize an ASYNC client here, not a sync client.
        Using a synchronous client will block the event loop and break UI elements
        like progress spinners.

        Example:
            ✓ self.client = AsyncAnthropic(api_key=key)  # Correct
            ✗ self.client = Anthropic(api_key=key)       # Wrong - blocks event loop!
        """
        pass

    def _validate_async_client(self):
        """
        Validate that the provider is using async patterns.

        Checks if the client has async methods and warns if sync methods are detected.
        This helps catch the common mistake of using sync clients in async code.
        """
        if not hasattr(self, 'client'):
            return  # Some providers might not use a client attribute

        client = self.client
        client_class_name = client.__class__.__name__

        # Check for common sync client patterns
        sync_patterns = ['Anthropic', 'OpenAI', 'Client']
        async_patterns = ['Async', 'async']

        # Warn if the class name looks like a sync client
        if any(pattern in client_class_name for pattern in sync_patterns):
            if not any(pattern in client_class_name for pattern in async_patterns):
                logger.warning(
                    f"⚠️  Provider {self.__class__.__name__} may be using a synchronous client "
                    f"({client_class_name}). This can block the event loop and break UI elements "
                    f"like progress spinners. Consider using an async client instead "
                    f"(e.g., AsyncAnthropic, AsyncOpenAI)."
                )

    @abstractmethod
    async def call(self, messages: List[Dict]) -> Dict:
        """
        Call the LLM with conversation messages.

        Args:
            messages: Conversation history in universal format

        Returns:
            Normalized response dict with:
                - message: Text response from model
                - tool_calls: List of tool calls (if any)
                - done: Boolean indicating if conversation is complete
                - raw_message: Original provider response

        CRITICAL: When calling your API client, you MUST use 'await' to avoid
        blocking the event loop:
            ✓ response = await self.client.messages.create(...)  # Correct
            ✗ response = self.client.messages.create(...)        # Wrong - blocks!
        """
        pass

    @abstractmethod
    def format_assistant_message(self, response: Dict) -> Dict:
        """
        Format assistant response for message history.

        Args:
            response: The response dict from call() method

        Returns:
            Provider-specific message format for history
        """
        pass

    @staticmethod
    def _format_result_for_llm(result: Any) -> str:
        """
        Normalize any result type to string for LLM consumption.

        Args:
            result: Tool execution result (dict, list, str, etc.)

        Returns:
            String representation suitable for LLM
        """
        if isinstance(result, dict):
            return json.dumps(result, indent=2)
        elif isinstance(result, list):
            return json.dumps(result, indent=2)
        else:
            return str(result)

    @abstractmethod
    def format_tool_result(self, tool_call_id: str, tool_name: str, result: Any) -> Dict:
        """
        Format tool execution result for the provider.

        Args:
            tool_call_id: ID of the tool call
            tool_name: Name of the tool
            result: Tool execution result

        Returns:
            Provider-specific tool result message
        """
        pass
