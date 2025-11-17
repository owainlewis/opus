"""Built-in ask_approval tool for getting user confirmation before risky operations"""

import logging
from typing import Dict, Any, List
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.markdown import Markdown

logger = logging.getLogger(__name__)
console = Console()


async def execute_ask_approval(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute the ask_approval tool to get user confirmation for risky operations.

    Args:
        args: Tool arguments containing:
            - plan: Description of what will be done (required)
            - options: List of choices for the user (optional, defaults to Yes/No)

    Returns:
        Result dict with user's selected option
    """
    plan = args.get("plan")
    options = args.get("options", ["Proceed", "Cancel"])

    # Validate required parameters
    if not plan:
        return {"error": "Missing required parameter: plan"}

    # Validate options
    if not isinstance(options, list) or len(options) < 2:
        return {"error": "options must be a list with at least 2 choices"}

    if len(options) > 5:
        return {"error": "options cannot have more than 5 choices"}

    try:
        # Display the plan in a nice panel
        console.print()
        console.print(Panel(
            Markdown(plan),
            title="[yellow]⚠ Approval Required[/yellow]",
            border_style="yellow",
            padding=(1, 2)
        ))
        console.print()

        # Create numbered choices
        choices_display = []
        for i, option in enumerate(options, 1):
            choices_display.append(f"  {i}. {option}")

        console.print("\n".join(choices_display))
        console.print()

        # Prompt user for selection
        # Accept both number and full text
        valid_numbers = [str(i) for i in range(1, len(options) + 1)]
        all_choices = valid_numbers + options

        response = Prompt.ask(
            "  [yellow]Select an option[/yellow]",
            choices=all_choices,
            default="2",  # Default to second option (usually Cancel)
            show_choices=False,
        )

        # Convert number to option text if needed
        selected_option = response
        if response in valid_numbers:
            selected_option = options[int(response) - 1]

        console.print(f"  [dim]⎿ Selected: {selected_option}[/dim]")
        console.print()

        return {
            "output": f"User selected: {selected_option}",
            "selected_option": selected_option,
            "selected_index": options.index(selected_option),
        }

    except (KeyboardInterrupt, EOFError):
        console.print("  [dim]⎿ Cancelled[/dim]")
        return {
            "output": "User cancelled the operation",
            "selected_option": "Cancel",
            "cancelled": True,
        }
    except Exception as e:
        logger.error(f"Error prompting for approval: {e}")
        return {"error": f"Error prompting for approval: {str(e)}"}


# Tool definition for loader
ASK_APPROVAL_TOOL_DEFINITION = {
    "name": "ask_approval",
    "description": """Ask the user for approval before executing risky or destructive operations.

Use this tool when you are about to:
- Delete, move, or modify files (especially multiple files or important files)
- Execute commands that could affect system state (deployments, restarts, etc.)
- Make changes to production environments
- Perform batch operations
- Execute any operation that could result in data loss or significant changes

Present a clear plan of what you intend to do, and provide relevant options for the user to choose from.

Example usage:
{
  "plan": "I will delete 247 log files older than 30 days from /var/log/production, totaling 15.3 GB.",
  "options": ["Proceed - delete all files now", "Dry run - show what would be deleted first", "Cancel"]
}""",
    "parameters": {
        "type": "object",
        "properties": {
            "plan": {
                "type": "string",
                "description": "A clear description of what you plan to do. Supports markdown formatting. Include specific details like file counts, sizes, paths, or impacts.",
            },
            "options": {
                "type": "array",
                "description": "List of choices to present to the user (2-5 options). The user will select one. Consider including options like 'Proceed', 'Dry run first', 'Modify approach', or 'Cancel'.",
                "items": {
                    "type": "string",
                },
                "minItems": 2,
                "maxItems": 5,
                "default": ["Proceed", "Cancel"],
            },
        },
        "required": ["plan"],
    },
}
