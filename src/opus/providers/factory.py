"""Factory function for creating LLM provider instances"""

import logging
from typing import List, Dict

from opus.config import OpusConfig
from opus.providers.base import LLMProvider
from opus.providers.anthropic_provider import AnthropicProvider
from opus.providers.openai_provider import OpenAIProvider
from opus.providers.gemini_provider import GeminiProvider

logger = logging.getLogger(__name__)


def create_provider(
    config: OpusConfig,
    tools: List[Dict],
    system_prompt: str,
) -> LLMProvider:
    """
    Create an LLM provider instance.

    Args:
        config: Opus configuration
        tools: List of tool definitions
        system_prompt: System prompt for the agent

    Returns:
        Initialized LLM provider

    Raises:
        ValueError: If provider is not supported
    """
    provider_name = config.provider.lower()

    logger.info(f"Initializing {provider_name} provider with model {config.model}")

    if provider_name == "anthropic":
        return AnthropicProvider(config.model, tools, system_prompt)
    elif provider_name == "openai":
        return OpenAIProvider(config.model, tools, system_prompt)
    elif provider_name in ["gemini", "google"]:
        return GeminiProvider(config.model, tools, system_prompt)
    else:
        raise ValueError(
            f"Unsupported provider: {provider_name}. "
            f"Supported providers: anthropic, openai, gemini"
        )


# Backwards compatibility alias
class ProviderFactory:
    """Deprecated: Use create_provider() function instead"""
    @classmethod
    def create(cls, config: OpusConfig, tools: List[Dict], system_prompt: str) -> LLMProvider:
        return create_provider(config, tools, system_prompt)
