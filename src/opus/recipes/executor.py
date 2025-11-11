"""Recipe executor for automatic execution via agent"""

import logging
from typing import Dict, Any, Optional
from opus.tools.executor import ToolExecutor
from opus.tools.loader import ToolLoader

logger = logging.getLogger(__name__)


class RecipeExecutionResult:
    """Result of recipe execution"""

    def __init__(self):
        self.completed_steps = 0
        self.failed_steps = 0
        self.skipped_steps = 0
        self.step_results = []
        self.aborted = False

    def add_step_result(self, step_name: str, status: str, output: Optional[str] = None, error: Optional[str] = None):
        """
        Add a step result.

        Args:
            step_name: Name of the step
            status: 'completed', 'failed', 'skipped'
            output: Output from step
            error: Error message if failed
        """
        self.step_results.append({
            "name": step_name,
            "status": status,
            "output": output,
            "error": error,
        })

        if status == "completed":
            self.completed_steps += 1
        elif status == "failed":
            self.failed_steps += 1
        elif status == "skipped":
            self.skipped_steps += 1


class RecipeExecutor:
    """
    Executes recipes automatically (agent-only mode).

    Handles:
    - Step-by-step execution
    - Tool execution
    - Manual steps
    - Result tracking
    """

    def __init__(self, tool_loader: ToolLoader, tool_executor: ToolExecutor):
        """
        Initialize recipe executor.

        Args:
            tool_loader: Tool loader for getting tool definitions
            tool_executor: Tool executor for running tools
        """
        self.tool_loader = tool_loader
        self.tool_executor = tool_executor

    async def execute_recipe(self, recipe: Dict[str, Any]) -> RecipeExecutionResult:
        """
        Execute a recipe step by step automatically.

        Args:
            recipe: Recipe definition with interpolated parameters

        Returns:
            RecipeExecutionResult with execution summary
        """
        result = RecipeExecutionResult()
        total_steps = len(recipe["steps"])

        logger.info(f"Executing recipe '{recipe['name']}' with {total_steps} steps")

        # Execute each step
        for step_num, step in enumerate(recipe["steps"], 1):
            logger.info(f"Executing step {step_num}/{total_steps}: {step['name']}")

            # Execute step
            try:
                step_result = await self._execute_step(step)

                if step_result["success"]:
                    result.add_step_result(
                        step["name"],
                        "completed",
                        output=step_result.get("output")
                    )
                    logger.info(f"Step {step_num} completed: {step['name']}")
                else:
                    result.add_step_result(
                        step["name"],
                        "failed",
                        error=step_result.get("error")
                    )
                    logger.error(f"Step {step_num} failed: {step_result.get('error')}")

            except Exception as e:
                # Unexpected error
                error_msg = str(e)
                result.add_step_result(step["name"], "failed", error=error_msg)
                logger.error(f"Step {step_num} error: {e}", exc_info=True)

        logger.info(f"Recipe '{recipe['name']}' execution complete: "
                   f"{result.completed_steps} completed, "
                   f"{result.failed_steps} failed, "
                   f"{result.skipped_steps} skipped")

        return result

    async def _execute_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a single recipe step.

        Args:
            step: Step definition

        Returns:
            Dict with 'success', 'output', and optionally 'error'
        """
        if step.get("manual"):
            # Manual step - user confirms they've done it
            return {
                "success": True,
                "output": "Manual step completed by user"
            }

        # Tool step - execute via tool executor
        tool_name = step["tool"]
        tool_args = step.get("args", {})

        logger.info(f"Executing tool '{tool_name}' with args: {tool_args}")

        try:
            # Get tool definition
            tool = self.tool_loader.get_tool(tool_name)
            if not tool:
                return {
                    "success": False,
                    "error": f"Tool '{tool_name}' not found"
                }

            # Execute tool
            tool_result = await self.tool_executor.execute_tool(tool, tool_args)

            # Extract output
            if isinstance(tool_result, dict):
                output = tool_result.get("output", str(tool_result))
                # Check for errors in result
                if "error" in tool_result:
                    return {
                        "success": False,
                        "error": tool_result["error"],
                        "output": output
                    }
            else:
                output = str(tool_result)

            return {
                "success": True,
                "output": output
            }

        except Exception as e:
            logger.error(f"Tool execution failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
