# Providers

Opus supports multiple LLM providers through both native integrations and a universal provider interface. Native providers give you access to advanced features like prompt caching and custom endpoints, while the universal provider lets you use any of 100+ LLM services.

## Native Providers

Native providers are built directly into Opus and support provider-specific features that aren't available through the universal interface.

### Anthropic

The Anthropic provider gives you access to Claude models with support for prompt caching, which can significantly reduce costs for repeated operations.

```yaml
provider: anthropic
model: claude-sonnet-4-20250514

# Optional settings
anthropic_api_key: ${ANTHROPIC_API_KEY}  # Or set via environment variable
anthropic_prompt_caching: true           # Enable prompt caching (default: true)
anthropic_max_tokens: 4096               # Maximum response length
```

Available models include `claude-sonnet-4-20250514`, `claude-3-5-sonnet-20241022`, and others. Check the Anthropic documentation for the latest model names.

Prompt caching works automatically for the system prompt and tool definitions. When you run multiple commands in a session, Opus reuses the cached context, which can reduce API costs by up to 90% for the cached portions.

Set your API key:
```bash
export ANTHROPIC_API_KEY=your-key-here
```

### OpenAI

The OpenAI provider supports both OpenAI's models and OpenAI-compatible APIs from other services. This means you can use the native OpenAI provider to access models from services like Kimi, DeepSeek, OpenRouter, Together AI, and others that implement the OpenAI API format.

```yaml
provider: openai
model: gpt-4.1-mini

# Optional settings
openai_api_key: ${OPENAI_API_KEY}       # Or set via environment variable
openai_api_type: chat_completions       # API type (default)
openai_max_tokens: 4096                  # Maximum response length
```

For OpenAI-compatible services, set a custom base URL:

```yaml
provider: openai
model: kimi-k2-thinking
openai_base_url: https://api.moonshot.cn/v1
openai_api_key: ${KIMI_API_KEY}
```

This works with any service that uses the OpenAI API format. Popular examples include:

**Kimi (Moonshot)** - Affordable reasoning models
```yaml
provider: openai
model: kimi-k2-thinking
openai_base_url: https://api.moonshot.cn/v1
openai_api_key: ${KIMI_API_KEY}
```

**DeepSeek** - Cost-effective Chinese models
```yaml
provider: openai
model: deepseek-chat
openai_base_url: https://api.deepseek.com/v1
openai_api_key: ${DEEPSEEK_API_KEY}
```

**OpenRouter** - Access to multiple providers
```yaml
provider: openai
model: anthropic/claude-3-5-sonnet
openai_base_url: https://openrouter.ai/api/v1
openai_api_key: ${OPENROUTER_API_KEY}
```

The OpenAI provider supports two API types. The default `chat_completions` type works with standard OpenAI models and most compatible services. The `responses` type is an advanced API that supports stateful conversations, but it's only available for certain OpenAI models.

### Oracle GenAI

The Oracle provider gives you access to models through Oracle's GenAI service, including Grok, Cohere Command R+, and Meta Llama.

```yaml
provider: oracle
model: xai.grok-4
```

Available models include:
- `xai.grok-4` - XAI's Grok model
- `cohere.command-r-plus` - Cohere's Command R+ model
- `meta.llama-3-1-405b-instruct` - Meta's Llama 3.1 405B model

Oracle GenAI uses OCI authentication, so you need to have the OCI CLI configured. See the [OCI SDK Configuration Guide](https://docs.oracle.com/en-us/iaas/Content/API/Concepts/sdkconfig.htm) for setup instructions.

## Universal Provider (LiteLLM)

The LiteLLM provider gives you access to over 100 LLM services through a single interface. This is useful when you want to use a provider that doesn't have native support, or when you're experimenting with different models.

```yaml
provider: litellm
model: gemini/gemini-2.5-flash
```

Some commonly used providers through LiteLLM:

**Google Gemini**
```yaml
provider: litellm
model: gemini/gemini-2.5-flash
```
Set `GOOGLE_API_KEY` environment variable.

**Azure OpenAI**
```yaml
provider: litellm
model: azure/gpt-4
```
Requires Azure-specific environment variables. See LiteLLM docs for details.

**Together AI**
```yaml
provider: litellm
model: together_ai/meta-llama/Llama-3-70b-chat-hf
```
Set `TOGETHERAI_API_KEY` environment variable.

**Groq**
```yaml
provider: litellm
model: groq/llama-3-70b-8192
```
Set `GROQ_API_KEY` environment variable.

LiteLLM supports many more providers. See the [LiteLLM documentation](https://docs.litellm.ai/docs/providers) for a complete list and configuration details.

## Choosing a Provider

Use a native provider when available. Native providers support advanced features and are generally more reliable than going through the universal interface.

For Anthropic Claude, use the native Anthropic provider to get prompt caching. This can significantly reduce costs for repeated operations.

For OpenAI models and OpenAI-compatible services (Kimi, DeepSeek, OpenRouter, etc.), use the native OpenAI provider. You can access different services by changing the base URL.

For Oracle GenAI models, use the native Oracle provider.

For everything else, use LiteLLM. This includes Google Gemini, Azure OpenAI, Together AI, Groq, and many other services.

## API Keys and Authentication

Most providers use API keys for authentication. Set these as environment variables:

```bash
# Anthropic
export ANTHROPIC_API_KEY=your-key-here

# OpenAI
export OPENAI_API_KEY=your-key-here

# Google (for LiteLLM)
export GOOGLE_API_KEY=your-key-here

# Kimi/Moonshot
export KIMI_API_KEY=your-key-here
```

You can also set API keys directly in the config file using environment variable syntax:

```yaml
anthropic_api_key: ${ANTHROPIC_API_KEY}
openai_api_key: ${OPENAI_API_KEY}
```

Oracle GenAI uses OCI authentication instead of API keys. Configure the OCI CLI following their documentation.

## Advanced Configuration

Each provider has specific settings you can configure. Here are the available options:

**Anthropic Settings**
- `anthropic_api_key` - API key (or use environment variable)
- `anthropic_prompt_caching` - Enable prompt caching (default: true)
- `anthropic_max_tokens` - Maximum response length (default: 4096)

**OpenAI Settings**
- `openai_api_key` - API key (or use environment variable)
- `openai_base_url` - Custom base URL for OpenAI-compatible APIs
- `openai_api_type` - API type: `chat_completions` or `responses` (default: `chat_completions`)
- `openai_max_tokens` - Maximum response length (default: 4096)

**General Settings** (apply to all providers)
- `max_iterations` - Maximum conversation turns (default: 25)
- `max_retry_attempts` - Retry attempts for failed operations (default: 2)
- `default_timeout` - Timeout for tool execution in seconds (default: 30)

## Example Configurations

See the `examples/` directory for complete configuration examples:

- `examples/config_anthropic.yaml` - Anthropic with prompt caching
- `examples/config_openai.yaml` - OpenAI with standard models
- `examples/config_kimi_k2.yaml` - Kimi K2 via Moonshot API
- `examples/config-sample.yaml` - General configuration template
