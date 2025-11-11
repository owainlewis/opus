"""Tool executor for running tool scripts via subprocess

SECURITY NOTE: This executor uses create_subprocess_exec instead of
create_subprocess_shell to prevent shell injection vulnerabilities.
"""

import asyncio
import json
import os
import shlex
from typing import Dict, Any, List


class ToolExecutor:
    """
    Securely executes tools by running their scripts in subprocesses.

    Handles:
    - Parameter substitution in script commands
    - Secure subprocess execution (no shell injection)
    - Output capture and parsing
    - Error handling

    Security:
    - Uses create_subprocess_exec instead of create_subprocess_shell
    - Properly escapes and splits arguments using shlex
    - Prevents shell metacharacter injection
    """

    def __init__(self, timeout: int = 30):
        """
        Initialize the executor.

        Args:
            timeout: Default timeout in seconds for tool execution
        """
        self.timeout = timeout

    async def execute_tool(self, tool: Dict, arguments: Dict) -> Any:
        """
        Execute a tool with given arguments.

        Args:
            tool: Tool definition from tool loader
            arguments: Tool arguments from LLM

        Returns:
            Tool execution result (parsed JSON if possible, else string)

        Raises:
            Exception: If tool execution fails
        """
        # Apply default values from parameter schema
        arguments = self._apply_defaults(tool.get("parameters", {}), arguments)

        # Check if this is a Python callable tool
        if "python_callable" in tool:
            # Execute Python function directly
            result = await tool["python_callable"](arguments)
            return result

        # Build command array securely for script-based tools
        command_array = self._build_command_array(tool["script"], arguments)

        # Determine timeout: tool-level or executor default
        timeout = tool.get("timeout", self.timeout)

        # Execute script
        result = await self._run_command(command_array, cwd=tool["tool_path"], timeout=timeout)

        return result

    def _apply_defaults(self, parameters: Dict, arguments: Dict) -> Dict:
        """
        Apply default values from parameter schema to arguments.

        Args:
            parameters: Parameter schema (with properties and defaults)
            arguments: Provided arguments from LLM

        Returns:
            Arguments with defaults applied
        """
        # Handle None arguments
        if arguments is None:
            arguments = {}

        # Copy arguments to avoid modifying original
        result = dict(arguments)

        # Extract properties from schema
        properties = parameters.get("properties", {})

        # Apply defaults for missing parameters
        for param_name, param_schema in properties.items():
            if param_name not in result and "default" in param_schema:
                result[param_name] = param_schema["default"]

        return result

    def _build_command_array(self, script_template: str, arguments: Dict) -> List[str]:
        """
        Build a secure command array from script template and arguments.

        This method prevents shell injection by:
        1. Parsing the template to identify placeholders
        2. Substituting arguments safely with proper quoting
        3. Using shlex to properly split the command
        4. Returning an array suitable for create_subprocess_exec

        Args:
            script_template: Script template with {param} placeholders
            arguments: Argument values

        Returns:
            List of command parts suitable for exec (not shell)

        Examples:
            >>> _build_command_array("git {args}", {"args": "log -5"})
            ["git", "log", "-5"]

            >>> _build_command_array("python tool.py {include_env}", {"include_env": "true"})
            ["python", "tool.py", "true"]
        """
        # Handle None arguments
        if arguments is None:
            arguments = {}

        # Convert arguments to strings for substitution with proper quoting
        safe_args = {}
        for key, value in arguments.items():
            if value is None or value == "":
                # Quote empty strings to preserve them through shlex.split()
                safe_args[key] = "''"
            elif isinstance(value, bool):
                # Convert boolean to lowercase string (true/false)
                safe_args[key] = str(value).lower()
            elif isinstance(value, (dict, list)):
                # Serialize dict/list to JSON and quote it
                json_value = json.dumps(value)
                safe_args[key] = shlex.quote(json_value)
            else:
                # Quote arguments that contain spaces or special characters
                str_value = str(value)
                if ' ' in str_value or any(c in str_value for c in ['"', "'", '\\', '|', '&', ';', '<', '>', '(', ')', '`', '$']):
                    safe_args[key] = shlex.quote(str_value)
                else:
                    safe_args[key] = str_value

        # Substitute parameters in template
        try:
            substituted_script = script_template.format(**safe_args)
        except KeyError as e:
            raise ValueError(f"Missing required parameter: {e}")

        # Use shlex to properly split command into array
        try:
            command_array = shlex.split(substituted_script)
        except ValueError as e:
            raise ValueError(f"Invalid command syntax: {e}")

        if not command_array:
            raise ValueError("Empty command after substitution")

        return command_array

    async def _run_command(self, command_array: List[str], cwd: str, timeout: int = None) -> Any:
        """
        Run a command via subprocess using exec (not shell).

        This is secure against shell injection because:
        - Uses create_subprocess_exec instead of create_subprocess_shell
        - Arguments are passed as array, not interpolated into shell string
        - Shell metacharacters (;|&`$()) have no special meaning

        Args:
            command_array: Command and arguments as array
            cwd: Working directory (tool path)
            timeout: Timeout in seconds (defaults to self.timeout)

        Returns:
            Parsed output (JSON if possible, else string)

        Raises:
            Exception: If command execution fails with detailed error information
        """
        cmd_str = " ".join(command_array)
        timeout = timeout if timeout is not None else self.timeout

        try:
            # Get the original working directory (where the user is)
            original_cwd = os.getcwd()

            # Create environment with original CWD for tools to use
            env = os.environ.copy()
            env["OPUS_CWD"] = original_cwd

            # SECURE: Use exec with argument array, not shell with string
            process = await asyncio.create_subprocess_exec(
                *command_array,  # Unpack array into separate arguments
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
                env=env,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                raise Exception(
                    f"Command timed out after {timeout}s\n"
                    f"Command: {cmd_str}\n"
                    f"Working directory: {cwd}"
                )

            # Decode output streams
            stdout_text = stdout.decode("utf-8", errors="replace").strip() if stdout else ""
            stderr_text = stderr.decode("utf-8", errors="replace").strip() if stderr else ""

            # Check return code
            if process.returncode != 0:
                # Build detailed error message
                error_parts = [
                    f"Command failed with exit code {process.returncode}",
                    f"Command: {cmd_str}",
                    f"Working directory: {cwd}",
                ]

                if stderr_text:
                    error_parts.append(f"Error output (stderr):\n{stderr_text}")

                if stdout_text:
                    error_parts.append(f"Standard output (stdout):\n{stdout_text}")

                if not stderr_text and not stdout_text:
                    error_parts.append("No output captured from command")

                raise Exception("\n".join(error_parts))

            # Parse output - always wrap in {"output": ...} for consistent handling
            return {"output": stdout_text}

        except FileNotFoundError:
            # Command not found in PATH
            raise Exception(
                f"Command not found: '{command_array[0]}'\n"
                f"Full command: {cmd_str}\n"
                f"Working directory: {cwd}\n"
                f"Ensure the command is installed and available in PATH"
            )
        except asyncio.TimeoutError:
            # Re-raise timeout errors as-is
            raise
        except Exception as e:
            # Check if this is already a detailed error from above
            if "Command failed with exit code" in str(e) or "Command not found" in str(e) or "timed out" in str(e):
                raise

            # Otherwise, wrap with additional context
            raise Exception(
                f"Tool execution error: {str(e)}\n"
                f"Command: {cmd_str}\n"
                f"Working directory: {cwd}"
            )
