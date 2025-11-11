"""Google Gemini provider implementation"""

import json
import logging
import os
from typing import Dict, List, Any
from google import genai
from google.genai import types

from opus.providers.base import LLMProvider

logger = logging.getLogger(__name__)


class GeminiProvider(LLMProvider):
    """
    Google Gemini provider with function calling support.

    Converts universal tool schema to Gemini's function format and
    handles response normalization.
    """

    def _setup(self):
        """Initialize Gemini client and convert tools to Gemini format"""
        # Configure API key from environment
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")

        # Initialize client with new API
        self.client = genai.Client(api_key=api_key)

        # Convert tools to Gemini function format
        self.function_declarations = []
        for tool in self.tools:
            # Build function declaration as dict
            function_declaration = {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": {
                    "type": "object",
                    "properties": tool["parameters"].get("properties", {}),
                    "required": tool["parameters"].get("required", []),
                }
            }
            self.function_declarations.append(function_declaration)

        # Create Tool and config objects if tools are present
        if self.function_declarations:
            self.tool = types.Tool(function_declarations=self.function_declarations)
        else:
            self.tool = None

    async def call(self, messages: List[Dict]) -> Dict:
        """
        Call Gemini API with conversation messages.

        Args:
            messages: Conversation history

        Returns:
            Normalized response with message, tool_calls, and done flag
        """
        # Convert messages to Gemini format
        gemini_messages = []

        for msg in messages:
            role = msg.get("role")
            content = msg.get("content")
            parts = msg.get("parts")

            # Skip system messages - already in system_instruction
            if role == "system":
                continue

            # Map roles: assistant -> model, user -> user
            gemini_role = "model" if role == "assistant" else "user"

            # If message already has parts, use them directly
            if parts:
                logger.debug(f"Using existing parts for {gemini_role} message")
                gemini_messages.append({
                    "role": gemini_role,
                    "parts": parts,
                })
                continue

            # Handle different content formats
            if isinstance(content, str):
                # Simple text message
                gemini_messages.append({
                    "role": gemini_role,
                    "parts": [{"text": content}] if content else [{"text": ""}],
                })
            elif isinstance(content, list):
                # Handle content blocks
                parts = []
                for block in content:
                    if isinstance(block, dict):
                        if block.get("type") == "text":
                            parts.append({"text": block.get("text", "")})
                        elif block.get("type") == "tool_result":
                            parts.append({
                                "function_response": {
                                    "name": "tool_result",
                                    "response": {"result": block.get("content", "")}
                                }
                            })
                        elif block.get("type") == "tool_use":
                            parts.append({
                                "function_call": {
                                    "name": block.get("name"),
                                    "args": block.get("input", {})
                                }
                            })
                if parts:
                    gemini_messages.append({"role": gemini_role, "parts": parts})
            elif role == "tool":
                # OpenAI-style tool result
                gemini_messages.append({
                    "role": "user",
                    "parts": [{
                        "function_response": {
                            "name": msg.get("name", "unknown"),
                            "response": {"result": content}
                        }
                    }]
                })

        # Handle tool_calls in assistant messages (OpenAI format)
        for i, msg in enumerate(messages):
            if msg.get("role") == "assistant" and msg.get("tool_calls"):
                if i < len(gemini_messages) and gemini_messages[i]["role"] == "model":
                    for tool_call in msg["tool_calls"]:
                        arguments = tool_call.get("arguments", {})
                        if arguments is None:
                            arguments = {}
                        gemini_messages[i]["parts"].append({
                            "function_call": {
                                "name": tool_call["name"],
                                "args": arguments
                            }
                        })

        # Create config with system instruction and tools
        config_params = {
            "system_instruction": self.system_prompt,
        }
        if self.tool:
            config_params["tools"] = [self.tool]

        config = types.GenerateContentConfig(**config_params)

        # Generate response using new API
        response = self.client.models.generate_content(
            model=self.model,
            contents=gemini_messages,
            config=config,
        )

        # Extract response
        if not response.candidates:
            return {
                "message": "No response from Gemini",
                "tool_calls": [],
                "done": True,
                "raw_message": response,
            }

        candidate = response.candidates[0]

        # Extract text and function calls
        text_content = ""
        tool_calls = []

        for part in candidate.content.parts:
            if part.text:
                text_content += part.text
            elif hasattr(part, 'function_call') and part.function_call:
                args = part.function_call.args
                arguments = dict(args) if args is not None else {}
                tool_calls.append({
                    "id": f"call_{len(tool_calls)}",
                    "name": part.function_call.name,
                    "arguments": arguments,
                })

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
            Gemini formatted assistant message
        """
        raw_message = response.get("raw_message")

        if not raw_message or not raw_message.candidates:
            return {"role": "assistant", "content": response["message"]}

        candidate = raw_message.candidates[0]

        # Build parts list
        parts = []
        for part in candidate.content.parts:
            if part.text:
                parts.append({"text": part.text})
            elif hasattr(part, 'function_call') and part.function_call:
                args = part.function_call.args
                arguments = dict(args) if args is not None else {}
                parts.append({
                    "function_call": {
                        "name": part.function_call.name,
                        "args": arguments
                    }
                })

        return {
            "role": "assistant",
            "parts": parts,
        }

    def format_tool_result(self, tool_call_id: str, tool_name: str, result: Any) -> Dict:
        """
        Format tool execution result as a function response.

        Args:
            tool_call_id: ID of the tool call (not used by Gemini)
            tool_name: Name of the tool
            result: Tool execution result

        Returns:
            Gemini function_response message format
        """
        # Pass result as structured data to Gemini
        if isinstance(result, dict):
            result_dict = result
        elif isinstance(result, list):
            result_dict = {"items": result}
        else:
            result_dict = {"result": str(result)}

        return {
            "role": "user",
            "parts": [{
                "function_response": {
                    "name": tool_name,
                    "response": result_dict,
                }
            }]
        }
