"""Professional dark theme for Opus terminal UI

This module provides backward compatibility by re-exporting
the Pydantic-based Theme from models.py.

Inspired by Claude Code, VS Code Dark+, and modern development tools.
Features carefully chosen colors for optimal readability and visual hierarchy.
"""

# Re-export Theme and related objects from models for backward compatibility
from opus.models import Theme, DEFAULT_THEME, get_theme

__all__ = ["Theme", "DEFAULT_THEME", "get_theme"]
