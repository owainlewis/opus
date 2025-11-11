"""Console helper utilities for rich terminal output"""

import asyncio
import time
from typing import Dict, Any
from rich.console import Console
from rich.live import Live
from rich.text import Text
from rich.markdown import Markdown

console = Console()

# Spinner animation frames
SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]


def print_tool_call(tool_name: str, tool_args: Dict[str, Any], needs_approval: bool = False):
    """
    Print a tool call to the console.

    Args:
        tool_name: Name of the tool being called
        tool_args: Arguments passed to the tool
        needs_approval: Whether the tool needs user approval
    """
    text = Text()

    # Green dot for tool calls
    if needs_approval:
        text.append("● ", style="yellow")
    else:
        text.append("● ", style="green")

    # Tool name in cyan bold
    text.append(f"{tool_name.capitalize()}", style="bold cyan")

    # Print args if present
    if tool_args:
        args_str = ", ".join([f"{k}={repr(v)[:50]}" for k, v in tool_args.items()])
        if len(args_str) > 80:
            args_str = args_str[:77] + "..."
        text.append(f"({args_str})", style="dim")

    console.print(text)


def print_tool_result(result: Any, max_lines: int = 5):
    """
    Print a tool execution result with truncation for long output.

    Args:
        result: Tool execution result
        max_lines: Maximum number of output lines to display (default: 5)
    """
    # Show the actual output from the tool
    if isinstance(result, dict) and "output" in result:
        output = result["output"]
        if output and output.strip():
            lines = output.strip().split('\n')

            # Show truncated output
            console.print(Text("  Output:", style="dim"))

            # Show first max_lines
            display_lines = lines[:max_lines]
            for line in display_lines:
                # Truncate very long lines
                if len(line) > 100:
                    line = line[:97] + "..."
                console.print(Text(f"    {line}", style="dim"))

            # Show truncation message if needed
            if len(lines) > max_lines:
                remaining = len(lines) - max_lines
                console.print(Text(f"    ... ({remaining} more lines)", style="dim italic"))

    # Show completion
    text = Text()
    text.append("  ⎿ Done", style="green dim")
    console.print(text)
    console.print()  # Add spacing after tool execution


def print_tool_error(error: str, will_retry: bool = False):
    """
    Print a tool execution error.

    Args:
        error: Error message
        will_retry: Whether the tool will be retried
    """
    if will_retry:
        console.print("  [dim]⎿[/dim] [yellow]⚠ Error (will retry)[/yellow]")
    else:
        console.print("  [dim]⎿[/dim] [red]✗ Error[/red]")

    # Display the actual error message
    if error:
        # Split error into lines and display with indentation
        error_lines = error.strip().split('\n')
        for line in error_lines[:10]:  # Limit to first 10 lines
            # Truncate very long lines
            if len(line) > 120:
                line = line[:117] + "..."
            console.print(Text(f"    {line}", style="dim red"))

        if len(error_lines) > 10:
            console.print(Text(f"    ... ({len(error_lines) - 10} more lines)", style="dim italic red"))


class ToolExecutionStatus:
    """
    Context manager for showing tool execution status with progress indicator.

    Shows progress after a delay to avoid flashing for quick operations.
    """

    def __init__(self, tool_name: str, tool_args: Dict[str, Any], delay: float = 2.0):
        """
        Initialize status indicator.

        Args:
            tool_name: Name of the tool
            tool_args: Tool arguments
            delay: Delay in seconds before showing progress
        """
        self.tool_name = tool_name
        self.tool_args = tool_args
        self.delay = delay
        self.start_time = None
        self.live = None
        self.update_task = None
        self.running = False
        self.show_progress = False

    async def _update_status(self):
        """Background task to update elapsed time"""
        # Wait for delay before showing progress
        await asyncio.sleep(self.delay)

        if not self.running:
            return

        self.show_progress = True

        # Start the live display
        idx = 0

        self.live = Live(
            Text("", style="dim cyan"),
            console=console,
            refresh_per_second=10
        )
        self.live.start()

        while self.running:
            elapsed = int(time.time() - self.start_time)
            spinner = SPINNER_FRAMES[idx % len(SPINNER_FRAMES)]
            message = Text(f"  {spinner} Executing… {elapsed}s", style="dim cyan")
            self.live.update(message)
            idx += 1
            await asyncio.sleep(0.1)

    async def __aenter__(self):
        self.start_time = time.time()
        self.running = True
        self.update_task = asyncio.create_task(self._update_status())
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.running = False

        if self.update_task:
            self.update_task.cancel()
            try:
                await self.update_task
            except asyncio.CancelledError:
                pass

        if self.live:
            self.live.stop()

        return False


class ThinkingStatus:
    """Context manager for showing LLM thinking status with elapsed time"""

    def __init__(self):
        self.start_time = None
        self.live = None
        self.update_task = None
        self.running = False

    async def _update_status(self):
        """Background task to update elapsed time"""
        idx = 0
        while self.running:
            elapsed = int(time.time() - self.start_time)
            spinner = SPINNER_FRAMES[idx % len(SPINNER_FRAMES)]
            message = Text(f"{spinner} Thinking… {elapsed}s", style="dim cyan")
            self.live.update(message)
            idx += 1
            await asyncio.sleep(0.1)

    async def __aenter__(self):
        self.start_time = time.time()
        self.running = True
        self.live = Live(Text("⠋ Thinking… 0s", style="dim cyan"), console=console, refresh_per_second=10)
        self.live.start()
        self.update_task = asyncio.create_task(self._update_status())
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.running = False
        if self.update_task:
            self.update_task.cancel()
            try:
                await self.update_task
            except asyncio.CancelledError:
                pass
        if self.live:
            self.live.stop()
        return False


def print_welcome_message():
    """Print welcome message on startup"""
    console.print("[bold cyan]Opus[/bold cyan] [dim]v0.1.0[/dim]")
    console.print("[dim]Type /help for commands or just start chatting[/dim]\n")


def print_markdown(text: str):
    """
    Print markdown formatted text.

    Args:
        text: Markdown text to print
    """
    md = Markdown(text)
    console.print(md)
