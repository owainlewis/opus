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
from opus.console_helper import print_markdown, console
from opus.ui import create_simple_ui


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

`/help`      Show this help
`/tools`     List available tools
`/clear`     Clear conversation history
`/raw <cmd>` Execute shell command directly
`/exit`      Exit Opus

Config: `~/.opus/config.yaml`
"""
        print_markdown(help_text)
        return True

    elif command == "/clear":
        agent.messages.clear()
        console.print("[dim]Conversation history cleared[/dim]")
        return True

    elif command == "/tools":
        # Re-show tools list
        console.print()
        console.print(Text("Available Tools:", style="bold white"))
        console.print()
        for tool in agent.tools:
            name = tool["name"]
            desc = tool.get("description", "")
            needs_approval = agent.config.get_tool_config(name).get("approval", False)

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
            # Thin separator like in the reference
            console.rule(style="dim")
            console.print()

            # Get user input - minimal prompt (>:)
            user_input = Prompt.ask("[bold cyan]>:[/bold cyan]").strip()

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
def main(ctx, config: str, verbose: bool, message: str):
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
        console.print(f"[red]Error: {e}[/red]")
        console.print("\n[yellow]To get started:[/yellow]")
        console.print(f"1. Create config directory: mkdir -p {opus_dir}")
        console.print(f"2. Create a config.yaml file at {opus_dir}/config.yaml")
        console.print("\n[dim]Example config.yaml:[/dim]")
        console.print("""
provider: anthropic
model: claude-sonnet-4-20250514

tools:
  bash:
    enabled: true
    approval: false
""")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Fatal error: {e}[/red]")
        logging.exception("Fatal error")
        sys.exit(1)


if __name__ == "__main__":
    main()
