"""Ultra-minimal, elegant terminal UI for Opus"""

import os
from typing import List, Dict
from rich.text import Text
from rich.markdown import Markdown
from rich.panel import Panel

from opus.console_helper import console

# Version from pyproject.toml
__version__ = "0.1.0"


class OpusUI:
    """
    Ultra-minimal terminal UI for Opus.

    Matches the elegant spacing and layout from the reference design.
    """

    def __init__(self, model: str, provider: str, tools: List[Dict], failed_tools: Dict[str, str] = None):
        self.model = model
        self.provider = provider
        self.tools = tools
        self.failed_tools = failed_tools or {}

    def show_startup_screen(self):
        """Display the minimal startup screen"""
        console.clear()

        # Create welcome content with banner
        welcome_text = Text()

        # Banner - plain text
        welcome_text.append("OPUS\n", style="bold magenta")
        welcome_text.append(f"Version: {__version__}\n\n", style="dim")

        # Info
        welcome_text.append("Model: ", style="dim")
        welcome_text.append(f"{self.provider} · {self.model}\n", style="white")
        welcome_text.append("Directory: ", style="dim")
        welcome_text.append(f"{os.getcwd()}\n\n", style="white")
        welcome_text.append("Type your message or ", style="dim")
        welcome_text.append("/help", style="cyan")
        welcome_text.append(" for commands · ", style="dim")
        welcome_text.append("/exit", style="cyan")
        welcome_text.append(" to quit", style="dim")

        # Create panel with border that spans terminal width
        panel = Panel(
            welcome_text,
            border_style="magenta",
            padding=(1, 2),
            expand=True
        )

        console.print(panel)
        console.print()

        # Show warnings for failed tools
        if self.failed_tools:
            console.print(f"[yellow]⚠ Warning: {len(self.failed_tools)} tool(s) failed to load:[/yellow]")
            for tool_name, error_msg in self.failed_tools.items():
                console.print(f"  [yellow]•[/yellow] [bold]{tool_name}[/bold]: [dim]{error_msg}[/dim]")
            console.print()

    def show_assistant_message(self, message: str):
        """Display assistant message with markdown"""
        if message.strip():
            console.print(Markdown(message))
            console.print()


def create_simple_ui(model: str, provider: str, tools: List[Dict], failed_tools: Dict[str, str] = None) -> OpusUI:
    """
    Create and display the Opus UI.

    Args:
        model: Model name
        provider: Provider name
        tools: Available tools
        failed_tools: Dict of tools that failed to load (name -> error message)

    Returns:
        OpusUI instance
    """
    ui = OpusUI(model, provider, tools, failed_tools)
    ui.show_startup_screen()
    return ui
