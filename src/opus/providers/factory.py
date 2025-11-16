"""Factory function for creating LLM provider instances"""

import logging
from typing import List, Dict

from opus.config import OpusConfig
from opus.providers.base import LLMProvider

logger = logging.getLogger(__name__)


def create_provider(
    config: OpusConfig,
    tools: List[Dict],
    system_prompt: str,
) -> LLMProvider:
    """
    Create an LLM provider instance based on configuration.

    Supports:
    - anthropic: Native Anthropic provider with prompt caching (recommended for Claude)
    - openai: Native OpenAI provider (recommended for GPT, OpenAI-compatible APIs)
    - oracle: Native Oracle GenAI provider (recommended for OCI GenAI)
    - litellm: Universal provider supporting 100+ LLM providers

    Args:
        config: Opus configuration with provider and model
        tools: List of tool definitions
        system_prompt: System prompt for the agent

    Returns:
        Initialized provider instance

    Raises:
        ValueError: If provider SDK is not installed
        ValueError: If provider is unknown
    """
    provider = config.provider.lower() if hasattr(config, 'provider') else 'litellm'

    if provider == 'anthropic':
        logger.info(f"Initializing Anthropic provider with model {config.model}")
        try:
            from opus.providers.anthropic_provider import AnthropicProvider
            return AnthropicProvider(config, tools, system_prompt)
        except ImportError:
            raise ImportError(
                "Anthropic SDK not installed. Install with: pip install opus[anthropic]"
            )

    elif provider == 'openai':
        logger.info(f"Initializing OpenAI provider with model {config.model}")
        try:
            from opus.providers.openai_provider import OpenAIProvider
            return OpenAIProvider(config, tools, system_prompt)
        except ImportError:
            raise ImportError(
                "OpenAI SDK not installed. Install with: pip install opus[openai]"
            )

    elif provider == 'oracle':
        logger.info(f"Initializing Oracle GenAI provider with model {config.model}")
        from opus.providers.oracle_provider import OracleProvider
        return OracleProvider(config.model, tools, system_prompt)

    elif provider == 'litellm':
        logger.info(f"Initializing LiteLLM provider with model {config.model}")
        try:
            from opus.providers.litellm_provider import LiteLLMProvider
            return LiteLLMProvider(config.model, tools, system_prompt)
        except ImportError:
            raise ImportError(
                "LiteLLM not installed. Install with: pip install opus[litellm]"
            )

    else:
        raise ValueError(
            f"Unknown provider: {provider}. "
            f"Supported providers: anthropic, openai, oracle, litellm"
        )


# Backwards compatibility alias
class ProviderFactory:
    """Deprecated: Use create_provider() function instead"""
    @classmethod
    def create(cls, config: OpusConfig, tools: List[Dict], system_prompt: str) -> LLMProvider:
        return create_provider(config, tools, system_prompt)
