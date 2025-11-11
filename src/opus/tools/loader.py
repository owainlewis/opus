"""Tool loader for loading custom script-based tools"""

import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import yaml

from opus.config import OpusConfig

logger = logging.getLogger(__name__)


class ToolLoader:
    """
    Loads and manages custom tools from YAML definitions.

    Each tool is defined by a YAML file containing:
    - name: Tool name
    - description: What the tool does
    - script: Command to execute with parameter placeholders
    - parameters: JSON Schema for parameters
    """

    def __init__(self):
        """Initialize tool loader"""
        self.tools_by_name = {}
        self.failed_tools = {}  # Dict[tool_name, error_message]

    def load_tools(
        self,
        config: OpusConfig,
        enabled_tools: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Load tools based on configuration.

        Args:
            config: Opus configuration
            enabled_tools: List of tool names to load (None = load all enabled)

        Returns:
            List of tool definitions in universal format
        """
        if enabled_tools is None:
            enabled_tools = config.get_enabled_tools()

        loaded_tools = []

        for tool_name in enabled_tools:
            tool_source = config.get_tool_source(tool_name)

            if tool_source:
                # Custom tool with source file
                tool, error = self._load_tool_from_file(tool_source)
                if tool:
                    loaded_tools.append(tool)
                    self.tools_by_name[tool_name] = tool
                else:
                    self.failed_tools[tool_name] = error or "Unknown error loading tool"
            else:
                # Built-in tool
                tool = self._load_builtin_tool(tool_name)
                if tool:
                    loaded_tools.append(tool)
                    self.tools_by_name[tool_name] = tool
                else:
                    self.failed_tools[tool_name] = f"Built-in tool '{tool_name}' not found"

        logger.info(f"Loaded {len(loaded_tools)} tools: {[t['name'] for t in loaded_tools]}")
        if self.failed_tools:
            logger.warning(f"Failed to load {len(self.failed_tools)} tools: {list(self.failed_tools.keys())}")

        return loaded_tools

    def _load_tool_from_file(self, tool_path: Path) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Load a tool definition from a YAML file.

        Args:
            tool_path: Path to tool YAML file

        Returns:
            Tuple of (tool definition dict or None, error message or None)
        """
        try:
            if not tool_path.exists():
                error_msg = f"Tool file not found: {tool_path}"
                logger.error(error_msg)
                return None, error_msg

            with open(tool_path, "r") as f:
                tool_def = yaml.safe_load(f)

            # Validate required fields
            required_fields = ["name", "description", "script"]
            for field in required_fields:
                if field not in tool_def:
                    error_msg = f"Tool definition missing required field '{field}': {tool_path}"
                    logger.error(error_msg)
                    return None, error_msg

            # Add tool path for executor to use as working directory (convert to string for JSON serialization)
            tool_def["tool_path"] = str(tool_path.parent)

            # Ensure parameters has proper structure
            if "parameters" not in tool_def:
                tool_def["parameters"] = {"type": "object", "properties": {}, "required": []}

            logger.info(f"Loaded tool '{tool_def['name']}' from {tool_path}")

            return tool_def, None

        except Exception as e:
            error_msg = f"Failed to load tool from {tool_path}: {e}"
            logger.error(error_msg)
            return None, error_msg

    def _load_builtin_tool(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        Load a built-in tool definition.

        Args:
            tool_name: Name of the built-in tool

        Returns:
            Tool definition dict, or None if not found
        """
        # Import fetch tool definition if needed
        if tool_name == "fetch":
            from opus.tools.fetch import FETCH_TOOL_DEFINITION, execute_fetch
            tool_def = FETCH_TOOL_DEFINITION.copy()
            tool_def["tool_path"] = str(Path.cwd())
            tool_def["python_callable"] = execute_fetch  # Mark as Python callable
            logger.info(f"Loaded built-in tool '{tool_name}'")
            return tool_def

        # Import recipe tool definition if needed
        if tool_name == "recipe":
            from opus.tools.recipe_tool import RECIPE_TOOL_DEFINITION, execute_recipe_tool
            tool_def = RECIPE_TOOL_DEFINITION.copy()
            tool_def["tool_path"] = str(Path.cwd())
            tool_def["python_callable"] = execute_recipe_tool  # Mark as Python callable
            logger.info(f"Loaded built-in tool '{tool_name}'")
            return tool_def

        # Built-in script-based tools
        BUILTIN_TOOLS = {
            "bash": {
                "name": "bash",
                "description": "Execute a bash command in the shell. Use this for terminal operations, running scripts, or system commands.",
                "script": "bash -c {command}",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "The bash command to execute"
                        }
                    },
                    "required": ["command"]
                },
                "tool_path": str(Path.cwd()),
            },
            "read": {
                "name": "read",
                "description": "Read the contents of a file. Returns the file content as text.",
                "script": "cat {file}",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file": {
                            "type": "string",
                            "description": "Path to the file to read"
                        }
                    },
                    "required": ["file"]
                },
                "tool_path": str(Path.cwd()),
            }
        }

        if tool_name in BUILTIN_TOOLS:
            logger.info(f"Loaded built-in tool '{tool_name}'")
            return BUILTIN_TOOLS[tool_name]

        logger.warning(f"Unknown built-in tool: {tool_name}")
        return None

    def get_tool(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        Get a loaded tool by name.

        Args:
            tool_name: Name of the tool

        Returns:
            Tool definition dict, or None if not found
        """
        return self.tools_by_name.get(tool_name)

    def get_failed_tools(self) -> Dict[str, str]:
        """
        Get tools that failed to load.

        Returns:
            Dict mapping tool name to error message
        """
        return self.failed_tools.copy()
