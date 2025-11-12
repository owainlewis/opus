"""Built-in write tool for writing file contents"""

import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Maximum content size to write (10 MB)
MAX_CONTENT_SIZE = 10 * 1024 * 1024


async def execute_write(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute the write tool to write content to a file.

    Args:
        args: Tool arguments containing:
            - file_path: Path to file to write (required)
            - content: Content to write (required)
            - mode: Write mode - "write" (overwrite) or "append" (optional, default "write")

    Returns:
        Result dict with success message or error
    """
    file_path = args.get("file_path")
    content = args.get("content")
    mode = args.get("mode", "write")

    # Validate required parameters
    if not file_path:
        return {"error": "Missing required parameter: file_path"}

    if content is None:
        return {"error": "Missing required parameter: content"}

    # Validate mode
    if mode not in ["write", "append"]:
        return {"error": "mode must be either 'write' or 'append'"}

    # Check content size
    content_size = len(content.encode("utf-8"))
    if content_size > MAX_CONTENT_SIZE:
        return {
            "error": f"Content size ({content_size} bytes) exceeds maximum allowed size ({MAX_CONTENT_SIZE} bytes)"
        }

    # Convert to Path object
    try:
        path = Path(file_path).resolve()
    except Exception as e:
        return {"error": f"Invalid file path: {str(e)}"}

    # Check if parent directory exists
    parent_dir = path.parent
    if not parent_dir.exists():
        return {
            "error": f"Parent directory does not exist: {parent_dir}. Create the directory first."
        }

    # Check if path exists and is a directory
    if path.exists() and path.is_dir():
        return {"error": f"Path is a directory, not a file: {file_path}"}

    # Write the file
    try:
        write_mode = "w" if mode == "write" else "a"

        with open(path, write_mode, encoding="utf-8") as f:
            f.write(content)

        # Get file info after writing
        file_size = path.stat().st_size
        lines_written = content.count("\n") + (1 if content and not content.endswith("\n") else 0)

        action = "Created" if not path.exists() or mode == "write" else "Appended to"
        output = f"{action} file: {file_path}\n"
        output += f"Lines written: {lines_written}\n"
        output += f"File size: {file_size} bytes"

        metadata = {
            "file_path": str(path),
            "mode": mode,
            "lines_written": lines_written,
            "bytes_written": content_size,
            "file_size": file_size,
        }

        logger.info(f"Successfully wrote {content_size} bytes to {file_path}")

        return {
            "output": output,
            "metadata": metadata,
        }

    except PermissionError:
        return {"error": f"Permission denied: {file_path}"}

    except Exception as e:
        logger.error(f"Error writing to file {file_path}: {e}")
        return {"error": f"Error writing to file: {str(e)}"}


# Tool definition for loader
WRITE_TOOL_DEFINITION = {
    "name": "file_write",
    "description": "Write content to a file. Can create new files or overwrite/append to existing files. The parent directory must exist.",
    "parameters": {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "The absolute path to the file to write",
            },
            "content": {
                "type": "string",
                "description": "The content to write to the file",
            },
            "mode": {
                "type": "string",
                "enum": ["write", "append"],
                "description": "Write mode: 'write' to overwrite the file (default), 'append' to add to the end",
                "default": "write",
            },
        },
        "required": ["file_path", "content"],
    },
}
