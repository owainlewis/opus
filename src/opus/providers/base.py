"""Base LLM provider interface"""

import json
from abc import ABC, abstractmethod
from typing import Dict, List, Any


class LLMProvider(ABC):
    """
    Abstract base class for LLM providers.

    Defines the interface that all LLM providers must implement.
    Handles tool/function calling in a provider-agnostic way.
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

    @abstractmethod
    def _setup(self):
        """
        Provider-specific setup.

        Called after __init__ to initialize clients and convert tools
        to provider-specific format.
        """
        pass

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
