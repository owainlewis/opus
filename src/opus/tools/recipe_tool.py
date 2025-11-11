"""Built-in recipe tool for executing recipes from agent"""

import asyncio
import logging
from typing import Dict, Any

from opus.recipes.loader import RecipeLoader
from opus.recipes.executor import RecipeExecutor
from opus.tools.loader import ToolLoader
from opus.tools.executor import ToolExecutor
from opus.config import OpusConfig

logger = logging.getLogger(__name__)


async def execute_recipe_tool(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a recipe from the agent.

    Args:
        args: Tool arguments containing:
            - recipe_name: Name of recipe to run
            - params: Optional dict of parameter values

    Returns:
        Dict with execution results
    """
    recipe_name = args.get("recipe_name")
    params = args.get("params", {})

    if not recipe_name:
        return {"error": "Missing required parameter: recipe_name"}

    try:
        # Load recipe
        loader = RecipeLoader()
        recipe_def = loader.load_recipe(recipe_name)

        # Validate parameters
        param_errors = loader.validate_params(recipe_def, params)
        if param_errors:
            return {
                "error": f"Parameter validation failed:\n" + "\n".join(param_errors)
            }

        # Apply defaults for missing optional parameters
        recipe_params = recipe_def.get("parameters", {})
        for param_name, param_def in recipe_params.items():
            if param_name not in params and "default" in param_def:
                params[param_name] = param_def["default"]

        # Interpolate variables
        recipe_with_vars = loader.interpolate_variables(recipe_def, params)

        # Get current opus config (assuming it's accessible globally or passed in)
        # For now, we'll create a minimal setup
        # TODO: Pass config through from agent
        opus_config = OpusConfig.from_yaml()

        # Load tools
        tool_loader = ToolLoader()
        enabled_tools = opus_config.get_enabled_tools()
        tools = tool_loader.load_tools(config=opus_config, enabled_tools=enabled_tools)

        # Create tool executor
        tool_executor = ToolExecutor(timeout=opus_config.default_timeout)

        # Create recipe executor (agent-only, no approval needed)
        executor = RecipeExecutor(
            tool_loader=tool_loader,
            tool_executor=tool_executor
        )

        # Execute recipe
        logger.info(f"Agent executing recipe '{recipe_name}' with params {params}")
        result = await executor.execute_recipe(recipe_with_vars)

        # Format results for agent
        summary_lines = []
        summary_lines.append(f"Recipe '{recipe_name}' execution complete:")
        summary_lines.append(f"- Completed: {result.completed_steps}/{result.completed_steps + result.failed_steps + result.skipped_steps}")

        if result.failed_steps > 0:
            summary_lines.append(f"- Failed: {result.failed_steps}")
        if result.skipped_steps > 0:
            summary_lines.append(f"- Skipped: {result.skipped_steps}")

        # Include step details
        summary_lines.append("\nStep Results:")
        for step_result in result.step_results:
            status_emoji = {
                "completed": "✓",
                "failed": "✗",
                "skipped": "⊘",
                "aborted": "⚠"
            }.get(step_result["status"], "?")

            summary_lines.append(f"{status_emoji} {step_result['name']} - {step_result['status']}")

            # Include output for completed steps (truncated)
            if step_result["status"] == "completed" and step_result.get("output"):
                output = step_result["output"].strip()
                lines = output.split('\n')
                if len(lines) > 3:
                    summary_lines.append(f"  Output: {lines[0]}")
                    summary_lines.append(f"  ... ({len(lines) - 1} more lines)")
                else:
                    summary_lines.append(f"  Output: {output[:200]}")

            # Include errors for failed steps
            if step_result["status"] == "failed" and step_result.get("error"):
                error = step_result["error"][:200]
                summary_lines.append(f"  Error: {error}")

        return {
            "output": "\n".join(summary_lines),
            "metadata": {
                "recipe": recipe_name,
                "completed": result.completed_steps,
                "failed": result.failed_steps,
                "skipped": result.skipped_steps,
                "aborted": result.aborted
            }
        }

    except FileNotFoundError:
        return {"error": f"Recipe not found: {recipe_name}"}

    except Exception as e:
        logger.error(f"Error executing recipe '{recipe_name}': {e}", exc_info=True)
        return {"error": f"Recipe execution failed: {str(e)}"}


# Tool definition for loader
RECIPE_TOOL_DEFINITION = {
    "name": "recipe",
    "description": "Execute a recipe - a step-by-step guide that can be an operational runbook or knowledge guide. Recipes combine context, instructions, and executable steps. Examples: incident response, debugging workflows, code review procedures, health checks. Steps are executed automatically with your assistance.",
    "parameters": {
        "type": "object",
        "properties": {
            "recipe_name": {
                "type": "string",
                "description": "Name of the recipe to execute (e.g., 'k8s-pod-debug', 'incident-triage', 'health-check')"
            },
            "params": {
                "type": "object",
                "description": "Recipe parameters as key-value pairs (e.g., {'service': 'api', 'namespace': 'production'})"
            }
        },
        "required": ["recipe_name"]
    },
}
