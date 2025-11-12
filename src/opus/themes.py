"""Professional dark theme for Opus terminal UI

Inspired by Claude Code, VS Code Dark+, and modern development tools.
Features carefully chosen colors for optimal readability and visual hierarchy.
"""

from dataclasses import dataclass


@dataclass
class Theme:
    """Professional color theme for Opus UI"""
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


# Single, carefully crafted professional dark theme
DEFAULT_THEME = Theme(
    name="Opus Dark",

    # Primary: Professional blue - not too bright, excellent contrast
    primary="#5B9BD5",           # Calm, professional blue
    secondary="#7AA3CC",         # Slightly muted blue

    # Status colors: Clear but not harsh
    success="#4EC9B0",           # Teal green - modern and clear
    warning="#D4A960",           # Warm amber - visible but not alarming
    error="#E06C75",             # Soft red - clear without being harsh
    info="#61AFEF",              # Light blue - informative

    # Text: High readability with good hierarchy
    text="#D4D4D4",              # Soft white - easy on eyes
    dim="#6B7280",               # Medium gray - clear hierarchy
    bold="bold #E5E7EB",         # Slightly brighter for emphasis

    # Tool execution: Subtle but clear
    tool_name="bold #61AFEF",    # Bright blue for tool names
    tool_args="#6B7280",         # Gray for args - not distracting
    tool_output="#9CA3AF",       # Lighter gray for output

    # UI elements: Clean and minimal
    spinner="#5B9BD5",           # Match primary
    prompt="bold #61AFEF",       # Inviting blue
    border="#374151",            # Subtle border - barely visible
)


def get_theme() -> Theme:
    """
    Get the Opus theme.

    Returns:
        Theme object
    """
    return DEFAULT_THEME
