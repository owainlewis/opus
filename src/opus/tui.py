"""Textual-based TUI for Opus - World-class terminal interface"""

import os
import time
import logging
from typing import Optional, Dict, TYPE_CHECKING

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical, Horizontal, VerticalScroll
from textual.widgets import Static, Input
from textual.reactive import reactive
from rich.text import Text
from rich.markdown import Markdown
from rich.panel import Panel
from rich.align import Align
from rich.box import ROUNDED
from rich.console import Group

if TYPE_CHECKING:
    from opus.agent import OpusAgent

logger = logging.getLogger(__name__)


class MessageDisplay(Static):
    """Widget for displaying a single message"""
    pass


class ThinkingIndicator(Static):
    """Animated thinking indicator"""

    _frame = reactive(0)
    _running = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._timer = None

    def on_mount(self) -> None:
        """Start animation when mounted"""
        self._running = True
        self._timer = self.set_interval(0.4, self._advance_frame)

    def on_unmount(self) -> None:
        """Stop animation when unmounted"""
        self._running = False
        if self._timer:
            self._timer.stop()

    def _advance_frame(self) -> None:
        """Advance to next animation frame"""
        if self._running:
            self._frame = (self._frame + 1) % 4

    def watch__frame(self, frame: int) -> None:
        """Update display when frame changes"""
        dots = "." * frame
        spaces = " " * (3 - frame)
        text = Text()
        text.append("⏺ ", style="#606060")
        text.append(f"thinking{dots}{spaces}", style="italic #505050")
        self.update(text)


class MessagesContainer(VerticalScroll):
    """Scrollable container for chat messages"""

    def compose(self) -> ComposeResult:
        yield Static(id="welcome-message")


class ModeIndicator(Static):
    """Shows the current approval mode"""

    mode = reactive("Auto")

    def render(self) -> Text:
        text = Text()
        if self.mode == "Auto":
            text.append("Auto (High)", style="bold #e6b450")
            text.append(" - allow all commands", style="#e6b450 dim")
        elif self.mode == "Approve":
            text.append("Approve", style="bold #5fd7ff")
            text.append(" - require approval", style="#5fd7ff dim")
        else:
            text.append("Manual", style="bold #888888")
            text.append(" - manual only", style="#666666")
        return text


class ModelIndicator(Static):
    """Shows the current model"""

    model_name = reactive("opus")

    def render(self) -> Text:
        return Text(self.model_name, style="bold #909090")


class PromptInput(Input):
    """Custom input with opus styling"""

    BINDINGS = [
        Binding("escape", "clear_input", "Clear"),
        Binding("up", "history_prev", "Previous", show=False),
        Binding("down", "history_next", "Next", show=False),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.history: list[str] = []
        self.history_index = -1

    def action_clear_input(self) -> None:
        self.value = ""

    def action_history_prev(self) -> None:
        if self.history and self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.value = self.history[-(self.history_index + 1)]

    def action_history_next(self) -> None:
        if self.history_index > 0:
            self.history_index -= 1
            self.value = self.history[-(self.history_index + 1)]
        elif self.history_index == 0:
            self.history_index = -1
            self.value = ""

    def add_to_history(self, value: str) -> None:
        if value and (not self.history or self.history[-1] != value):
            self.history.append(value)
        self.history_index = -1


class InputBar(Container):
    """Sticky input bar at the bottom"""

    def compose(self) -> ComposeResult:
        with Horizontal(id="mode-line"):
            yield ModeIndicator(id="mode-indicator")
            yield Static("shift+tab to cycle modes, tab to cycle reasoning", id="mode-hint")
            yield ModelIndicator(id="model-indicator")
        with Horizontal(id="input-line"):
            yield Static("› ", id="prompt-char")
            yield PromptInput(
                placeholder="Ask anything...",
                id="user-input"
            )
        yield Static("? for help", id="help-hint")


class OpusTUI(App):
    """Main Opus TUI Application"""

    CSS = """
    Screen {
        background: #0a0a0a;
    }

    #main-container {
        height: 100%;
        width: 100%;
    }

    #messages-area {
        height: 1fr;
        width: 100%;
        padding: 1 2;
        background: #0a0a0a;
    }

    #welcome-message {
        width: 100%;
        content-align: center middle;
    }

    .message {
        width: 100%;
        margin-bottom: 1;
    }

    .user-message {
        color: #f0f0f0;
        border-top: solid #1e1e1e;
        padding-top: 1;
        margin-top: 1;
    }

    .assistant-message {
        color: #d0d0d0;
        margin-top: 1;
    }

    .tool-message {
        border: solid #252525;
        padding: 0 1;
        margin: 0 0 1 0;
    }

    #input-bar {
        dock: bottom;
        height: auto;
        max-height: 8;
        width: 100%;
        background: #0a0a0a;
        padding: 0 1;
    }

    #mode-line {
        height: 1;
        width: 100%;
        margin-bottom: 0;
    }

    #mode-indicator {
        width: auto;
    }

    #mode-hint {
        width: 1fr;
        color: #4a4a4a;
        text-align: center;
    }

    #model-indicator {
        width: auto;
        text-align: right;
    }

    #input-line {
        height: 3;
        width: 100%;
        border: solid #252525;
        background: #101010;
        padding: 0 1;
    }

    #prompt-char {
        width: 2;
        height: 1;
        color: #707070;
        padding-top: 1;
    }

    #user-input {
        width: 1fr;
        height: 100%;
        border: none;
        background: transparent;
        color: #e8e8e8;
        padding: 0;
    }

    #user-input:focus {
        border: none;
    }

    Input>.input--placeholder {
        color: #505050;
    }

    #help-hint {
        height: 1;
        width: 100%;
        color: #3a3a3a;
        margin-top: 0;
    }

    .thinking-indicator {
        color: #505050;
        margin-top: 1;
    }

    .tool-call {
        color: #707070;
        margin-top: 1;
        padding: 0;
    }

    #user-input:disabled {
        color: #404040;
    }
    """

    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit"),
        Binding("ctrl+l", "clear_messages", "Clear"),
        Binding("escape", "focus_input", "Focus Input", show=False),
    ]

    def __init__(
        self,
        agent: Optional["OpusAgent"] = None,
        model: str = "opus",
        provider: str = "anthropic",
        **kwargs
    ):
        super().__init__(**kwargs)
        self.agent = agent
        self.model = model
        self.provider = provider
        self._message_count = 0
        self._processing = False
        self._tool_start_times: Dict[str, float] = {}  # Track tool execution times

    def compose(self) -> ComposeResult:
        with Vertical(id="main-container"):
            yield MessagesContainer(id="messages-area")
            yield InputBar(id="input-bar")

    def on_mount(self) -> None:
        """Called when the app is mounted"""
        self._show_welcome()
        self.query_one("#user-input", Input).focus()

        # Set model name
        model_indicator = self.query_one("#model-indicator", ModelIndicator)
        model_indicator.model_name = self.model

    def _show_welcome(self) -> None:
        """Show the welcome message"""
        welcome = self.query_one("#welcome-message", Static)

        # Create boxed header with logo and model
        header_text = Text()
        header_text.append("OPUS", style="bold #c0c0c0")
        header_text.append("  ", style="")
        header_text.append(self.model, style="#606060")

        header_panel = Panel(
            Align.center(header_text),
            box=ROUNDED,
            border_style="#303030",
            padding=(0, 2),
        )

        # Build the full welcome content
        content = Text()
        content.append("\n")

        # Tagline - subtle italic
        content.append("You are standing in an open terminal. An AI awaits your commands.\n\n", style="italic #505050")

        # Instructions - clean and minimal
        content.append("ENTER", style="#707070")
        content.append(" to send ", style="#383838")
        content.append("•", style="#252525")
        content.append(" ", style="#383838")
        content.append("\\", style="#707070")
        content.append(" + ", style="#383838")
        content.append("ENTER", style="#707070")
        content.append(" for a new line ", style="#383838")
        content.append("•", style="#252525")
        content.append(" ", style="#383838")
        content.append("@", style="#707070")
        content.append(" to mention files\n\n", style="#383838")

        # Current directory
        content.append("Current folder: ", style="#383838")
        content.append(os.getcwd(), style="#606060")

        # Combine panel and content
        welcome.update(Group(header_panel, Align.center(content)))

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission"""
        value = event.value.strip()
        if not value or self._processing:
            return

        # Add to history
        input_widget = self.query_one("#user-input", PromptInput)
        input_widget.add_to_history(value)
        input_widget.value = ""

        # Handle slash commands locally
        if value.startswith("/"):
            await self._handle_slash_command(value)
            return

        # Add user message to display
        self.add_user_message(value)

        # Process with agent if available
        if self.agent:
            self._processing = True
            input_widget.disabled = True

            # Connect UI to agent for tool display
            self.agent.ui = self

            try:
                # Show thinking indicator
                self.add_thinking_indicator()

                # Run agent chat
                response = await self.agent.chat(value)

                # Remove thinking indicator
                self.remove_thinking_indicator()

                # Display response
                if response:
                    self.add_assistant_message(response)

            except Exception as e:
                self.remove_thinking_indicator()
                logger.exception("Error in agent chat")
                self.add_system_message(f"Error: {e}")
            finally:
                self._processing = False
                input_widget.disabled = False
                input_widget.focus()

    async def _handle_slash_command(self, command: str) -> None:
        """Handle slash commands"""
        cmd = command.lower().strip()

        if cmd in ["/exit", "/quit", "/q"]:
            self.exit()
        elif cmd == "/clear":
            self.action_clear_messages()
            if self.agent:
                self.agent.messages.clear()
        elif cmd == "/help":
            self.add_system_message("""
**Commands:**
- `/help` - Show this help
- `/clear` - Clear messages and history
- `/tools` - List available tools
- `/exit` - Exit Opus
""")
        elif cmd == "/tools":
            if self.agent:
                tools_text = "**Available Tools:**\n"
                for tool in self.agent.tools:
                    name = tool["name"]
                    desc = tool.get("description", "")[:60]
                    tools_text += f"- `{name}` - {desc}...\n"
                self.add_system_message(tools_text)
            else:
                self.add_system_message("No agent connected")
        else:
            self.add_system_message(f"Unknown command: {command}")

    def action_quit(self) -> None:
        """Quit the application"""
        self.exit()

    def action_clear_messages(self) -> None:
        """Clear all messages"""
        messages_area = self.query_one("#messages-area", MessagesContainer)
        # Remove all message widgets except welcome
        for widget in list(messages_area.query(".message")):
            widget.remove()
        self._message_count = 0

    def action_focus_input(self) -> None:
        """Focus the input"""
        self.query_one("#user-input", Input).focus()

    def add_user_message(self, content: str) -> None:
        """Add a user message to the display"""
        self._message_count += 1
        messages_area = self.query_one("#messages-area", MessagesContainer)

        text = Text()
        text.append("› ", style="#606060")
        text.append(content, style="#d0d0d0")

        widget = MessageDisplay(text, classes="message user-message")
        messages_area.mount(widget)
        widget.scroll_visible()

    def add_assistant_message(self, content: str) -> None:
        """Add an assistant message to the display"""
        self._message_count += 1
        messages_area = self.query_one("#messages-area", MessagesContainer)

        # Prepend indicator to content
        prefixed_content = f"⏺ {content}"
        md = Markdown(prefixed_content)

        widget = MessageDisplay(md, classes="message assistant-message")
        messages_area.mount(widget)
        widget.scroll_visible()

    def add_system_message(self, content: str) -> None:
        """Add a system/info message"""
        self._message_count += 1
        messages_area = self.query_one("#messages-area", MessagesContainer)

        md = Markdown(content)
        widget = MessageDisplay(md, classes="message system-message")
        messages_area.mount(widget)
        widget.scroll_visible()

    def add_tool_message(self, tool_name: str, content: str) -> None:
        """Add a tool execution message"""
        self._message_count += 1
        messages_area = self.query_one("#messages-area", MessagesContainer)

        text = Text()
        text.append(f"› {tool_name}\n", style="#808080")
        text.append(content, style="#505050")

        widget = MessageDisplay(
            Panel(text, border_style="#252525", padding=(0, 1)),
            classes="message tool-message"
        )
        messages_area.mount(widget)
        widget.scroll_visible()

    def add_tool_call(self, tool_name: str, args: str, status: str = "running") -> None:
        """Add a tool call indicator to the display"""
        messages_area = self.query_one("#messages-area", MessagesContainer)

        # Remove thinking indicator if present
        self.remove_thinking_indicator()

        # Record start time
        tool_id = f"tool-{tool_name.replace('.', '-')}"
        self._tool_start_times[tool_id] = time.time()

        # Create tool display - Claude Code style
        text = Text()
        text.append("⏺ ", style="#e6b450")  # Amber while running
        text.append(tool_name, style="bold #909090")
        if args:
            text.append(f"({args})", style="#606060")
        text.append(" ...", style="italic #505050")

        widget = MessageDisplay(
            text,
            classes="message tool-call",
            id=tool_id
        )
        messages_area.mount(widget)
        widget.scroll_visible()

    def update_tool_status(self, tool_name: str, status: str, result: str = "") -> None:
        """Update the status of a tool call"""
        tool_id = f"tool-{tool_name.replace('.', '-')}"

        # Calculate elapsed time
        elapsed = ""
        if tool_id in self._tool_start_times:
            elapsed_secs = time.time() - self._tool_start_times[tool_id]
            if elapsed_secs >= 60:
                elapsed = f"{elapsed_secs/60:.1f}m"
            elif elapsed_secs >= 1:
                elapsed = f"{elapsed_secs:.1f}s"
            else:
                elapsed = f"{elapsed_secs*1000:.0f}ms"
            del self._tool_start_times[tool_id]

        try:
            widget = self.query_one(f"#{tool_id}", MessageDisplay)

            text = Text()
            if status == "done":
                text.append("⏺ ", style="#4a9a4a")  # Green when done
                text.append(tool_name, style="#707070")
                if elapsed:
                    text.append(f" ({elapsed})", style="#4a6a4a")
            elif status == "error":
                text.append("⏺ ", style="#9a4a4a")  # Red on error
                text.append(tool_name, style="#707070")
                if elapsed:
                    text.append(f" ({elapsed})", style="#6a4a4a")
                if result:
                    text.append(f" {result[:50]}", style="#6a4a4a")
            elif status == "rejected":
                text.append("⏺ ", style="#6a6a5a")  # Gray if rejected
                text.append(tool_name, style="#606060")
                text.append(" rejected", style="#5a5a4a")

            widget.update(text)
            widget.scroll_visible()

        except Exception:
            # Widget not found, ignore
            pass

    def set_mode(self, mode: str) -> None:
        """Set the approval mode"""
        self.query_one("#mode-indicator", ModeIndicator).mode = mode

    def add_thinking_indicator(self) -> None:
        """Add an animated thinking indicator"""
        messages_area = self.query_one("#messages-area", MessagesContainer)
        widget = ThinkingIndicator(classes="message thinking-indicator", id="thinking")
        messages_area.mount(widget)
        widget.scroll_visible()

    def remove_thinking_indicator(self) -> None:
        """Remove the thinking indicator"""
        try:
            thinking = self.query_one("#thinking", ThinkingIndicator)
            thinking.remove()
        except Exception:
            pass

    def update_streaming(self, content: str) -> None:
        """Update the last message with streaming content"""
        messages_area = self.query_one("#messages-area", MessagesContainer)
        messages = list(messages_area.query(".assistant-message"))

        if messages:
            last_message = messages[-1]
            md = Markdown(content)
            last_message.update(md)
            last_message.scroll_visible()


def run_tui(
    agent: Optional["OpusAgent"] = None,
    model: str = "opus",
    provider: str = "anthropic",
) -> None:
    """Run the Opus TUI"""
    app = OpusTUI(agent=agent, model=model, provider=provider)
    app.run()


# For testing
if __name__ == "__main__":
    run_tui(model="claude-3-opus", provider="anthropic")
