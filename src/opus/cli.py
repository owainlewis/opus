"""CLI entry point for Opus"""

import asyncio
import logging
import sys
from pathlib import Path
import click
from rich.prompt import Prompt

from opus.agent import OpusAgent
from opus.console_helper import print_markdown, console
from opus.tui import run_tui


def setup_logging(verbose: bool = False):
    """
    Setup logging configuration.

    Args:
        verbose: Enable verbose logging
    """
    level = logging.DEBUG if verbose else logging.INFO

    # Ensure .opus directory exists
    opus_dir = Path.home() / ".opus"
    opus_dir.mkdir(exist_ok=True)

    log_file = opus_dir / "opus.log"

    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file),
        ]
    )

    # Suppress LiteLLM's noisy INFO logs
    logging.getLogger("LiteLLM").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


def start_tui(agent: OpusAgent):
    """
    Start the TUI with the agent.

    Args:
        agent: The agent instance
    """
    run_tui(
        agent=agent,
        model=agent.config.model,
        provider=agent.config.provider,
    )


@click.group(invoke_without_command=True)
@click.pass_context
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True),
    help="Path to config.yaml file (default: ~/.opus/config.yaml)"
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose output"
)
@click.option(
    "--message",
    "-m",
    help="Send a single message and exit (non-interactive mode)"
)
def cli(ctx, config: str, verbose: bool, message: str):
    """
    Opus - Terminal-based AI agent for software engineering automation
    """
    # If no subcommand, run the agent REPL
    if ctx.invoked_subcommand is not None:
        return
    # Setup logging
    setup_logging(verbose)

    # Create .opus directory if it doesn't exist
    opus_dir = Path.home() / ".opus"
    opus_dir.mkdir(exist_ok=True)

    try:
        # Initialize agent
        agent = OpusAgent(config_path=config)

        if message:
            # Non-interactive mode: send single message
            async def run_once():
                response = await agent.chat(message)
                if response:
                    print_markdown(response)

            asyncio.run(run_once())
        else:
            # Interactive mode: start TUI
            start_tui(agent)

    except FileNotFoundError as e:
        console.print(f"[red]Error: Configuration file not found[/red]")
        console.print(f"\n[yellow]Run the following command to set up Opus:[/yellow]")
        console.print(f"  [cyan]opus init[/cyan]")
        console.print(f"\n[dim]Or manually create a config file at: {opus_dir}/config.yaml[/dim]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Fatal error: {e}[/red]")
        logging.exception("Fatal error")
        sys.exit(1)


@cli.command()
def init():
    """Initialize Opus configuration interactively"""
    opus_dir = Path.home() / ".opus"
    config_path = opus_dir / "config.yaml"

    # Check if config already exists
    if config_path.exists():
        console.print(f"[yellow]Config file already exists at {config_path}[/yellow]")
        overwrite = Prompt.ask(
            "Do you want to overwrite it?",
            choices=["y", "n"],
            default="n"
        )
        if overwrite.lower() != "y":
            console.print("[dim]Keeping existing configuration.[/dim]")
            return

    console.print("\n[bold cyan]Welcome to Opus![/bold cyan]")
    console.print("[dim]Let's set up your configuration...[/dim]\n")

    # Model selection
    console.print("[bold]Select your LLM model:[/bold]")
    console.print("[dim]Opus supports Oracle GenAI and 100+ providers via LiteLLM[/dim]\n")

    console.print("  [cyan]1.[/cyan] gpt-4.1-mini (OpenAI, recommended)")
    console.print("  [cyan]2.[/cyan] gemini/gemini-2.5-flash (Google)")
    console.print("  [cyan]3.[/cyan] anthropic/claude-sonnet-4-20250514 (Anthropic)")
    console.print("  [cyan]4.[/cyan] xai.grok-4 (Oracle GenAI)")
    console.print("  [cyan]5.[/cyan] Custom model (enter manually)")
    console.print()

    model_choice = Prompt.ask(
        "Model",
        choices=["1", "2", "3", "4", "5"],
        default="1"
    )

    model_map = {
        "1": "gpt-4.1-mini",
        "2": "gemini/gemini-2.5-flash",
        "3": "anthropic/claude-sonnet-4-20250514",
        "4": "xai.grok-4",
    }

    if model_choice == "5":
        console.print("\n[dim]Examples:[/dim]")
        console.print("[dim]  - gpt-4.1-mini (OpenAI)[/dim]")
        console.print("[dim]  - gemini/gemini-2.5-flash (Google)[/dim]")
        console.print("[dim]  - anthropic/claude-3-5-sonnet-20241022 (Anthropic)[/dim]")
        console.print("[dim]  - xai.grok-4 (Oracle GenAI)[/dim]")
        console.print()
        model = Prompt.ask("Enter model name")
    else:
        model = model_map[model_choice]

    # Determine provider based on model
    # Oracle GenAI models use native oracle provider, everything else uses litellm
    if model.startswith("xai.") or model.startswith("cohere.") or model.startswith("meta."):
        provider = "oracle"
    elif "/" in model:
        provider = "litellm"
    else:
        provider = "litellm"  # Default to litellm for models without prefix

    # Create config directory
    opus_dir.mkdir(exist_ok=True)

    # Generate config content
    config_content = f"""# Opus Configuration
# Generated by: opus init

# LLM Provider Configuration
# Use "oracle" for Oracle GenAI models, or "litellm" (default) for other providers
provider: {provider}
model: {model}

# Supported configurations:
# Oracle GenAI (requires provider: oracle):
#   provider: oracle
#   model: xai.grok-4
#   model: cohere.command-r-plus
#   model: meta.llama-3-1-405b-instruct
#
# LiteLLM (supports 100+ providers, use provider: litellm):
#   model: gpt-4.1-mini                      # OpenAI
#   model: gpt-4o                            # OpenAI
#   model: gemini/gemini-2.5-flash           # Google Gemini
#   model: gemini/gemini-1.5-pro             # Google Gemini
#   model: anthropic/claude-sonnet-4-20250514  # Anthropic
#   model: anthropic/claude-3-5-sonnet-20241022  # Anthropic

# Agent Behavior
max_iterations: 25  # Maximum conversation turns per request
default_timeout: 30  # Default timeout for tool execution (seconds)

# Tools Configuration
tools:
  # Built-in tools
  bash:
    enabled: true
    approval: true  # Require user approval before running bash commands

  read:
    enabled: true
    approval: false  # Read operations don't need approval

  fetch:
    enabled: true
    approval: false  # Web fetch doesn't need approval
"""

    # Write config file
    with open(config_path, "w") as f:
        f.write(config_content)

    console.print(f"\n[green]✓[/green] Configuration created at [cyan]{config_path}[/cyan]")
    console.print(f"\n[dim]Provider:[/dim] {provider}")
    console.print(f"[dim]Model:[/dim] {model}")
    console.print(f"\n[bold green]Ready to go![/bold green] Run [cyan]opus[/cyan] to start.\n")


# Alias for backwards compatibility
main = cli


if __name__ == "__main__":
    cli()
