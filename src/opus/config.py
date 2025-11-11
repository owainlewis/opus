"""Configuration management for Opus"""

import os
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import yaml

logger = logging.getLogger(__name__)


class OpusConfig:
    """
    Opus configuration manager.

    Loads configuration from ~/.opus/config.yaml or custom path.
    Manages LLM provider settings, tool configurations, and behavior settings.
    """

    DEFAULT_CONFIG_PATH = Path.home() / ".opus" / "config.yaml"

    def __init__(self, config_data: Dict[str, Any], config_path: Optional[Path] = None):
        """
        Initialize configuration.

        Args:
            config_data: Parsed configuration dictionary
            config_path: Path to config file (for resolving relative tool paths)
        """
        self.config_data = config_data
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH
        self.config_dir = self.config_path.parent if config_path else Path.cwd()

        # LLM settings
        self.provider = config_data.get("provider", "anthropic")
        self.model = config_data.get("model", "claude-sonnet-4-20250514")

        # Agent behavior settings
        self.max_iterations = config_data.get("max_iterations", 25)
        self.max_retry_attempts = 2  # Hardcoded - rarely needs adjustment
        self.default_timeout = config_data.get("default_timeout", 30)

        # UI settings
        self.theme = config_data.get("theme", "default")
        self.show_tool_output = config_data.get("show_tool_output", True)

        # Parse tools configuration
        self.tools_config = config_data.get("tools", {})

        # Normalize tool config format (convert bool to dict)
        for tool_name, tool_config in self.tools_config.items():
            if not isinstance(tool_config, dict):
                # Convert simple boolean to dict format
                self.tools_config[tool_name] = {"enabled": bool(tool_config)}

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
            config_path = cls.DEFAULT_CONFIG_PATH
        else:
            config_path = Path(config_path)

        if not config_path.exists():
            raise FileNotFoundError(
                f"Configuration file not found: {config_path}\n"
                f"Please create a config.yaml file at {config_path}"
            )

        with open(config_path, "r") as f:
            config_data = yaml.safe_load(f) or {}

        return cls(config_data, config_path)

    def get_enabled_tools(self) -> List[str]:
        """
        Get list of enabled tools.

        Returns:
            List of tool names that are enabled
        """
        return [
            tool_name
            for tool_name, tool_config in self.tools_config.items()
            if tool_config.get("enabled", True)
        ]

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
