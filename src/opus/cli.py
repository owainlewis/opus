"""CLI entry point for Opus"""

import asyncio
import logging
import sys
import os
from pathlib import Path
import click
from rich.prompt import Prompt
from rich.text import Text

from opus.agent import OpusAgent
from opus.console_helper import print_markdown, console, get_current_theme
from opus.ui import create_simple_ui
from opus.models import MODEL_ALIASES


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


async def handle_slash_command(command: str, agent: OpusAgent) -> bool:
    """
    Handle slash commands.

    Args:
        command: The command (including slash)
        agent: The agent instance

    Returns:
        True to continue, False to exit
    """
    command = command.strip()

    if command == "/help":
        help_text = """
# Commands

`/help`        Show this help
`/tools`       List available tools
`/model <name>` Switch LLM model mid-conversation
`/clear`       Clear conversation history
`/raw <cmd>`   Execute shell command directly
`/exit`        Exit Opus

Config: `~/.opus/config.yaml`

## Model Switching

Use `/model <name>` to switch the LLM model during a conversation.
You can use model aliases (e.g., `sonnet`, `4o`, `mini`) or full model names.

Examples:
- `/model sonnet`  - Switch to Claude Sonnet 4
- `/model 4o`      - Switch to GPT-4o
- `/model mini`    - Switch to GPT-4.1 Mini
"""
        print_markdown(help_text)
        return True

    elif command == "/clear":
        agent.messages.clear()
        console.print("[dim]Conversation history cleared[/dim]")
        return True

    elif command.startswith("/model"):
        # Handle model switching
        parts = command.split(maxsplit=1)
        if len(parts) < 2:
            console.print("[yellow]Usage: /model <model-name>[/yellow]")
            console.print("\n[dim]Available aliases:[/dim]")
            for alias, full_name in sorted(MODEL_ALIASES.items()):
                console.print(f"  [cyan]{alias:15}[/cyan] → {full_name}")
            console.print("\n[dim]Or use a full model name (e.g., gpt-4o)[/dim]")
            return True

        new_model = parts[1].strip()

        # Resolve alias if it exists
        resolved_model = MODEL_ALIASES.get(new_model, new_model)

        # Show what we're switching to
        if new_model != resolved_model:
            console.print(f"[dim]Resolving alias '{new_model}' → '{resolved_model}'[/dim]")

        console.print(f"[cyan]Switching to model:[/cyan] {resolved_model}")

        try:
            # Update config
            agent.config.model = resolved_model

            # Auto-detect and update provider if needed
            from opus.models.config import PROVIDER_PREFIXES
            for prefix, provider in PROVIDER_PREFIXES.items():
                if resolved_model.startswith(prefix):
                    if provider != agent.config.provider:
                        agent.config.provider = provider
                        console.print(f"[dim]Auto-detected provider: {provider}[/dim]")
                    break

            # Reinitialize LLM provider with new model
            from opus.providers.factory import ProviderFactory
            from opus.prompt import create_system_prompt

            system_prompt = create_system_prompt(
                tools=agent.tools,
                model=agent.config.model,
                provider=agent.config.provider
            )

            agent.llm = ProviderFactory.create(
                config=agent.config,
                tools=agent.tools,
                system_prompt=system_prompt,
            )

            console.print(f"[green]✓[/green] Model switched to [bold]{resolved_model}[/bold]")
            console.print("[dim]Conversation history preserved[/dim]")

        except Exception as e:
            console.print(f"[red]Error switching model: {e}[/red]")
            logging.exception("Model switch failed")

        return True

    elif command == "/tools":
        # Re-show tools list
        console.print()
        console.print(Text("Available Tools:", style="bold white"))
        console.print()
        for tool in agent.tools:
            name = tool["name"]
            desc = tool.get("description", "")
            needs_approval = agent.config.get_tool_config(name).approval

            tool_line = Text()
            tool_line.append(" ")
            if needs_approval:
                tool_line.append("● ", style="yellow")
            else:
                tool_line.append("● ", style="green")
            tool_line.append(f"{name.capitalize()}", style="bold cyan")
            tool_line.append(f" ({name})", style="dim cyan")
            if needs_approval:
                tool_line.append(" [approval required]", style="yellow")
            else:
                tool_line.append(" [auto]", style="green")

            console.print(tool_line)
            desc_line = Text()
            desc_line.append(f"   {desc}", style="dim")
            console.print(desc_line)
            console.print()

        # Show failed tools if any
        failed_tools = agent.tool_loader.get_failed_tools()
        if failed_tools:
            console.print(Text("Failed to Load:", style="bold yellow"))
            console.print()
            for name, error in failed_tools.items():
                tool_line = Text()
                tool_line.append(" ")
                tool_line.append("✗ ", style="red")
                tool_line.append(f"{name.capitalize()}", style="bold red")
                tool_line.append(f" ({name})", style="dim red")
                console.print(tool_line)
                desc_line = Text()
                desc_line.append(f"   {error}", style="dim red")
                console.print(desc_line)
                console.print()

        return True

    elif command.startswith("/raw "):
        # Execute raw command directly
        raw_cmd = command[5:].strip()
        if not raw_cmd:
            console.print("[yellow]Usage: /raw <command>[/yellow]")
            return True

        console.print(f"[dim]Executing: {raw_cmd}[/dim]")
        proc = await asyncio.create_subprocess_shell(
            raw_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=os.getcwd()
        )

        stdout, stderr = await proc.communicate()

        if stdout:
            console.print(stdout.decode())
        if stderr:
            console.print(f"[red]{stderr.decode()}[/red]")

        if proc.returncode != 0:
            console.print(f"[yellow]Exit code: {proc.returncode}[/yellow]")

        return True

    elif command in ["/exit", "/quit"]:
        return False

    else:
        console.print(f"[yellow]Unknown command: {command}[/yellow]")
        console.print("[dim]Type /help for available commands[/dim]")
        return True


async def repl(agent: OpusAgent):
    """
    Run the Read-Eval-Print Loop.

    Args:
        agent: The agent instance
    """
    # Show the beautiful startup UI
    ui = create_simple_ui(
        model=agent.config.model,
        provider=agent.config.provider,
        tools=agent.tools,
        failed_tools=agent.tool_loader.get_failed_tools()
    )

    while True:
        try:
            theme = get_current_theme()

            # Thin separator like in the reference
            console.rule(style=theme.border)
            console.print()

            # Get user input - minimal prompt (>:)
            user_input = Prompt.ask(f"[{theme.prompt}]>:[/{theme.prompt}]").strip()

            if not user_input:
                continue

            # Don't show user message here - it's already shown by the prompt
            # ui.show_user_message(user_input)

            # Handle slash commands
            if user_input.startswith("/"):
                should_continue = await handle_slash_command(user_input, agent)
                if not should_continue:
                    break
                continue

            # Process with agent
            response = await agent.chat(user_input)

            if response:
                ui.show_assistant_message(response)

        except KeyboardInterrupt:
            console.print("\n[dim]Use /exit to quit[/dim]")
            continue
        except EOFError:
            break
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            logging.exception("Error in REPL")

    console.print("[dim]Goodbye![/dim]")


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
            # Interactive mode: start REPL
            asyncio.run(repl(agent))

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
#   model: xai.grok-4           # Or use alias: grok
#   model: cohere.command-r-plus  # Or use alias: command-r
#   model: meta.llama-3-1-405b-instruct  # Or use alias: llama
#
# LiteLLM (supports 100+ providers, use provider: litellm):
#   model: gpt-4.1-mini                      # OpenAI (alias: mini)
#   model: gpt-4o                            # OpenAI (alias: 4o)
#   model: gemini/gemini-2.5-flash           # Google Gemini (alias: flash)
#   model: gemini/gemini-1.5-pro             # Google Gemini (alias: gemini)
#   model: anthropic/claude-sonnet-4-20250514  # Anthropic (alias: sonnet)
#   model: anthropic/claude-3-5-sonnet-20241022  # Anthropic (alias: sonnet-3.5)
#
# Model Aliases: You can use short aliases instead of full model names
# Example: Use 'sonnet' instead of 'anthropic/claude-sonnet-4-20250514'
# Use /model command to switch models during conversation (e.g., /model sonnet)

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
