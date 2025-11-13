"""Pydantic models for Opus data structures"""

from opus.models.config import (
    OpusConfig,
    ToolConfig,
    MODEL_ALIASES,
    BUILTIN_TOOLS,
)

from opus.models.messages import (
    Message,
    UserMessage,
    SystemMessage,
    AssistantMessage,
    ToolResultMessage,
    ToolCall,
    ToolCallOpenAI,
    FunctionCall,
    LLMResponse,
    ToolDefinition,
    message_to_dict,
    messages_to_dicts,
    dict_to_message,
    dicts_to_messages,
)

__all__ = [
    # Config models
    "OpusConfig",
    "ToolConfig",
    "MODEL_ALIASES",
    "BUILTIN_TOOLS",
    # Message models
    "Message",
    "UserMessage",
    "SystemMessage",
    "AssistantMessage",
    "ToolResultMessage",
    "ToolCall",
    "ToolCallOpenAI",
    "FunctionCall",
    "LLMResponse",
    "ToolDefinition",
    # Helper functions
    "message_to_dict",
    "messages_to_dicts",
    "dict_to_message",
    "dicts_to_messages",
]
