# Opus

Opus is an AI-powered automation agent for your terminal. It turns any script into an intelligent tool through simple configuration, letting you chain together complex workflows with natural language.

**Key Features:**
- Turn any script into a tool that AI can use (Bash, Python, or any executable)
- Native support for Anthropic Claude, OpenAI, Oracle GenAI, plus 100+ providers via LiteLLM
- Per-tool approval settings for safe automation
- Recipes for reusable workflows and runbooks
- Simple YAML configuration

## Installation

```bash
# Install with uv (recommended)
uv tool install opus

# Or with pip
pip install opus
```

Once installed, the `opus` command will be available in your terminal.

## Quick Start

Create a config file at `~/.opus/config.yaml`:

```yaml
# Choose your provider and model
provider: anthropic
model: claude-sonnet-4-20250514

# Built-in tools are enabled by default
# You can configure approval settings
tools:
  bash:
    approval: true  # Require approval for bash commands
```

Set your API key:

```bash
export ANTHROPIC_API_KEY=your-key-here
```

Run Opus:

```bash
# Interactive mode
opus

# Single command
opus -m "Check disk usage on /var/log"

# Use specific config
opus -c /path/to/config.yaml
```

## Providers

Opus has native support for several providers, which gives you access to advanced features like prompt caching and custom endpoints.

**Anthropic** (recommended for most use cases)
```yaml
provider: anthropic
model: claude-sonnet-4-20250514
```

Anthropic's native provider includes prompt caching, which can significantly reduce costs for repeated operations.

**OpenAI**
```yaml
provider: openai
model: gpt-4.1-mini
```

The OpenAI provider supports both standard models and OpenAI-compatible APIs. You can use services like Kimi, DeepSeek, or OpenRouter by setting a custom base URL:

```yaml
provider: openai
model: kimi-k2-thinking
openai_base_url: https://api.moonshot.cn/v1
openai_api_key: ${KIMI_API_KEY}
```

**Oracle GenAI**
```yaml
provider: oracle
model: xai.grok-4
```

Oracle's provider gives you access to models like Grok, Cohere Command R+, and Meta Llama through Oracle's GenAI service.

**LiteLLM (100+ providers)**
```yaml
provider: litellm
model: gemini/gemini-2.5-flash
```

LiteLLM supports over 100 providers including Google Gemini, Azure OpenAI, Together AI, Groq, and many others. See the [LiteLLM docs](https://docs.litellm.ai/docs/providers) for the complete list.

For more details on providers and their features, see [docs/PROVIDERS.md](docs/PROVIDERS.md).

## Creating Custom Tools

You can turn any script into a tool that Opus can use. Create a YAML file that describes your tool:

```yaml
# tools/deploy.yaml
name: deploy_service
description: Deploy a service to production

script: ./deploy.sh {service} {environment}

parameters:
  type: object
  properties:
    service:
      type: string
      enum: ["api", "worker", "frontend"]
      description: Service to deploy
    environment:
      type: string
      enum: ["staging", "production"]
      description: Target environment
  required:
    - service
    - environment

timeout: 300
```

Reference your custom tool in the config:

```yaml
tools:
  deploy_service:
    enabled: true
    approval: true
    source: ./tools/deploy.yaml
```

See [docs/TOOLS.md](docs/TOOLS.md) for more information on creating custom tools.

## Recipes

Recipes are reusable prompt templates for specialized tasks. They package expertise and best practices into a format that Opus can use to handle complex workflows.

```bash
opus -m "Review src/app.py using the python-code-review recipe"
```

You can create your own recipes to capture domain knowledge, standard procedures, or common tasks. See [docs/RECIPES.md](docs/RECIPES.md) for details.

## Built-in Tools

Opus comes with several built-in tools that are always available:

- `bash` - Execute shell commands
- `file_read` - Read files from disk
- `file_write` - Create or overwrite files
- `file_edit` - Edit existing files
- `fetch_url` - Fetch content from URLs
- `run_recipe` - Execute recipes
- `get_current_time` - Get current date and time
- `run_subagents` - Spawn parallel agents for independent tasks

All built-in tools are enabled by default. You can disable them or configure approval settings in your config file.

## Example Configs

The `examples/` directory contains complete configuration examples:

- `examples/config_anthropic.yaml` - Anthropic with prompt caching
- `examples/config_openai.yaml` - OpenAI with standard models
- `examples/config_kimi_k2.yaml` - Kimi K2 via Moonshot API
- `examples/config-sample.yaml` - General configuration template

## Development

```bash
git clone https://github.com/owainlewis/opus.git
cd opus
uv sync
uv run opus
```

## License

MIT License - see [LICENSE](LICENSE) for details.
