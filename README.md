# Opus

Opus is an AI-powered automation agent for your terminal. It turns any script into an intelligent tool through simple configuration, letting you chain together complex workflows with natural language. Whether you're troubleshooting production incidents, executing runbooks, or managing tribal knowledge, Opus gives you the confidence to handle modern operational complexity.

**Key Features:**
- 🔧 **Turn any script into a tool** - Bash scripts, Python, or any executable
- 🤖 **Any LLM provider** - Native Oracle GenAI support + LiteLLM for Anthropic, OpenAI, Google Gemini, and more
- 🔒 **Enterprise-ready** - Per-tool approval settings, no vendor lock-in
- 📋 **Recipes (Runbooks)** - Interactive, reusable workflows
- 🎯 **Simple configuration** - YAML-based tool definitions

## Quick Start

### Installation

```bash
# Install as a uv tool (recommended - installs globally)
uv tool install opus

# Or install with uv pip
uv pip install opus

# Or with pip
pip install opus
```

Once installed, the `opus` command will be available in your terminal.

### Configuration

Create `~/.opus/config.yaml`:

```yaml
# LLM Provider Configuration
# Use "oracle" for Oracle GenAI, "litellm" (default) for other providers
provider: litellm
model: gpt-4.1-mini

# Oracle GenAI examples (use provider: oracle):
# provider: oracle
# model: xai.grok-4
# model: cohere.command-r-plus

# LiteLLM examples (use provider: litellm):
# model: gpt-4.1-mini                      # OpenAI
# model: gemini/gemini-2.5-flash           # Google
# model: anthropic/claude-sonnet-4-20250514  # Anthropic

tools:
  bash:
    enabled: true
    approval: true  # Require approval for bash commands

  file_read:
    enabled: true
    approval: false

  fetch_url:
    enabled: true
    approval: false
```

Set your API key (depends on provider):
```bash
# For OpenAI
export OPENAI_API_KEY=your-key-here

# For Google Gemini
export GOOGLE_API_KEY=your-key-here

# For Anthropic
export ANTHROPIC_API_KEY=your-key-here

# For Oracle GenAI (OCI CLI config required)
# See: https://docs.oracle.com/en-us/iaas/Content/API/Concepts/sdkconfig.htm
```

### Basic Usage

**Interactive mode:**
```bash
opus
```

**Single command:**
```bash
opus -m "Check disk usage on /var/log"
```

**Run with specific config:**
```bash
opus -c /path/to/config.yaml
```

## Creating Custom Tools

Opus lets you turn any script into an AI-accessible tool. Create a YAML file:

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
      enum: ["api", "worker", "frontend"]  # Helps LLM choose correctly
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

Add to your config:
```yaml
tools:
  deploy:
    enabled: true
    approval: true
    source: ./tools/deploy.yaml
```

See [examples/tools/](examples/tools/) for more examples.

## Recipes (Runbooks)

Recipes are interactive runbooks that guide you through multi-step workflows:

```bash
# List available recipes
opus recipe list

# Run a recipe
opus recipe run incident-triage \
  --params service=api \
  --params severity=P1
```

See [docs/RECIPES.md](docs/RECIPES.md) for full documentation.

## Supported LLM Providers

Opus supports two provider modes:

### Oracle GenAI (Native Provider)
For Oracle GenAI models, use `provider: oracle` for optimal performance:

```yaml
provider: oracle
model: xai.grok-4                    # XAI Grok
model: cohere.command-r-plus         # Cohere Command R+
model: meta.llama-3-1-405b-instruct  # Meta Llama 3.1
```

### LiteLLM (Universal Provider)
For all other providers, use `provider: litellm` (default):

| Provider | Example Models | Model String Format |
|----------|----------------|---------------------|
| **OpenAI** | GPT-4.1 Mini, GPT-4o | `gpt-4.1-mini`, `gpt-4o` |
| **Google Gemini** | Gemini 2.5 Flash, 1.5 Pro | `gemini/gemini-2.5-flash` |
| **Anthropic** | Claude Sonnet 4, Opus 4 | `anthropic/claude-sonnet-4-20250514` |

LiteLLM supports 100+ providers. See [LiteLLM docs](https://docs.litellm.ai/docs/providers) for the complete list.

## Tool Approval Modes

Control which tools require user approval:

```yaml
tools:
  bash:
    approval: true   # Always ask

  read:
    approval: false  # Auto-approve (safe operations)
```

## Project Structure

```
opus/
├── src/opus/           # Core agent code
├── examples/           # Example configs and tools
│   └── tools/          # Custom tool examples
├── docs/               # Documentation
└── recipes/            # Runbook examples
```

## Development

```bash
# Clone the repository
git clone https://github.com/owainlewis/opus.git
cd opus

# Install dependencies
uv sync

# Run in development mode
uv run opus
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

Contributions welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) first.

## Acknowledgments

Built with:
- [LiteLLM](https://docs.litellm.ai/) for universal LLM support
- [Rich](https://rich.readthedocs.io/) for beautiful terminal output

Supports models from:
- [Anthropic Claude](https://www.anthropic.com/)
- [OpenAI](https://openai.com/)
- [Google Gemini](https://deepmind.google/technologies/gemini/)
- [Oracle GenAI](https://www.oracle.com/artificial-intelligence/)
- And 100+ more providers
