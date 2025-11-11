# Opus

Opus is an AI-powered automation agent for your terminal. It turns any script into an intelligent tool through simple configuration, letting you chain together complex workflows with natural language. Whether you're troubleshooting production incidents, executing runbooks, or managing tribal knowledge, Opus gives you the confidence to handle modern operational complexity.

**Key Features:**
- 🔧 **Turn any script into a tool** - Bash scripts, Python, or any executable
- 🤖 **100+ LLM providers** - Powered by LiteLLM supporting Anthropic, OpenAI, Gemini, AWS Bedrock, Azure, Oracle GenAI, and more
- 🔒 **Enterprise-ready** - Per-tool approval settings, no vendor lock-in
- 📋 **Recipes (Runbooks)** - Interactive, reusable workflows
- 🎯 **Simple configuration** - YAML-based tool definitions

## Quick Start

### Installation

```bash
# Install with uv (recommended)
uv pip install opus-agent

# Or with pip
pip install opus-agent
```

### Configuration

Create `~/.opus/config.yaml`:

```yaml
# Opus uses LiteLLM for universal LLM support
provider: anthropic
model: anthropic/claude-sonnet-4-20250514

# Other provider examples:
# - OpenAI: gpt-4.1-mini
# - Gemini: gemini/gemini-2.5-flash
# - AWS Bedrock: bedrock/anthropic.claude-v2
# - Azure: azure/your-deployment-name
# - Oracle GenAI: oci/cohere.command-r-plus

tools:
  bash:
    enabled: true
    approval: true  # Require approval for bash commands

  read:
    enabled: true
    approval: false

  fetch:
    enabled: true
    approval: false
```

Set your API key (depends on provider):
```bash
export ANTHROPIC_API_KEY=your-key-here
# or OPENAI_API_KEY, GOOGLE_API_KEY, AWS_ACCESS_KEY_ID, etc.
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

Opus uses [LiteLLM](https://docs.litellm.ai/docs/providers) to support 100+ LLM providers. Here are some popular options:

| Provider | Example Models | Model String Format |
|----------|----------------|---------------------|
| **Anthropic** | Claude 3.5 Sonnet, Opus 4 | `anthropic/claude-sonnet-4-20250514` |
| **OpenAI** | GPT-4.1 Mini, GPT-4o | `gpt-4.1-mini` (prefix optional) |
| **Google Gemini** | Gemini 2.5 Flash, 1.5 Pro | `gemini/gemini-2.5-flash` |
| **AWS Bedrock** | Claude, Titan, Llama | `bedrock/anthropic.claude-v2` |
| **Azure OpenAI** | GPT-4, GPT-3.5 | `azure/your-deployment-name` |
| **Oracle GenAI** | Command R+, Llama | `oci/cohere.command-r-plus` |
| **Cohere** | Command R+, Command | `command-r-plus` |

See [LiteLLM docs](https://docs.litellm.ai/docs/providers) for the complete list of supported providers.

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
git clone https://github.com/yourusername/opus.git
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
