"""Theme system for Opus terminal UI"""

from dataclasses import dataclass
from typing import Dict


@dataclass
class Theme:
    """Color theme for Opus UI"""
    name: str

    # Primary colors
    primary: str          # Main accent color
    secondary: str        # Secondary accent

    # Status colors
    success: str          # Success indicators
    warning: str          # Warnings
    error: str            # Errors
    info: str            # Information

    # Text colors
    text: str            # Normal text
    dim: str             # Dimmed/secondary text
    bold: str            # Emphasized text

    # Tool execution colors
    tool_name: str       # Tool name display
    tool_args: str       # Tool arguments
    tool_output: str     # Tool output text

    # UI elements
    spinner: str         # Thinking/loading spinner
    prompt: str          # User prompt (>:)
    border: str          # Borders and separators


# Built-in themes
THEMES: Dict[str, Theme] = {
    "default": Theme(
        name="Default",
        primary="cyan",
        secondary="blue",
        success="green",
        warning="yellow",
        error="red",
        info="cyan",
        text="white",
        dim="bright_black",
        bold="bold white",
        tool_name="bold cyan",
        tool_args="bright_black",
        tool_output="bright_black",
        spinner="cyan",
        prompt="bold cyan",
        border="bright_black",
    ),

    "dracula": Theme(
        name="Dracula",
        primary="#bd93f9",         # Purple
        secondary="#ff79c6",       # Pink
        success="#50fa7b",         # Green
        warning="#f1fa8c",         # Yellow
        error="#ff5555",           # Red
        info="#8be9fd",            # Cyan
        text="#f8f8f2",            # Foreground
        dim="#6272a4",             # Comment
        bold="bold #f8f8f2",
        tool_name="bold #bd93f9",
        tool_args="#6272a4",
        tool_output="#6272a4",
        spinner="#bd93f9",
        prompt="bold #ff79c6",
        border="#44475a",
    ),

}


def get_theme(theme_name: str = "default") -> Theme:
    """
    Get a theme by name.

    Args:
        theme_name: Name of the theme

    Returns:
        Theme object
    """
    return THEMES.get(theme_name.lower(), THEMES["default"])


def list_themes() -> list[str]:
    """
    Get list of available theme names.

    Returns:
        List of theme names
    """
    return list(THEMES.keys())
