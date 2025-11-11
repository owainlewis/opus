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

    For YAML recipes: Returns the prompt as context for the agent to use
    For Markdown recipes: Executes steps (legacy behavior)

    Args:
        args: Tool arguments containing:
            - recipe_name: Name of recipe to run
            - params: Optional dict of parameter values

    Returns:
        Dict with execution results or prompt context
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

        # Handle based on format
        if recipe_def.get('format') == 'yaml':
            # New format: Return prompt as context for agent
            return _handle_yaml_recipe(recipe_with_vars, recipe_name, params)
        else:
            # Legacy format: Execute steps
            return await _handle_markdown_recipe(recipe_with_vars, recipe_name, params)

    except FileNotFoundError:
        return {"error": f"Recipe not found: {recipe_name}"}

    except Exception as e:
        logger.error(f"Error executing recipe '{recipe_name}': {e}", exc_info=True)
        return {"error": f"Recipe execution failed: {str(e)}"}


def _handle_yaml_recipe(recipe: Dict[str, Any], recipe_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle YAML recipe by returning prompt as context.

    Args:
        recipe: Recipe with interpolated variables
        recipe_name: Name of recipe
        params: Parameter values

    Returns:
        Dict with prompt and instructions
    """
    logger.info(f"Loading YAML recipe '{recipe_name}' as context")

    # Build output message
    output_lines = []
    output_lines.append(f"Recipe: {recipe['title']}")
    output_lines.append(f"Description: {recipe['description']}")
    output_lines.append("")
    output_lines.append("=" * 60)
    output_lines.append("RECIPE CONTEXT:")
    output_lines.append("=" * 60)
    output_lines.append("")

    # Include instructions if present (system-level role/persona)
    if recipe.get('instructions'):
        output_lines.append("## Role")
        output_lines.append("")
        output_lines.append(recipe['instructions'])
        output_lines.append("")
        output_lines.append("## Task")
        output_lines.append("")

    output_lines.append(recipe['prompt'])
    output_lines.append("")
    output_lines.append("=" * 60)
    output_lines.append("")
    output_lines.append("You should now proceed with the task using the context above.")
    output_lines.append("Use your available tools to complete the work described in the recipe.")

    return {
        "output": "\n".join(output_lines),
        "metadata": {
            "recipe": recipe_name,
            "format": "yaml",
            "title": recipe['title'],
            "parameters": params
        }
    }


async def _handle_markdown_recipe(recipe: Dict[str, Any], recipe_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle Markdown recipe by executing steps (legacy behavior).

    Args:
        recipe: Recipe with interpolated variables
        recipe_name: Name of recipe
        params: Parameter values

    Returns:
        Dict with execution results
    """
    logger.info(f"Executing Markdown recipe '{recipe_name}' (legacy mode)")

    # Get current opus config
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
    result = await executor.execute_recipe(recipe)

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
            "format": "markdown",
            "completed": result.completed_steps,
            "failed": result.failed_steps,
            "skipped": result.skipped_steps,
            "aborted": result.aborted
        }
    }


# Tool definition for loader
RECIPE_TOOL_DEFINITION = {
    "name": "recipe",
    "description": "Load a recipe - a specialized, reusable prompt package that provides expert context and instructions for specific tasks. Recipes are like specialized skills that guide you through complex tasks. Examples: python-code-review, api-spec-review, weekly-report, incident-response. When you load a recipe, you receive detailed context and instructions to complete the task effectively.",
    "parameters": {
        "type": "object",
        "properties": {
            "recipe_name": {
                "type": "string",
                "description": "Name of the recipe to load (e.g., 'python-code-review', 'api-spec-review', 'weekly-report')"
            },
            "params": {
                "type": "object",
                "description": "Recipe parameters as key-value pairs (e.g., {'file_path': 'src/app.py', 'focus': 'security'})"
            }
        },
        "required": ["recipe_name"]
    },
}
