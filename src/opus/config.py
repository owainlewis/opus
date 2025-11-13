"""
Configuration management for Opus

This module re-exports the Pydantic-based configuration models from opus.models.config
for backward compatibility.
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Re-export from the new Pydantic models
from opus.models.config import (
    OpusConfig,
    ToolConfig,
    BUILTIN_TOOLS,
    MODEL_ALIASES,
)

logger = logging.getLogger(__name__)

# For backward compatibility, expose the same interface
__all__ = [
    "OpusConfig",
    "ToolConfig",
    "BUILTIN_TOOLS",
    "MODEL_ALIASES",
]
