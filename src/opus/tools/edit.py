"""Built-in edit tool for performing exact string replacements in files"""

import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Maximum file size to edit (10 MB)
MAX_FILE_SIZE = 10 * 1024 * 1024


async def execute_edit(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute the edit tool to perform exact string replacement in a file.

    Args:
        args: Tool arguments containing:
            - file_path: Path to file to edit (required)
            - old_string: String to find and replace (required)
            - new_string: String to replace with (required)
            - replace_all: Replace all occurrences (optional, default False)

    Returns:
        Result dict with success message or error
    """
    file_path = args.get("file_path")
    old_string = args.get("old_string")
    new_string = args.get("new_string")
    replace_all = args.get("replace_all", False)

    # Validate required parameters
    if not file_path:
        return {"error": "Missing required parameter: file_path"}

    if old_string is None:
        return {"error": "Missing required parameter: old_string"}

    if new_string is None:
        return {"error": "Missing required parameter: new_string"}

    # Validate that strings are different
    if old_string == new_string:
        return {"error": "old_string and new_string must be different"}

    # Convert to Path object
    try:
        path = Path(file_path).resolve()
    except Exception as e:
        return {"error": f"Invalid file path: {str(e)}"}

    # Check if file exists
    if not path.exists():
        return {"error": f"File not found: {file_path}"}

    # Check if it's a file (not a directory)
    if not path.is_file():
        return {"error": f"Path is not a file: {file_path}"}

    # Check file size
    try:
        file_size = path.stat().st_size
        if file_size > MAX_FILE_SIZE:
            return {
                "error": f"File size ({file_size} bytes) exceeds maximum allowed size ({MAX_FILE_SIZE} bytes)"
            }
    except Exception as e:
        return {"error": f"Error checking file size: {str(e)}"}

    # Read file contents
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except UnicodeDecodeError:
        return {"error": f"File is not a valid text file (encoding error): {file_path}"}
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        return {"error": f"Error reading file: {str(e)}"}

    # Check if old_string exists in the file
    if old_string not in content:
        return {
            "error": f"old_string not found in file. The exact string to replace must exist in the file.",
            "old_string_preview": old_string[:100] + "..." if len(old_string) > 100 else old_string,
        }

    # Count occurrences
    occurrence_count = content.count(old_string)

    # If not replace_all, ensure the string is unique
    if not replace_all and occurrence_count > 1:
        return {
            "error": f"old_string appears {occurrence_count} times in the file. "
                     f"Either provide a more specific/unique string, or set replace_all=true to replace all occurrences.",
            "occurrences": occurrence_count,
        }

    # Perform replacement
    if replace_all:
        new_content = content.replace(old_string, new_string)
    else:
        # Replace only the first occurrence
        new_content = content.replace(old_string, new_string, 1)

    # Verify that content actually changed
    if new_content == content:
        return {"error": "Replacement did not change the file content"}

    # Write the modified content back
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_content)

        # Calculate stats
        old_line_count = content.count("\n") + 1
        new_line_count = new_content.count("\n") + 1
        line_diff = new_line_count - old_line_count

        output = f"Successfully edited file: {file_path}\n"
        output += f"Replaced {occurrence_count if replace_all else 1} occurrence(s)\n"
        output += f"Old line count: {old_line_count}\n"
        output += f"New line count: {new_line_count}\n"

        if line_diff > 0:
            output += f"Added {line_diff} line(s)"
        elif line_diff < 0:
            output += f"Removed {abs(line_diff)} line(s)"
        else:
            output += "Line count unchanged"

        metadata = {
            "file_path": str(path),
            "occurrences_replaced": occurrence_count if replace_all else 1,
            "old_line_count": old_line_count,
            "new_line_count": new_line_count,
            "line_diff": line_diff,
            "replace_all": replace_all,
        }

        logger.info(f"Successfully edited {file_path}, replaced {occurrence_count if replace_all else 1} occurrence(s)")

        return {
            "output": output,
            "metadata": metadata,
        }

    except PermissionError:
        return {"error": f"Permission denied: {file_path}"}

    except Exception as e:
        logger.error(f"Error writing to file {file_path}: {e}")
        return {"error": f"Error writing changes: {str(e)}"}


# Tool definition for loader
EDIT_TOOL_DEFINITION = {
    "name": "file_edit",
    "description": "Perform exact string replacement in a file. The old_string must match exactly (including whitespace and indentation). If the string appears multiple times, either provide a more unique string or use replace_all=true.",
    "parameters": {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "The absolute path to the file to edit",
            },
            "old_string": {
                "type": "string",
                "description": "The exact string to find and replace (must exist in the file)",
            },
            "new_string": {
                "type": "string",
                "description": "The string to replace with (must be different from old_string)",
            },
            "replace_all": {
                "type": "boolean",
                "description": "If true, replace all occurrences. If false (default), the old_string must be unique in the file.",
                "default": False,
            },
        },
        "required": ["file_path", "old_string", "new_string"],
    },
}
