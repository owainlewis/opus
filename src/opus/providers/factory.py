"""Factory function for creating LLM provider instances"""

import logging
from typing import List, Dict

from opus.config import OpusConfig
from opus.providers.base import LLMProvider
from opus.providers.litellm_provider import LiteLLMProvider
from opus.providers.oracle_provider import OracleProvider

logger = logging.getLogger(__name__)


def create_provider(
    config: OpusConfig,
    tools: List[Dict],
    system_prompt: str,
) -> LLMProvider:
    """
    Create an LLM provider instance based on configuration.

    Supports:
    - oracle: Native Oracle GenAI provider (recommended for OCI GenAI)
    - litellm: Universal provider supporting 100+ LLM providers

    Args:
        config: Opus configuration with provider and model
        tools: List of tool definitions
        system_prompt: System prompt for the agent

    Returns:
        Initialized provider instance

    Note:
        For Oracle GenAI, use provider: oracle instead of litellm
        to avoid dependency issues and get better native support.
    """
    provider = config.provider.lower() if hasattr(config, 'provider') else 'litellm'

    if provider == 'oracle':
        logger.info(f"Initializing Oracle GenAI provider with model {config.model}")
        return OracleProvider(config.model, tools, system_prompt)
    else:
        logger.info(f"Initializing LiteLLM provider with model {config.model}")
        return LiteLLMProvider(config.model, tools, system_prompt)


# Backwards compatibility alias
class ProviderFactory:
    """Deprecated: Use create_provider() function instead"""
    @classmethod
    def create(cls, config: OpusConfig, tools: List[Dict], system_prompt: str) -> LLMProvider:
        return create_provider(config, tools, system_prompt)
