# Opus

Opus is an AI-powered automation agent for your terminal. It turns any script into an intelligent tool through simple configuration, letting you chain together complex workflows with natural language. Whether you're troubleshooting production incidents, executing runbooks, or managing tribal knowledge, Opus gives you the confidence to handle modern operational complexity.

**Key Features:**
- 🔧 **Turn any script into a tool** - Bash scripts, Python, or any executable
- 🤖 **Multi-LLM support** - Works with Anthropic Claude, OpenAI, and Google Gemini
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
provider: anthropic  # or openai, gemini
model: claude-sonnet-4-20250514

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

Set your API key:
```bash
export ANTHROPIC_API_KEY=your-key-here
# or OPENAI_API_KEY, GOOGLE_API_KEY
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

| Provider | Models | Configuration |
|----------|--------|---------------|
| **Anthropic** | Claude 3.5 Sonnet, Opus, Haiku | `provider: anthropic` |
| **OpenAI** | GPT-4, GPT-4 Turbo, GPT-3.5 | `provider: openai` |
| **Google** | Gemini 1.5 Pro, Flash | `provider: gemini` |

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
- [Anthropic Claude](https://www.anthropic.com/)
- [OpenAI](https://openai.com/)
- [Google Gemini](https://deepmind.google/technologies/gemini/)
- [Rich](https://rich.readthedocs.io/) for beautiful terminal output
