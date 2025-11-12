"""Built-in read tool for reading file contents"""

import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Maximum file size to read (10 MB)
MAX_FILE_SIZE = 10 * 1024 * 1024

# Default line limit
DEFAULT_LINE_LIMIT = 2000
MAX_LINE_LIMIT = 10000

# Maximum line length before truncation
MAX_LINE_LENGTH = 2000


async def execute_read(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute the read tool to read file contents.

    Args:
        args: Tool arguments containing:
            - file_path: Path to file to read (required)
            - offset: Line number to start reading from (optional, default 0)
            - limit: Number of lines to read (optional, default 2000, max 10000)

    Returns:
        Result dict with file content or error
    """
    file_path = args.get("file_path")
    offset = args.get("offset", 0)
    limit = args.get("limit", DEFAULT_LINE_LIMIT)

    # Validate required parameters
    if not file_path:
        return {"error": "Missing required parameter: file_path"}

    # Validate offset and limit
    try:
        offset = int(offset)
        limit = int(limit)
    except (ValueError, TypeError):
        return {"error": "offset and limit must be integers"}

    if offset < 0:
        return {"error": "offset must be non-negative"}

    if limit < 1:
        return {"error": "limit must be at least 1"}

    if limit > MAX_LINE_LIMIT:
        return {"error": f"limit cannot exceed {MAX_LINE_LIMIT}"}

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
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

        total_lines = len(lines)

        # Apply offset and limit
        end_line = min(offset + limit, total_lines)
        selected_lines = lines[offset:end_line]

        # Format with line numbers (starting from offset + 1)
        formatted_lines = []
        for i, line in enumerate(selected_lines, start=offset + 1):
            # Truncate long lines
            if len(line) > MAX_LINE_LENGTH:
                line = line[:MAX_LINE_LENGTH] + "... [truncated]\n"

            # Remove trailing newline for formatting, will add back
            line_content = line.rstrip("\n")
            formatted_lines.append(f"{i:6d}→{line_content}")

        output = "\n".join(formatted_lines)

        # Add metadata about what was read
        metadata = {
            "file_path": str(path),
            "total_lines": total_lines,
            "lines_read": len(selected_lines),
            "offset": offset,
            "limit": limit,
            "file_size": file_size,
        }

        # Add warning if file was partially read
        if total_lines > end_line:
            lines_remaining = total_lines - end_line
            output += f"\n\n... {lines_remaining} more lines not shown (use offset={end_line} to continue)"

        return {
            "output": output,
            "metadata": metadata,
        }

    except UnicodeDecodeError:
        return {"error": f"File is not a valid text file (encoding error): {file_path}"}

    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        return {"error": f"Error reading file: {str(e)}"}


# Tool definition for loader
READ_TOOL_DEFINITION = {
    "name": "file_read",
    "description": "Read the contents of a file with line numbers. Supports reading large files with offset and limit parameters. Line numbers use the format 'N→content' where N is the line number.",
    "parameters": {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "The absolute path to the file to read",
            },
            "offset": {
                "type": "integer",
                "description": "The line number to start reading from (0-indexed, default: 0)",
                "default": 0,
            },
            "limit": {
                "type": "integer",
                "description": f"The number of lines to read (default: {DEFAULT_LINE_LIMIT}, max: {MAX_LINE_LIMIT})",
                "default": DEFAULT_LINE_LIMIT,
            },
        },
        "required": ["file_path"],
    },
}
