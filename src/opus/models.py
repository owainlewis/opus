"""Pydantic models for Opus configuration and data structures"""

import logging
import os
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
import yaml
from pydantic import (
    BaseModel,
    Field,
    field_validator,
    model_validator,
    ConfigDict,
)
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)

# Built-in tools that are always available
BUILTIN_TOOLS = [
    "bash",
    "file_read",
    "file_write",
    "file_edit",
    "fetch_url",
    "run_recipe",
    "get_current_time",
    "run_subagents",
]


class Theme(BaseModel):
    """Professional color theme for Opus UI"""

    model_config = ConfigDict(frozen=True)

    name: str

    # Primary colors
    primary: str = Field(description="Main accent color")
    secondary: str = Field(description="Secondary accent")

    # Status colors
    success: str = Field(description="Success indicators")
    warning: str = Field(description="Warnings")
    error: str = Field(description="Errors")
    info: str = Field(description="Information")

    # Text colors
    text: str = Field(description="Normal text")
    dim: str = Field(description="Dimmed/secondary text")
    bold: str = Field(description="Emphasized text")

    # Tool execution colors
    tool_name: str = Field(description="Tool name display")
    tool_args: str = Field(description="Tool arguments")
    tool_output: str = Field(description="Tool output text")

    # UI elements
    spinner: str = Field(description="Thinking/loading spinner")
    prompt: str = Field(description="User prompt (>:)")
    border: str = Field(description="Borders and separators")

    @field_validator(
        "primary",
        "secondary",
        "success",
        "warning",
        "error",
        "info",
        "text",
        "dim",
        "spinner",
        "border",
    )
    @classmethod
    def validate_color(cls, v: str) -> str:
        """Validate color is a valid hex color or rich color name"""
        if not v:
            raise ValueError("Color value cannot be empty")
        # Accept hex colors, rich color names, or rich styling (bold, etc)
        return v


class ToolError(BaseModel):
    """Structured error information for tool failures"""

    tool_name: str = Field(description="Name of the tool that failed")
    error_message: str = Field(description="Error message from the tool")
    arguments: Dict[str, Any] = Field(
        default_factory=dict, description="Arguments passed to the tool"
    )
    recovery_hints: str = Field(
        default="", description="Hints for recovering from the error"
    )

    @classmethod
    def from_exception(
        cls, tool_name: str, exception: Exception, arguments: Dict[str, Any]
    ) -> "ToolError":
        """
        Create a ToolError from an exception.

        Args:
            tool_name: Name of the tool that failed
            exception: The exception that was raised
            arguments: Arguments that were passed to the tool

        Returns:
            ToolError instance with recovery hints
        """
        error_msg = str(exception)
        hints = cls._generate_recovery_hints(tool_name, error_msg, arguments)

        return cls(
            tool_name=tool_name,
            error_message=error_msg,
            arguments=arguments,
            recovery_hints=hints,
        )

    @staticmethod
    def _generate_recovery_hints(
        tool_name: str, error_msg: str, arguments: Dict[str, Any]
    ) -> str:
        """
        Generate recovery hints based on error patterns.

        Args:
            tool_name: Name of the tool
            error_msg: Error message
            arguments: Tool arguments

        Returns:
            Recovery hints as string
        """
        hints = []

        # Command not found
        if "Command not found" in error_msg or "command not found" in error_msg.lower():
            hints.append("- The command is not installed or not in PATH")
            hints.append("- Check if the tool needs to be installed")
            hints.append("- Try using an alternative tool or command")

        # Permission denied
        elif "Permission denied" in error_msg:
            hints.append("- The tool doesn't have permission to access the resource")
            hints.append("- Check file/directory permissions")
            hints.append("- Try with a different path or ask the user for access")

        # File not found
        elif "No such file or directory" in error_msg or "File not found" in error_msg:
            hints.append("- The specified file or directory doesn't exist")
            hints.append("- Check the path is correct")
            hints.append("- Use bash tool to list directory contents first")

        # Timeout
        elif "timed out" in error_msg.lower():
            hints.append("- The tool took too long to execute")
            hints.append("- Try breaking the task into smaller steps")
            hints.append("- Consider if the operation is genuinely long-running")

        # Invalid syntax
        elif "Invalid command syntax" in error_msg or "SyntaxError" in error_msg:
            hints.append("- The command syntax is invalid")
            hints.append("- Check the parameter format")
            hints.append("- Review the tool's parameter requirements")

        # Missing parameter
        elif "Missing required parameter" in error_msg:
            hints.append("- A required parameter is missing")
            hints.append("- Check the tool definition for required parameters")
            hints.append("- Provide all required parameters")

        # Generic hints if no specific pattern matched
        if not hints:
            hints.append("- Review the error message for clues")
            hints.append("- Check if the parameters are correct")
            hints.append("- Try a different approach or tool")

        return "\n".join(hints)

    def to_llm_message(self, attempt: int, max_attempts: int) -> str:
        """
        Format error for LLM with recovery guidance.

        Args:
            attempt: Current attempt number
            max_attempts: Maximum number of attempts allowed

        Returns:
            Formatted error message for LLM
        """
        can_retry = attempt < max_attempts

        message_parts = [
            f"Tool '{self.tool_name}' failed (attempt {attempt}/{max_attempts})",
            "",
            "Error:",
            self.error_message,
            "",
            "Arguments used:",
            str(self.arguments),
        ]

        if can_retry:
            message_parts.extend(
                [
                    "",
                    "Recovery hints:",
                    self.recovery_hints,
                    "",
                    f"You have {max_attempts - attempt} more attempt(s) to fix this.",
                    "Please adjust your approach based on the error and hints above.",
                ]
            )
        else:
            message_parts.extend(
                [
                    "",
                    "Maximum retry attempts reached.",
                    "Consider:",
                    "- Asking the user for help",
                    "- Trying a completely different approach",
                    "- Breaking down the task into simpler steps",
                ]
            )

        return "\n".join(message_parts)


def expand_env_vars(data: Any) -> Any:
    """
    Recursively expand environment variables in configuration data.

    Supports the following formats:
    - ${VAR_NAME} - expands to environment variable value
    - ${VAR_NAME:-default} - expands to value or default if not set

    Args:
        data: Configuration data (dict, list, str, or other)

    Returns:
        Configuration data with environment variables expanded
    """
    if isinstance(data, dict):
        return {key: expand_env_vars(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [expand_env_vars(item) for item in data]
    elif isinstance(data, str):
        # Pattern to match ${VAR_NAME} or ${VAR_NAME:-default}
        def replace_var(match):
            var_expr = match.group(1)

            # Check if there's a default value (VAR_NAME:-default)
            if ":-" in var_expr:
                var_name, default_value = var_expr.split(":-", 1)
                return os.getenv(var_name.strip(), default_value)
            else:
                # No default, just get the var (returns empty string if not found)
                var_name = var_expr.strip()
                value = os.getenv(var_name)
                if value is None:
                    logger.warning(
                        f"Environment variable '{var_name}' not found in config expansion"
                    )
                    return match.group(0)  # Return original ${VAR} if not found
                return value

        # Replace ${VAR} or ${VAR:-default} patterns
        return re.sub(r'\$\{([^}]+)\}', replace_var, data)
    else:
        return data


class OpusConfig(BaseSettings):
    """
    Opus configuration manager with Pydantic validation.

    Loads configuration from ~/.opus/config.yaml or custom path.
    Manages LLM provider settings, tool configurations, and behavior settings.
    Supports environment variable overrides with OPUS_ prefix.
    """

    model_config = ConfigDict(
        env_prefix="OPUS_",
        case_sensitive=False,
        extra="allow",
        validate_assignment=True,
    )

    # Internal fields
    config_data: Dict[str, Any] = Field(
        default_factory=dict, description="Raw configuration data from YAML"
    )
    config_path: Path = Field(
        default=Path.home() / ".opus" / "config.yaml",
        description="Path to configuration file",
    )

    # LLM settings
    provider: str = Field(
        default="litellm", description="LLM provider (anthropic, oracle, litellm)"
    )
    model: str = Field(
        default="gpt-4.1-mini", description="Model identifier for the LLM"
    )

    # Agent behavior settings
    max_iterations: int = Field(
        default=25, ge=1, le=1000, description="Maximum agent iterations"
    )
    max_retry_attempts: int = Field(
        default=2, ge=0, le=10, description="Maximum retry attempts for failed tools"
    )
    default_timeout: int = Field(
        default=30, ge=1, le=600, description="Default timeout for tool execution (seconds)"
    )

    # Sub-agent settings
    subagent_max_turns: int = Field(
        default=15, ge=1, le=100, description="Maximum turns for sub-agents"
    )
    subagent_timeout: int = Field(
        default=300, ge=1, le=3600, description="Timeout for sub-agent execution (seconds)"
    )

    # UI settings
    show_tool_output: bool = Field(
        default=False, description="Show detailed tool output in terminal"
    )

    # Tools configuration
    tools_config: Dict[str, Any] = Field(
        default_factory=dict, description="Tool-specific configurations"
    )

    # Anthropic-specific settings
    anthropic_api_key: Optional[str] = Field(
        default=None, description="Anthropic API key (or use ANTHROPIC_API_KEY env var)"
    )
    anthropic_prompt_caching: bool = Field(
        default=True, description="Enable Anthropic prompt caching to reduce costs"
    )
    anthropic_max_tokens: int = Field(
        default=4096, ge=1, le=200000, description="Maximum tokens for Anthropic responses"
    )

    # OpenAI-specific settings
    openai_api_key: Optional[str] = Field(
        default=None, description="OpenAI API key (or use OPENAI_API_KEY env var)"
    )
    openai_base_url: Optional[str] = Field(
        default=None, description="Custom OpenAI base URL for compatible APIs (Kimi, DeepSeek, etc.)"
    )
    openai_api_type: str = Field(
        default="chat_completions",
        description="OpenAI API type: 'chat_completions' (default) or 'responses' (advanced features)"
    )
    openai_max_tokens: int = Field(
        default=4096, ge=1, le=128000, description="Maximum tokens for OpenAI responses"
    )

    @property
    def config_dir(self) -> Path:
        """
        Get the directory containing the config file.

        This fixes the bug where config_dir was set to Path.cwd() when using
        the default config path.
        """
        return self.config_path.parent

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, v: str) -> str:
        """Validate provider is one of the supported providers"""
        valid_providers = ["anthropic", "openai", "oracle", "litellm"]
        if v not in valid_providers:
            logger.warning(
                f"Provider '{v}' is not in the standard list {valid_providers}. "
                "Proceeding anyway - custom providers may work."
            )
        return v

    @field_validator("openai_api_type")
    @classmethod
    def validate_api_type(cls, v: str) -> str:
        """Validate API type is one of the valid values"""
        valid_types = ["chat_completions", "responses"]
        if v not in valid_types:
            raise ValueError(f"openai_api_type must be one of {valid_types}, got: {v}")
        return v

    @field_validator("config_path")
    @classmethod
    def validate_config_path(cls, v: Path) -> Path:
        """Convert string paths to Path objects"""
        if isinstance(v, str):
            return Path(v).expanduser()
        return v

    @model_validator(mode="after")
    def normalize_tools_config(self) -> "OpusConfig":
        """Normalize tool config format (convert bool to dict)"""
        for tool_name, tool_config in self.tools_config.items():
            if not isinstance(tool_config, dict):
                # Convert simple boolean to dict format
                self.tools_config[tool_name] = {"enabled": bool(tool_config)}
        return self

    @classmethod
    def from_yaml(cls, config_path: Optional[str] = None) -> "OpusConfig":
        """
        Load configuration from YAML file.

        Args:
            config_path: Path to config.yaml (defaults to ~/.opus/config.yaml)

        Returns:
            OpusConfig instance

        Raises:
            FileNotFoundError: If config file doesn't exist
            yaml.YAMLError: If config file is invalid
        """
        if config_path is None:
            config_path = Path.home() / ".opus" / "config.yaml"
        else:
            config_path = Path(config_path).expanduser()

        if not config_path.exists():
            raise FileNotFoundError(
                f"Configuration file not found: {config_path}\n"
                f"Please create a config.yaml file at {config_path}"
            )

        with open(config_path, "r") as f:
            config_data = yaml.safe_load(f) or {}

        # Expand environment variables in configuration
        config_data = expand_env_vars(config_data)

        # Map 'tools' from YAML to 'tools_config' model field
        if "tools" in config_data:
            config_data["tools_config"] = config_data.pop("tools")

        # Create config with data from YAML and path
        return cls(
            config_data=config_data,
            config_path=config_path,
            **config_data,  # Unpack YAML data into model fields
        )

    def get_enabled_tools(self) -> List[str]:
        """
        Get list of enabled tools.

        Built-in tools are always enabled unless explicitly disabled in config.
        Custom tools must be listed in config.

        Returns:
            List of tool names that are enabled
        """
        enabled = []

        # Add built-in tools (enabled by default, unless explicitly disabled)
        for builtin_tool in BUILTIN_TOOLS:
            tool_config = self.tools_config.get(builtin_tool, {})
            if tool_config.get("enabled", True):  # Default to enabled
                enabled.append(builtin_tool)

        # Add custom tools from config (must be explicitly listed with source)
        for tool_name, tool_config in self.tools_config.items():
            if tool_name not in BUILTIN_TOOLS and tool_config.get("enabled", True):
                enabled.append(tool_name)

        return enabled

    def get_tool_config(self, tool_name: str) -> Dict[str, Any]:
        """
        Get configuration for a specific tool.

        Args:
            tool_name: Name of the tool

        Returns:
            Tool configuration dictionary
        """
        return self.tools_config.get(tool_name, {})

    def get_tool_source(self, tool_name: str) -> Optional[Path]:
        """
        Get the source file path for a custom tool.

        Args:
            tool_name: Name of the tool

        Returns:
            Absolute path to tool YAML file, or None if not specified
        """
        tool_config = self.get_tool_config(tool_name)
        source = tool_config.get("source")

        if source:
            source_path = Path(source)
            # Resolve relative paths relative to config directory
            if not source_path.is_absolute():
                source_path = self.config_dir / source_path
            return source_path.resolve()

        return None


# Default theme instance
DEFAULT_THEME = Theme(
    name="Opus Dark",
    # Primary: Professional blue - not too bright, excellent contrast
    primary="#5B9BD5",  # Calm, professional blue
    secondary="#7AA3CC",  # Slightly muted blue
    # Status colors: Clear but not harsh
    success="#4EC9B0",  # Teal green - modern and clear
    warning="#D4A960",  # Warm amber - visible but not alarming
    error="#E06C75",  # Soft red - clear without being harsh
    info="#61AFEF",  # Light blue - informative
    # Text: High readability with good hierarchy
    text="#D4D4D4",  # Soft white - easy on eyes
    dim="#6B7280",  # Medium gray - clear hierarchy
    bold="bold #E5E7EB",  # Slightly brighter for emphasis
    # Tool execution: Subtle but clear
    tool_name="bold #61AFEF",  # Bright blue for tool names
    tool_args="#6B7280",  # Gray for args - not distracting
    tool_output="#9CA3AF",  # Lighter gray for output
    # UI elements: Clean and minimal
    spinner="#5B9BD5",  # Match primary
    prompt="bold #61AFEF",  # Inviting blue
    border="#374151",  # Subtle border - barely visible
)


def get_theme() -> Theme:
    """
    Get the Opus theme.

    Returns:
        Theme object
    """
    return DEFAULT_THEME
