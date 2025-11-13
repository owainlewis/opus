"""Configuration models for Opus with Pydantic validation"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from pydantic import (
    BaseModel,
    Field,
    field_validator,
    model_validator,
    ConfigDict,
)
import yaml

logger = logging.getLogger(__name__)

# Model aliases for user convenience (inspired by Aider)
MODEL_ALIASES = {
    # Anthropic
    "sonnet": "anthropic/claude-sonnet-4-20250514",
    "sonnet-4": "anthropic/claude-sonnet-4-20250514",
    "sonnet-3.5": "anthropic/claude-3-5-sonnet-20241022",
    "opus": "anthropic/claude-opus-4-20250514",

    # OpenAI
    "4o": "gpt-4o",
    "mini": "gpt-4.1-mini",
    "o1": "o1",
    "o1-mini": "o1-mini",

    # Google
    "flash": "gemini/gemini-2.5-flash",
    "flash-2": "gemini/gemini-2.5-flash",
    "gemini": "gemini/gemini-1.5-pro",

    # Oracle GenAI
    "grok": "xai.grok-4",
    "grok-4": "xai.grok-4",
    "command-r": "cohere.command-r-plus",
    "llama": "meta.llama-3-1-405b-instruct",
}

# Provider detection map
PROVIDER_PREFIXES = {
    "anthropic/": "litellm",
    "gemini/": "litellm",
    "gpt-": "litellm",
    "o1": "litellm",
    "xai.": "oracle",
    "cohere.": "oracle",
    "meta.": "oracle",
}

# Provider API key requirements
PROVIDER_API_KEYS = {
    "litellm": {
        "anthropic/": "ANTHROPIC_API_KEY",
        "gemini/": "GOOGLE_API_KEY",
        "gpt-": "OPENAI_API_KEY",
        "o1": "OPENAI_API_KEY",
    },
    "oracle": {
        # Oracle GenAI uses OCI config file, no env var needed
    }
}

# Built-in tools that are always available
BUILTIN_TOOLS = [
    "bash",
    "file_read",
    "file_write",
    "file_edit",
    "fetch_url",
    "run_recipe",
    "get_current_time"
]


class ToolConfig(BaseModel):
    """Configuration for a single tool"""

    enabled: bool = Field(default=True, description="Whether the tool is enabled")
    approval: bool = Field(default=False, description="Whether tool requires user approval")
    source: Optional[Path] = Field(default=None, description="Path to custom tool YAML file")
    timeout: Optional[int] = Field(default=None, description="Tool-specific timeout in seconds")
    max_retries: Optional[int] = Field(default=None, description="Maximum retry attempts for this tool")

    model_config = ConfigDict(extra="allow")  # Allow extra fields for custom tool configs

    @field_validator("source")
    @classmethod
    def validate_source_exists(cls, v: Optional[Path]) -> Optional[Path]:
        """Validate that source file exists if specified"""
        if v is not None and not v.exists():
            # Don't fail here - will be resolved relative to config dir later
            pass
        return v


class OpusConfig(BaseModel):
    """
    Opus configuration with validation.

    Supports multiple configuration sources:
    - YAML config file
    - Environment variables
    - Programmatic configuration
    """

    # LLM Settings
    provider: str = Field(
        default="litellm",
        description="LLM provider (oracle, litellm)"
    )
    model: str = Field(
        default="gpt-4.1-mini",
        description="Model identifier or alias"
    )

    # Agent Behavior
    max_iterations: int = Field(
        default=25,
        ge=1,
        le=100,
        description="Maximum conversation turns per request"
    )
    max_retry_attempts: int = Field(
        default=2,
        ge=0,
        le=10,
        description="Maximum retry attempts for failed tools"
    )
    default_timeout: int = Field(
        default=30,
        ge=1,
        le=600,
        description="Default timeout for tool execution (seconds)"
    )

    # UI Settings
    show_tool_output: bool = Field(
        default=False,
        description="Show detailed tool execution output"
    )

    # Tools Configuration
    tools: Dict[str, ToolConfig] = Field(
        default_factory=dict,
        description="Tool configurations"
    )

    # Internal fields (not from config file)
    config_path: Path = Field(
        default=Path.home() / ".opus" / "config.yaml",
        exclude=True,
        description="Path to config file"
    )
    config_dir: Path = Field(
        default=Path.cwd(),
        exclude=True,
        description="Directory containing config file"
    )

    model_config = ConfigDict(
        extra="allow",  # Allow extra fields for forward compatibility
        validate_assignment=False,  # Disabled to avoid recursion in normalizers
    )

    @field_validator("model", mode="before")
    @classmethod
    def resolve_model_alias(cls, v: str) -> str:
        """Resolve model aliases to full model names"""
        return MODEL_ALIASES.get(v, v)

    @field_validator("provider", mode="after")
    @classmethod
    def validate_provider(cls, v: str) -> str:
        """Validate provider is supported"""
        if v not in ["oracle", "litellm"]:
            raise ValueError(
                f"Unsupported provider '{v}'. "
                f"Supported providers: oracle, litellm"
            )
        return v

    @model_validator(mode="after")
    def auto_detect_provider(self) -> "OpusConfig":
        """Auto-detect provider from model name if not explicitly set"""
        # If provider is default (litellm), check if model suggests oracle
        if self.provider == "litellm":
            for prefix, provider in PROVIDER_PREFIXES.items():
                if self.model.startswith(prefix):
                    if provider == "oracle":
                        self.provider = "oracle"
                    break
        return self

    @model_validator(mode="after")
    def check_api_keys(self) -> "OpusConfig":
        """Check that required API keys are set (warning only)"""
        provider_keys = PROVIDER_API_KEYS.get(self.provider, {})

        for prefix, env_var in provider_keys.items():
            if self.model.startswith(prefix):
                if not os.getenv(env_var):
                    logger.warning(
                        f"API key '{env_var}' not set for model '{self.model}'. "
                        f"Set it with: export {env_var}=your-key-here"
                    )
        return self

    @model_validator(mode="after")
    def normalize_tool_configs(self) -> "OpusConfig":
        """Normalize tool configurations (convert bool to ToolConfig)"""
        normalized_tools = {}

        for tool_name, tool_config in self.tools.items():
            if isinstance(tool_config, bool):
                # Convert boolean to ToolConfig
                normalized_tools[tool_name] = ToolConfig(enabled=tool_config)
            elif isinstance(tool_config, dict):
                # Convert dict to ToolConfig
                normalized_tools[tool_name] = ToolConfig(**tool_config)
            elif isinstance(tool_config, ToolConfig):
                # Already a ToolConfig
                normalized_tools[tool_name] = tool_config
            else:
                logger.warning(f"Invalid tool config for '{tool_name}', using defaults")
                normalized_tools[tool_name] = ToolConfig()

        self.tools = normalized_tools
        return self

    @classmethod
    def from_yaml(cls, config_path: Optional[str] = None) -> "OpusConfig":
        """
        Load configuration from YAML file.

        Args:
            config_path: Path to config.yaml (defaults to ~/.opus/config.yaml)

        Returns:
            OpusConfig instance with validation

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config validation fails
        """
        default_path = Path.home() / ".opus" / "config.yaml"

        if config_path is None:
            path = default_path
        else:
            path = Path(config_path)

        if not path.exists():
            raise FileNotFoundError(
                f"Configuration file not found: {path}\n"
                f"Run 'opus init' to create a config file, or manually create one at {default_path}"
            )

        # Load YAML
        try:
            with open(path, "r") as f:
                config_data = yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in config file {path}: {e}")

        # Create config with validation
        config = cls(**config_data)

        # Set internal fields
        config.config_path = path
        config.config_dir = path.parent

        return config

    def get_enabled_tools(self) -> List[str]:
        """
        Get list of enabled tools.

        Built-in tools are enabled by default unless explicitly disabled.
        Custom tools must be explicitly listed in config.

        Returns:
            List of enabled tool names
        """
        enabled = []

        # Add built-in tools (enabled by default)
        for builtin_tool in BUILTIN_TOOLS:
            if builtin_tool in self.tools:
                if self.tools[builtin_tool].enabled:
                    enabled.append(builtin_tool)
            else:
                # Built-in tools are enabled by default if not configured
                enabled.append(builtin_tool)

        # Add custom tools from config (must be explicitly enabled)
        for tool_name, tool_config in self.tools.items():
            if tool_name not in BUILTIN_TOOLS and tool_config.enabled:
                enabled.append(tool_name)

        return enabled

    def get_tool_config(self, tool_name: str) -> ToolConfig:
        """
        Get configuration for a specific tool.

        Args:
            tool_name: Name of the tool

        Returns:
            Tool configuration (default if not configured)
        """
        return self.tools.get(tool_name, ToolConfig())

    def get_tool_source(self, tool_name: str) -> Optional[Path]:
        """
        Get the source file path for a custom tool.

        Args:
            tool_name: Name of the tool

        Returns:
            Absolute path to tool YAML file, or None if not specified
        """
        tool_config = self.get_tool_config(tool_name)
        source = tool_config.source

        if source:
            # Resolve relative paths relative to config directory
            if not source.is_absolute():
                source = self.config_dir / source
            return source.resolve()

        return None
