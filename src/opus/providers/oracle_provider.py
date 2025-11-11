"""Oracle GenAI provider implementation using native OCI SDK"""

import asyncio
import json
import logging
import os
from typing import Dict, List, Any

import oci
from oci.generative_ai_inference import GenerativeAiInferenceClient
from oci.generative_ai_inference.models import (
    ChatDetails,
    GenericChatRequest,
    OnDemandServingMode,
    UserMessage,
    AssistantMessage,
    ToolMessage,
    TextContent,
    FunctionDefinition,
)

from opus.providers.base import LLMProvider

logger = logging.getLogger(__name__)


class OracleProvider(LLMProvider):
    """
    Oracle GenAI provider using native OCI SDK.

    Uses the native Oracle Cloud Infrastructure SDK for GenAI service.
    Supports xAI Grok models and other models available in OCI GenAI.

    Default region: US Midwest (Chicago)
    Authentication: Uses API keys from ~/.oci/config
    """

    def _setup(self):
        """Initialize Oracle GenAI client using native SDK"""
        # Get profile name from environment or use default
        profile_name = os.getenv("OCI_PROFILE", "DEFAULT")

        # Load OCI config
        try:
            oci_config = oci.config.from_file(profile_name=profile_name)
        except Exception as e:
            raise ValueError(
                f"Failed to load OCI configuration. "
                f"Ensure ~/.oci/config is set up correctly: {e}"
            )

        # Get compartment ID from multiple sources (in priority order):
        # 1. Environment variable
        # 2. OCI config file (custom field)
        self.compartment_id = os.getenv("OCI_COMPARTMENT_ID")
        if not self.compartment_id:
            self.compartment_id = oci_config.get("compartment_id")

        if not self.compartment_id:
            raise ValueError(
                "compartment_id is required. Set it in one of these ways:\n"
                "  1. Environment variable: export OCI_COMPARTMENT_ID=ocid1.compartment...\n"
                "  2. Add 'compartment_id=ocid1.compartment...' to ~/.oci/config"
            )

        # Get service endpoint from environment or use default
        service_endpoint = os.getenv(
            "OCI_GENAI_ENDPOINT",
            "https://inference.generativeai.us-chicago-1.oci.oraclecloud.com"
        )

        # Initialize the GenAI client
        self.client = GenerativeAiInferenceClient(
            config=oci_config,
            service_endpoint=service_endpoint
        )

        # Convert tools to OCI FunctionDefinition format
        self.oci_tools = []
        if self.tools:
            for tool in self.tools:
                self.oci_tools.append(
                    FunctionDefinition(
                        name=tool["name"],
                        description=tool.get("description", ""),
                        parameters=tool.get("parameters", {})
                    )
                )

        logger.info(f"Initialized Oracle provider with model: {self.model}")

    def _convert_messages_to_oci(self, messages: List[Dict]) -> List:
        """
        Convert universal message format to OCI native format.

        Args:
            messages: Messages in universal format

        Returns:
            List of OCI message objects
        """
        oci_messages = []

        for msg in messages:
            role = msg.get("role")

            if role == "system":
                # System messages are handled separately in GenericChatRequest
                continue
            elif role == "user":
                oci_messages.append(
                    UserMessage(content=[TextContent(text=msg.get("content", ""))])
                )
            elif role == "assistant":
                # Build AssistantMessage with tool_calls at message level
                content_parts = []

                # Add text content (even if empty when there are tool calls)
                text = msg.get("content", "")
                if text or not msg.get("tool_calls"):
                    content_parts.append(TextContent(text=text))
                else:
                    # Need at least empty text content
                    content_parts.append(TextContent(text=""))

                # Extract tool calls for message-level tool_calls parameter
                tool_calls_list = None
                if "tool_calls" in msg and msg["tool_calls"]:
                    tool_calls_list = []
                    for tc in msg["tool_calls"]:
                        tool_calls_list.append({
                            "id": tc.get("id", tc["function"]["name"]),
                            "name": tc["function"]["name"],
                            "type": "FUNCTION",
                            "arguments": json.dumps(tc["function"]["arguments"]) if isinstance(tc["function"]["arguments"], dict) else tc["function"]["arguments"]
                        })

                oci_messages.append(AssistantMessage(
                    content=content_parts,
                    tool_calls=tool_calls_list
                ))
            elif role == "tool":
                # Tool result message
                oci_messages.append(
                    ToolMessage(
                        tool_call_id=msg.get("tool_call_id", ""),
                        content=[TextContent(text=msg.get("content", ""))]
                    )
                )

        return oci_messages

    async def call(self, messages: List[Dict]) -> Dict:
        """
        Call Oracle GenAI API with conversation messages.

        Args:
            messages: Conversation history

        Returns:
            Normalized response with message, tool_calls, and done flag
        """
        # Convert messages to OCI format
        oci_messages = self._convert_messages_to_oci(messages)

        # Debug: Log the converted messages
        logger.info(f"Converting {len(messages)} messages to OCI format")
        logger.info(f"Converted to {len(oci_messages)} OCI messages")
        for i, msg in enumerate(oci_messages):
            logger.info(f"OCI message {i}: type={type(msg).__name__}, content={msg}")

        # Build the chat request parameters
        chat_request_params = {
            "api_format": "GENERIC",
            "messages": oci_messages,
            "max_tokens": 4000,
        }

        # Add tools if available
        if self.oci_tools:
            chat_request_params["tools"] = self.oci_tools

        chat_request = GenericChatRequest(**chat_request_params)

        # Create the chat details
        chat_details = ChatDetails(
            compartment_id=self.compartment_id,
            serving_mode=OnDemandServingMode(model_id=self.model),
            chat_request=chat_request,
        )

        try:
            # Make the API call (OCI SDK is synchronous, so run in thread pool)
            response = await asyncio.to_thread(self.client.chat, chat_details)
            chat_response = response.data.chat_response

            # Debug: Log the raw response structure
            logger.info(f"Raw response type: {type(chat_response)}")
            logger.info(f"Raw response: {chat_response}")
        except Exception as e:
            logger.error(f"Oracle GenAI call failed: {e}")
            raise

        # Extract response content
        text_content = ""
        tool_calls = []

        # Parse the response content
        if hasattr(chat_response, 'choices') and chat_response.choices:
            choice = chat_response.choices[0]

            if hasattr(choice, 'message'):
                message = choice.message

                # Extract text content
                if hasattr(message, 'content') and message.content:
                    for content_part in message.content:
                        # Extract text - content_part should be a TextContent object
                        if hasattr(content_part, "text"):
                            text_content += content_part.text
                        elif isinstance(content_part, dict) and "text" in content_part:
                            text_content += content_part["text"]

                # Extract tool calls from message.tool_calls
                if hasattr(message, 'tool_calls') and message.tool_calls:
                    logger.info(f"Found tool_calls in message: {message.tool_calls}")
                    for tool_call in message.tool_calls:
                        logger.info(f"Processing tool call: {tool_call}")
                        tool_calls.append({
                            "id": tool_call.id,
                            "name": tool_call.name,
                            "arguments": json.loads(tool_call.arguments) if isinstance(tool_call.arguments, str) else tool_call.arguments,
                        })

        logger.info(f"Extracted {len(tool_calls)} tool_calls: {tool_calls}")

        # Check if conversation is done
        done = len(tool_calls) == 0

        return {
            "message": text_content,
            "tool_calls": tool_calls,
            "done": done,
            "raw_message": response.data,
        }

    def format_assistant_message(self, response: Dict) -> Dict:
        """
        Format assistant response for message history.

        Args:
            response: The response dict from call() method

        Returns:
            Universal message format
        """
        msg_dict = {
            "role": "assistant",
            "content": response["message"],
        }

        # Add tool calls if present
        if response.get("tool_calls"):
            msg_dict["tool_calls"] = [
                {
                    "id": tc["id"],
                    "type": "function",
                    "function": {
                        "name": tc["name"],
                        "arguments": tc["arguments"],
                    }
                }
                for tc in response["tool_calls"]
            ]

        return msg_dict

    def format_tool_result(self, tool_call_id: str, tool_name: str, result: Any) -> Dict:
        """
        Format tool execution result for Oracle GenAI.

        Args:
            tool_call_id: ID of the tool call
            tool_name: Name of the tool
            result: Tool execution result

        Returns:
            Universal tool message format
        """
        return {
            "role": "tool",
            "tool_call_id": tool_call_id,
            "name": tool_name,
            "content": self._format_result_for_llm(result),
        }
