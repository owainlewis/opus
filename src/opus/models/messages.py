"""Message type models for LLM conversations"""

from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field, ConfigDict


class ToolCall(BaseModel):
    """Represents a tool/function call from the assistant"""

    id: str = Field(description="Unique identifier for this tool call")
    name: str = Field(description="Name of the tool to call")
    arguments: Dict[str, Any] = Field(
        default_factory=dict,
        description="Arguments to pass to the tool"
    )

    model_config = ConfigDict(extra="forbid")


class ToolCallOpenAI(BaseModel):
    """OpenAI-formatted tool call (used in message history)"""

    id: str = Field(description="Tool call ID")
    type: Literal["function"] = Field(default="function", description="Type of tool call")
    function: "FunctionCall" = Field(description="Function call details")

    model_config = ConfigDict(extra="forbid")


class FunctionCall(BaseModel):
    """Function call details in OpenAI format"""

    name: str = Field(description="Function name")
    arguments: str = Field(description="JSON string of arguments")

    model_config = ConfigDict(extra="forbid")


class UserMessage(BaseModel):
    """Message from the user"""

    role: Literal["user"] = Field(default="user", description="Message role")
    content: str = Field(description="User's message content")

    model_config = ConfigDict(extra="allow")  # Allow extra fields for provider-specific data

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for LLM API"""
        return {"role": self.role, "content": self.content}


class SystemMessage(BaseModel):
    """System message for setting context"""

    role: Literal["system"] = Field(default="system", description="Message role")
    content: str = Field(description="System prompt content")

    model_config = ConfigDict(extra="allow")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for LLM API"""
        return {"role": self.role, "content": self.content}


class AssistantMessage(BaseModel):
    """Message from the assistant"""

    role: Literal["assistant"] = Field(default="assistant", description="Message role")
    content: Optional[str] = Field(default=None, description="Assistant's text response")
    tool_calls: Optional[List[ToolCallOpenAI]] = Field(
        default=None,
        description="Tool calls made by the assistant (OpenAI format)"
    )

    model_config = ConfigDict(extra="allow")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for LLM API"""
        result = {"role": self.role, "content": self.content}

        if self.tool_calls:
            result["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": tc.type,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    }
                }
                for tc in self.tool_calls
            ]

        return result


class ToolResultMessage(BaseModel):
    """Message containing tool execution result"""

    role: Literal["tool"] = Field(default="tool", description="Message role")
    tool_call_id: str = Field(description="ID of the tool call this is responding to")
    name: str = Field(description="Name of the tool that was executed")
    content: str = Field(description="Tool execution result (as string)")

    model_config = ConfigDict(extra="allow")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for LLM API"""
        return {
            "role": self.role,
            "tool_call_id": self.tool_call_id,
            "name": self.name,
            "content": self.content,
        }


# Discriminated union of all message types
Message = Union[UserMessage, SystemMessage, AssistantMessage, ToolResultMessage]


class LLMResponse(BaseModel):
    """Normalized response from LLM provider"""

    message: str = Field(description="Text content of the response")
    tool_calls: List[ToolCall] = Field(
        default_factory=list,
        description="Tool calls requested by the assistant"
    )
    done: bool = Field(description="Whether the conversation is complete (no tool calls)")
    raw_message: Optional[Any] = Field(
        default=None,
        description="Original provider response (for debugging)"
    )

    model_config = ConfigDict(extra="allow", arbitrary_types_allowed=True)


class ToolDefinition(BaseModel):
    """Definition of a tool available to the agent"""

    name: str = Field(description="Tool name (must be unique)")
    description: str = Field(description="What the tool does")
    parameters: Dict[str, Any] = Field(
        description="JSON Schema describing the tool's parameters"
    )

    model_config = ConfigDict(extra="allow")

    def to_openai_format(self) -> Dict[str, Any]:
        """Convert to OpenAI function calling format"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            }
        }


# Helper functions for backward compatibility
def message_to_dict(message: Message) -> Dict[str, Any]:
    """Convert a typed message to dictionary format"""
    return message.to_dict()


def messages_to_dicts(messages: List[Message]) -> List[Dict[str, Any]]:
    """Convert list of typed messages to list of dicts"""
    return [msg.to_dict() for msg in messages]


def dict_to_message(msg_dict: Dict[str, Any]) -> Message:
    """
    Convert dictionary to typed message.

    Args:
        msg_dict: Message dictionary with 'role' key

    Returns:
        Typed message instance

    Raises:
        ValueError: If role is unknown
    """
    role = msg_dict.get("role")

    if role == "user":
        return UserMessage(**msg_dict)
    elif role == "system":
        return SystemMessage(**msg_dict)
    elif role == "assistant":
        return AssistantMessage(**msg_dict)
    elif role == "tool":
        return ToolResultMessage(**msg_dict)
    else:
        raise ValueError(f"Unknown message role: {role}")


def dicts_to_messages(msg_dicts: List[Dict[str, Any]]) -> List[Message]:
    """Convert list of dicts to list of typed messages"""
    return [dict_to_message(msg) for msg in msg_dicts]
