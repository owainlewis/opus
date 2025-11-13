#!/usr/bin/env python3
"""Test script for Pydantic models integration"""

import sys
from opus.models import (
    OpusConfig,
    ToolConfig,
    MODEL_ALIASES,
    UserMessage,
    AssistantMessage,
    ToolResultMessage,
    ToolCall,
)


def test_model_aliases():
    """Test model alias resolution"""
    print("Testing model aliases...")

    # Test alias resolution
    config = OpusConfig(model="sonnet")
    assert config.model == "anthropic/claude-sonnet-4-20250514", "Alias resolution failed"
    print(f"  ✓ 'sonnet' resolves to '{config.model}'")

    config = OpusConfig(model="4o")
    assert config.model == "gpt-4o", "Alias resolution failed"
    print(f"  ✓ '4o' resolves to '{config.model}'")

    config = OpusConfig(model="mini")
    assert config.model == "gpt-4.1-mini", "Alias resolution failed"
    print(f"  ✓ 'mini' resolves to '{config.model}'")

    print(f"  ✓ Total {len(MODEL_ALIASES)} aliases defined\n")


def test_config_validation():
    """Test config validation"""
    print("Testing config validation...")

    # Test default config
    config = OpusConfig()
    assert config.provider == "litellm"
    assert config.model == "gpt-4.1-mini"
    assert config.max_iterations == 25
    assert config.default_timeout == 30
    print("  ✓ Default config values correct")

    # Test provider auto-detection
    config = OpusConfig(model="xai.grok-4")
    assert config.provider == "oracle", "Provider auto-detection failed"
    print("  ✓ Provider auto-detected for Oracle GenAI models")

    config = OpusConfig(model="anthropic/claude-sonnet-4-20250514")
    assert config.provider == "litellm", "Provider should be litellm for Anthropic"
    print("  ✓ Provider correct for Anthropic models\n")


def test_tool_config():
    """Test tool configuration"""
    print("Testing tool configuration...")

    # Test ToolConfig creation
    tool_cfg = ToolConfig(enabled=True, approval=True)
    assert tool_cfg.enabled is True
    assert tool_cfg.approval is True
    print("  ✓ ToolConfig creation works")

    # Test OpusConfig with tools
    config = OpusConfig(
        tools={
            "bash": {"enabled": True, "approval": True},
            "file_read": {"enabled": True, "approval": False},
        }
    )

    bash_cfg = config.get_tool_config("bash")
    assert isinstance(bash_cfg, ToolConfig)
    assert bash_cfg.approval is True
    print("  ✓ Tool config normalization works")

    # Test enabled tools
    enabled = config.get_enabled_tools()
    assert "bash" in enabled
    assert "file_read" in enabled
    print(f"  ✓ Enabled tools: {len(enabled)} tools\n")


def test_message_types():
    """Test message type models"""
    print("Testing message types...")

    # Test UserMessage
    user_msg = UserMessage(content="Hello, world!")
    assert user_msg.role == "user"
    assert user_msg.content == "Hello, world!"
    msg_dict = user_msg.to_dict()
    assert msg_dict["role"] == "user"
    assert msg_dict["content"] == "Hello, world!"
    print("  ✓ UserMessage works")

    # Test AssistantMessage
    asst_msg = AssistantMessage(content="Hi there!")
    assert asst_msg.role == "assistant"
    assert asst_msg.content == "Hi there!"
    print("  ✓ AssistantMessage works")

    # Test AssistantMessage with tool calls
    from opus.models.messages import ToolCallOpenAI, FunctionCall

    tool_call = ToolCallOpenAI(
        id="call_123",
        function=FunctionCall(name="bash", arguments='{"command": "ls"}'),
    )
    asst_msg_with_tools = AssistantMessage(content=None, tool_calls=[tool_call])
    assert asst_msg_with_tools.tool_calls is not None
    assert len(asst_msg_with_tools.tool_calls) == 1
    print("  ✓ AssistantMessage with tool calls works")

    # Test ToolResultMessage
    tool_result = ToolResultMessage(
        tool_call_id="call_123", name="bash", content="file1.txt\nfile2.txt"
    )
    assert tool_result.role == "tool"
    assert tool_result.tool_call_id == "call_123"
    print("  ✓ ToolResultMessage works\n")


def test_tool_call():
    """Test ToolCall model"""
    print("Testing ToolCall model...")

    tool_call = ToolCall(id="call_123", name="bash", arguments={"command": "ls -la"})
    assert tool_call.id == "call_123"
    assert tool_call.name == "bash"
    assert tool_call.arguments["command"] == "ls -la"
    print("  ✓ ToolCall model works\n")


def main():
    """Run all tests"""
    print("=" * 60)
    print("Testing Pydantic Models for Opus")
    print("=" * 60)
    print()

    try:
        test_model_aliases()
        test_config_validation()
        test_tool_config()
        test_message_types()
        test_tool_call()

        print("=" * 60)
        print("✓ ALL TESTS PASSED!")
        print("=" * 60)
        return 0

    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
