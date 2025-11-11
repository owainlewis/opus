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

    "nord": Theme(
        name="Nord",
        primary="#88c0d0",         # Frost blue
        secondary="#81a1c1",       # Frost light blue
        success="#a3be8c",         # Green
        warning="#ebcb8b",         # Yellow
        error="#bf616a",           # Red
        info="#88c0d0",            # Cyan
        text="#eceff4",            # Snow white
        dim="#4c566a",             # Polar night
        bold="bold #eceff4",
        tool_name="bold #88c0d0",
        tool_args="#4c566a",
        tool_output="#4c566a",
        spinner="#88c0d0",
        prompt="bold #81a1c1",
        border="#3b4252",
    ),

    "tokyo-night": Theme(
        name="Tokyo Night",
        primary="#7aa2f7",         # Blue
        secondary="#bb9af7",       # Purple
        success="#9ece6a",         # Green
        warning="#e0af68",         # Yellow
        error="#f7768e",           # Red
        info="#7dcfff",            # Cyan
        text="#c0caf5",            # Foreground
        dim="#565f89",             # Comment
        bold="bold #c0caf5",
        tool_name="bold #7aa2f7",
        tool_args="#565f89",
        tool_output="#565f89",
        spinner="#7aa2f7",
        prompt="bold #bb9af7",
        border="#1a1b26",
    ),

    "gruvbox": Theme(
        name="Gruvbox Dark",
        primary="#83a598",         # Blue
        secondary="#d3869b",       # Purple
        success="#b8bb26",         # Green
        warning="#fabd2f",         # Yellow
        error="#fb4934",           # Red
        info="#8ec07c",            # Aqua
        text="#ebdbb2",            # Foreground
        dim="#928374",             # Gray
        bold="bold #ebdbb2",
        tool_name="bold #83a598",
        tool_args="#928374",
        tool_output="#928374",
        spinner="#83a598",
        prompt="bold #d3869b",
        border="#504945",
    ),

    "monokai": Theme(
        name="Monokai",
        primary="#66d9ef",         # Cyan
        secondary="#ae81ff",       # Purple
        success="#a6e22e",         # Green
        warning="#e6db74",         # Yellow
        error="#f92672",           # Pink/Red
        info="#66d9ef",            # Cyan
        text="#f8f8f2",            # Foreground
        dim="#75715e",             # Comment
        bold="bold #f8f8f2",
        tool_name="bold #66d9ef",
        tool_args="#75715e",
        tool_output="#75715e",
        spinner="#66d9ef",
        prompt="bold #ae81ff",
        border="#3e3d32",
    ),

    "catppuccin": Theme(
        name="Catppuccin Mocha",
        primary="#89b4fa",         # Blue
        secondary="#cba6f7",       # Mauve
        success="#a6e3a1",         # Green
        warning="#f9e2af",         # Yellow
        error="#f38ba8",           # Red
        info="#94e2d5",            # Teal
        text="#cdd6f4",            # Text
        dim="#6c7086",             # Overlay
        bold="bold #cdd6f4",
        tool_name="bold #89b4fa",
        tool_args="#6c7086",
        tool_output="#6c7086",
        spinner="#89b4fa",
        prompt="bold #cba6f7",
        border="#45475a",
    ),

    "synthwave": Theme(
        name="Synthwave '84",
        primary="#ff7edb",         # Hot pink
        secondary="#36f9f6",       # Cyan
        success="#72f1b8",         # Mint
        warning="#fede5d",         # Yellow
        error="#fe4450",           # Red
        info="#36f9f6",            # Cyan
        text="#ffffff",            # White
        dim="#848bbd",             # Purple gray
        bold="bold #ffffff",
        tool_name="bold #ff7edb",
        tool_args="#848bbd",
        tool_output="#848bbd",
        spinner="#36f9f6",
        prompt="bold #ff7edb",
        border="#262335",
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
