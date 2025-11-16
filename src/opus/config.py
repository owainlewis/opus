"""Configuration management for Opus

This module provides backward compatibility by re-exporting
the Pydantic-based OpusConfig from models.py.
"""

# Re-export OpusConfig and BUILTIN_TOOLS from models for backward compatibility
from opus.models import OpusConfig, BUILTIN_TOOLS

__all__ = ["OpusConfig", "BUILTIN_TOOLS"]
