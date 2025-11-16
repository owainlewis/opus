"""Core agent orchestrator"""

import asyncio
import logging
from typing import Dict, List, Any
from rich.console import Console
from rich.prompt import Prompt

from opus.config import OpusConfig
from opus.providers.factory import ProviderFactory
from opus.tools.loader import ToolLoader
from opus.tools.executor import ToolExecutor
from opus.error_recovery import ToolExecutionTracker, ToolError
from opus.prompt import create_system_prompt
from opus.console_helper import (
    print_tool_call,
    print_tool_result,
    print_tool_error,
    ToolExecutionStatus,
    ThinkingStatus,
)

logger = logging.getLogger(__name__)
console = Console()


class OpusAgent:
    """
    Main agent orchestrator.

    Manages:
    - Conversation loop with LLM
    - Tool execution coordination
    - Message history
    - Configuration
    """

    def __init__(
        self,
        config_path: str = None,
        is_subagent: bool = False,
        initial_messages: List[Dict[str, str]] = None
    ):
        """
        Initialize the agent with configuration.

        Args:
            config_path: Path to config.yaml file (None = use default)
            is_subagent: Whether this is a sub-agent (prevents recursive sub-agent spawning)
            initial_messages: Optional initial message history (for sub-agents with context)
        """
        self.config = OpusConfig.from_yaml(config_path)
        self.is_subagent = is_subagent
        self.messages = []

        # Initialize tool executor with default timeout
        self.executor = ToolExecutor(timeout=self.config.default_timeout)

        # Initialize error recovery tracker
        self.execution_tracker = ToolExecutionTracker(max_attempts=self.config.max_retry_attempts)

        # Load tools from enabled tools
        self.tool_loader = ToolLoader()
        enabled_tools = self.config.get_enabled_tools()
        self.tools = self.tool_loader.load_tools(
            config=self.config,
            enabled_tools=enabled_tools
        )

        # If this is a sub-agent, filter out run_subagents to prevent recursion
        if is_subagent and "run_subagents" in self.tools:
            logger.info("Sub-agent: filtering out run_subagents tool to prevent recursion")
            self.tools = {k: v for k, v in self.tools.items() if k != "run_subagents"}

        logger.info(f"Loaded {len(self.tools)} tools")

        # Add initial messages if provided (for sub-agents with context)
        if initial_messages:
            self.messages.extend(initial_messages)
            logger.info(f"Initialized with {len(initial_messages)} initial messages")

        # Build system prompt with dynamic variables
        system_prompt = create_system_prompt(
            tools=self.tools,
            model=self.config.model,
            provider=self.config.provider
        )

        # Initialize LLM provider via factory
        self.llm = ProviderFactory.create(
            config=self.config,
            tools=self.tools,
            system_prompt=system_prompt,
        )

    def _needs_approval(self, tool_name: str) -> bool:
        """
        Check if a tool needs user approval before execution.

        Args:
            tool_name: Name of the tool to check

        Returns:
            True if approval is needed, False otherwise
        """
        # Check if tool is configured to require approval
        return self.config.get_tool_config(tool_name).get("approval", False)

    def _prompt_user_approval(self, tool_name: str, tool_args: Dict[str, Any]) -> bool:
        """
        Prompt the user for approval to execute a tool.

        Args:
            tool_name: Name of the tool
            tool_args: Tool arguments

        Returns:
            True if approved, False if rejected
        """
        try:
            response = Prompt.ask(
                "  [yellow]Approve?[/yellow]",
                choices=["y", "n", "yes", "no"],
                default="n",
                show_choices=False,
            )
            return response.lower() in ["y", "yes"]
        except (KeyboardInterrupt, EOFError):
            console.print("  [dim]⎿ Cancelled[/dim]")
            return False

    async def _execute_single_tool(self, tool_call: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a single tool call and return result message.

        Args:
            tool_call: Tool call dict with id, name, arguments

        Returns:
            Result message dict formatted for LLM
        """
        tool_name = tool_call["name"]
        tool_args = tool_call["arguments"]

        logger.info(f"Executing tool: {tool_name} with args: {tool_args}")

        # Determine if approval is needed
        needs_approval = self._needs_approval(tool_name)

        # Always show tool calls so users can see what's being executed
        print_tool_call(tool_name, tool_args, needs_approval=needs_approval)

        try:
            # Check if approval is needed
            if needs_approval:
                approved = self._prompt_user_approval(tool_name, tool_args)
                if not approved:
                    logger.info(f"Tool {tool_name} execution rejected by user")
                    error_result = {"error": "Tool execution rejected by user"}
                    result_message = self.llm.format_tool_result(
                        tool_call["id"], tool_name, error_result
                    )
                    return result_message

            # Record attempt before execution
            attempt = self.execution_tracker.record_attempt(tool_name)

            # Get tool definition
            tool = self.tool_loader.get_tool(tool_name)

            # Check if tool was found
            if tool is None:
                available_tools = list(self.tool_loader.tools_by_name.keys())
                error_msg = (
                    f"Tool '{tool_name}' not found. "
                    f"Available tools: {', '.join(available_tools)}"
                )
                raise ValueError(error_msg)

            # Execute tool with progress indicator
            async with ToolExecutionStatus(tool_name, tool_args):
                result = await self.executor.execute_tool(tool, tool_args)

            logger.info(f"Tool {tool_name} completed successfully")

            # Record success to reset counter
            self.execution_tracker.record_success(tool_name)

            # Show completion
            if self.config.show_tool_output:
                print_tool_result(result)

            # Format result for LLM
            result_message = self.llm.format_tool_result(
                tool_call["id"], tool_name, result
            )

            return result_message

        except Exception as e:
            logger.error(f"Tool {tool_name} failed: {e}")

            # Create structured error with recovery hints
            tool_error = ToolError.from_exception(tool_name, e, tool_args)

            # Check if we can retry
            can_retry = self.execution_tracker.can_retry(tool_name)
            print_tool_error(str(e), will_retry=can_retry)

            # Format error message with recovery guidance for LLM
            error_message = tool_error.to_llm_message(
                attempt=attempt,
                max_attempts=self.execution_tracker.max_attempts,
            )

            # Send structured error back to LLM
            error_result = {"error": error_message}
            result_message = self.llm.format_tool_result(
                tool_call["id"], tool_name, error_result
            )
            return result_message

    async def _execute_tool_calls_parallel(self, tool_calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Execute multiple tool calls in parallel when possible.

        Tools requiring approval are executed sequentially to avoid
        overlapping approval prompts.

        Args:
            tool_calls: List of tool call dicts

        Returns:
            List of result message dicts formatted for LLM
        """
        # Separate tools that need approval from those that don't
        needs_approval_calls = []
        auto_approved_calls = []

        for tool_call in tool_calls:
            if self._needs_approval(tool_call["name"]):
                needs_approval_calls.append(tool_call)
            else:
                auto_approved_calls.append(tool_call)

        results = []

        # Execute auto-approved tools in parallel
        if auto_approved_calls:
            logger.info(f"Executing {len(auto_approved_calls)} tools in parallel")
            parallel_results = await asyncio.gather(
                *[self._execute_single_tool(tc) for tc in auto_approved_calls],
                return_exceptions=False
            )
            results.extend(parallel_results)

        # Execute approval-required tools sequentially
        if needs_approval_calls:
            logger.info(f"Executing {len(needs_approval_calls)} tools sequentially (require approval)")
            for tool_call in needs_approval_calls:
                result = await self._execute_single_tool(tool_call)
                results.append(result)

        # Add all results to message history
        for result in results:
            self.messages.append(result)

        return results

    async def chat(self, user_message: str) -> str:
        """
        Process a user message and return the agent's response.

        Args:
            user_message: User's message

        Returns:
            Agent's final response
        """
        # Reset execution tracker for new conversation turn
        self.execution_tracker.reset()

        # Add user message to history (unless it's empty and we already have messages)
        # This handles the sub-agent case where initial_messages are provided
        if user_message or not self.messages:
            self.messages.append({"role": "user", "content": user_message})

        # Conversation loop with configurable max iterations
        max_iterations = self.config.max_iterations
        iteration = 0

        try:
            while iteration < max_iterations:
                iteration += 1
                logger.info(f"Agent iteration {iteration}/{max_iterations}")

                # Call LLM with thinking status indicator
                async with ThinkingStatus():
                    response = await self.llm.call(self.messages)

                # Add assistant message to history
                assistant_message = self.llm.format_assistant_message(response)
                self.messages.append(assistant_message)

                # If no tool calls, we're done
                if response["done"]:
                    logger.info("Agent conversation complete")
                    return response["message"]

                # Execute tool calls in parallel when possible
                tool_names = [tc["name"] for tc in response["tool_calls"]]
                logger.info(
                    f"Executing {len(response['tool_calls'])} tool(s): {tool_names}"
                )

                await self._execute_tool_calls_parallel(response["tool_calls"])

            return "Maximum iteration limit reached. Please try a simpler request."

        except KeyboardInterrupt:
            # User interrupted - clean up message history
            if self.messages and self.messages[-1].get("role") == "user":
                self.messages.pop()
            console.print("\n[dim]Interrupted[/dim]")
            return ""
