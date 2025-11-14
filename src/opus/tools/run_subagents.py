"""Built-in tool for running parallel/sequential sub-agents"""

import asyncio
import logging
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Union

logger = logging.getLogger(__name__)

# Maximum number of sub-agents that can run in parallel
MAX_SUBAGENTS = 10

# Default timeout for each sub-agent (5 minutes)
DEFAULT_SUBAGENT_TIMEOUT = 300


async def _prepare_context(context_spec: Union[str, Dict[str, Any]]) -> Optional[str]:
    """
    Convert context specification into actual context content.

    Args:
        context_spec: Either direct text string or a dict with type and location

    Returns:
        Context content as string, or None if no context
    """
    if context_spec is None:
        return None

    # Direct text context
    if isinstance(context_spec, str):
        return context_spec

    # Structured context with type
    if isinstance(context_spec, dict):
        context_type = context_spec.get("type")

        if context_type == "file":
            # Read file content
            file_path = context_spec.get("path")
            if not file_path:
                raise ValueError("File context requires 'path' field")

            try:
                path = Path(file_path).resolve()
                if not path.exists():
                    raise FileNotFoundError(f"File not found: {file_path}")
                if not path.is_file():
                    raise ValueError(f"Path is not a file: {file_path}")

                # Read file (with size limit)
                max_size = 10 * 1024 * 1024  # 10MB
                if path.stat().st_size > max_size:
                    raise ValueError(f"File too large: {file_path} (max {max_size} bytes)")

                with open(path, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()

                return f"File: {file_path}\n\n{content}"

            except Exception as e:
                raise ValueError(f"Error reading file {file_path}: {str(e)}")

        elif context_type == "url":
            # Fetch URL content using the fetch tool
            url = context_spec.get("url")
            if not url:
                raise ValueError("URL context requires 'url' field")

            # Import here to avoid circular dependency
            from opus.tools.fetch_url import fetch_url_content

            result = await fetch_url_content(url)
            if "error" in result:
                raise ValueError(f"Error fetching URL {url}: {result['error']}")

            return f"URL: {url}\n\n{result['content']}"

        elif context_type == "files":
            # Read multiple files
            paths = context_spec.get("paths", [])
            if not paths:
                raise ValueError("Files context requires 'paths' field with list of paths")

            contents = []
            for file_path in paths:
                try:
                    path = Path(file_path).resolve()
                    if not path.exists() or not path.is_file():
                        contents.append(f"[Error: {file_path} not found or not a file]")
                        continue

                    with open(path, 'r', encoding='utf-8', errors='replace') as f:
                        file_content = f.read()

                    contents.append(f"=== {file_path} ===\n{file_content}")
                except Exception as e:
                    contents.append(f"[Error reading {file_path}: {str(e)}]")

            return "\n\n".join(contents)

        else:
            raise ValueError(f"Unknown context type: {context_type}")

    return None


def _build_initial_messages(prompt: str, context: Optional[str]) -> List[Dict[str, str]]:
    """
    Build initial message history for a sub-agent.

    Args:
        prompt: The task prompt for the sub-agent
        context: Optional context content

    Returns:
        List of message dicts for initial history
    """
    messages = []

    if context:
        # Add context as first message
        messages.append({
            "role": "user",
            "content": f"Here is the context for your task:\n\n{context}"
        })

    # Add the actual task prompt
    messages.append({
        "role": "user",
        "content": prompt
    })

    return messages


async def _spawn_subagent(
    task_spec: Union[str, Dict[str, Any]],
    task_id: int,
    config_path: Optional[str] = None,
    max_turns: Optional[int] = None
) -> Dict[str, Any]:
    """
    Spawn and run a single sub-agent.

    Args:
        task_spec: Either a prompt string or a dict with 'prompt' and optional 'context'
        task_id: Unique identifier for this task
        config_path: Optional path to config file
        max_turns: Optional max iterations for sub-agent

    Returns:
        Dict with task result
    """
    start_time = time.time()

    try:
        # Parse task specification
        if isinstance(task_spec, str):
            prompt = task_spec
            context_spec = None
        elif isinstance(task_spec, dict):
            prompt = task_spec.get("prompt")
            if not prompt:
                raise ValueError("Task dict must have 'prompt' field")
            context_spec = task_spec.get("context")
        else:
            raise ValueError(f"Task must be string or dict, got {type(task_spec)}")

        # Prepare context if provided
        context = None
        if context_spec is not None:
            try:
                context = await _prepare_context(context_spec)
            except Exception as e:
                return {
                    "task_id": task_id,
                    "prompt": prompt,
                    "status": "error",
                    "error": f"Context preparation failed: {str(e)}",
                    "execution_time": time.time() - start_time
                }

        # Build initial messages
        initial_messages = _build_initial_messages(prompt, context)

        # Import OpusAgent here to avoid circular imports
        from opus.agent import OpusAgent
        from opus.config import OpusConfig

        # Load config
        config = OpusConfig.from_yaml(config_path)

        # Override max_turns if specified
        if max_turns is not None:
            config.max_iterations = max_turns
        elif hasattr(config, 'subagent_max_turns'):
            config.max_iterations = config.subagent_max_turns
        else:
            # Default to 15 for sub-agents (lower than typical parent of 25)
            config.max_iterations = 15

        # Create sub-agent instance
        logger.info(f"Spawning sub-agent {task_id} with prompt: {prompt[:100]}...")
        sub_agent = OpusAgent(
            config_path=config_path,
            is_subagent=True,
            initial_messages=initial_messages
        )

        # Run the sub-agent with timeout
        timeout = config.default_timeout if hasattr(config, 'default_timeout') else DEFAULT_SUBAGENT_TIMEOUT

        try:
            # The sub-agent already has initial messages, so we pass empty string
            # to start the conversation loop
            result = await asyncio.wait_for(
                sub_agent.chat(""),
                timeout=timeout
            )

            execution_time = time.time() - start_time

            logger.info(f"Sub-agent {task_id} completed successfully in {execution_time:.2f}s")

            return {
                "task_id": task_id,
                "prompt": prompt,
                "status": "success",
                "output": result,
                "execution_time": execution_time
            }

        except asyncio.TimeoutError:
            execution_time = time.time() - start_time
            logger.warning(f"Sub-agent {task_id} timed out after {timeout}s")

            return {
                "task_id": task_id,
                "prompt": prompt,
                "status": "error",
                "error": f"Sub-agent timed out after {timeout} seconds",
                "execution_time": execution_time
            }

    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"Sub-agent {task_id} failed: {e}")

        return {
            "task_id": task_id,
            "prompt": task_spec if isinstance(task_spec, str) else task_spec.get("prompt", "unknown"),
            "status": "error",
            "error": str(e),
            "execution_time": execution_time
        }


def _aggregate_results(results: List[Dict[str, Any]], execution_mode: str, total_time: float) -> str:
    """
    Aggregate sub-agent results into a formatted summary.

    Args:
        results: List of result dicts from sub-agents
        execution_mode: "parallel" or "sequential"
        total_time: Total execution time in seconds

    Returns:
        Formatted summary string
    """
    successful = [r for r in results if r["status"] == "success"]
    failed = [r for r in results if r["status"] == "error"]

    lines = []
    lines.append(f"{'='*80}")
    lines.append(f"SUB-AGENT EXECUTION SUMMARY ({execution_mode.upper()})")
    lines.append(f"{'='*80}")
    lines.append(f"Total tasks: {len(results)}")
    lines.append(f"Successful: {len(successful)}")
    lines.append(f"Failed: {len(failed)}")
    lines.append(f"Total execution time: {total_time:.2f}s")
    lines.append(f"{'='*80}")
    lines.append("")

    # Show successful results
    if successful:
        lines.append("## SUCCESSFUL TASKS")
        lines.append("")
        for result in successful:
            lines.append(f"### Task {result['task_id']}: {result['prompt']}")
            lines.append(f"Time: {result['execution_time']:.2f}s")
            lines.append("")
            lines.append(result['output'])
            lines.append("")
            lines.append(f"{'-'*80}")
            lines.append("")

    # Show failed results
    if failed:
        lines.append("## FAILED TASKS")
        lines.append("")
        for result in failed:
            lines.append(f"### Task {result['task_id']}: {result['prompt']}")
            lines.append(f"Error: {result['error']}")
            lines.append(f"Time: {result['execution_time']:.2f}s")
            lines.append("")
            lines.append(f"{'-'*80}")
            lines.append("")

    return "\n".join(lines)


async def execute_run_subagents(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute the run_subagents tool.

    Spawns multiple sub-agents to execute tasks in parallel or sequentially.
    Each sub-agent is a full OpusAgent instance with access to all tools.

    Args:
        args: Tool arguments containing:
            - tasks: List of task specifications (strings or dicts with prompt/context)
            - execution_mode: "parallel" or "sequential" (default: "parallel")
            - max_turns: Optional max iterations per sub-agent

    Returns:
        Result dict with aggregated output and metadata
    """
    tasks = args.get("tasks", [])
    execution_mode = args.get("execution_mode", "parallel")
    max_turns = args.get("max_turns")

    # Validate inputs
    if not tasks:
        return {"error": "Missing required parameter: tasks"}

    if not isinstance(tasks, list):
        return {"error": "tasks must be a list"}

    if len(tasks) == 0:
        return {"error": "tasks list cannot be empty"}

    if len(tasks) > MAX_SUBAGENTS:
        return {"error": f"Cannot run more than {MAX_SUBAGENTS} sub-agents at once"}

    if execution_mode not in ["parallel", "sequential"]:
        return {"error": "execution_mode must be 'parallel' or 'sequential'"}

    logger.info(f"Running {len(tasks)} sub-agents in {execution_mode} mode")

    start_time = time.time()

    try:
        if execution_mode == "parallel":
            # Execute all sub-agents in parallel using asyncio.gather
            results = await asyncio.gather(
                *[
                    _spawn_subagent(task, task_id, max_turns=max_turns)
                    for task_id, task in enumerate(tasks)
                ],
                return_exceptions=False  # Let exceptions be handled in _spawn_subagent
            )
        else:
            # Execute sub-agents sequentially
            results = []
            for task_id, task in enumerate(tasks):
                result = await _spawn_subagent(task, task_id, max_turns=max_turns)
                results.append(result)

        total_time = time.time() - start_time

        # Aggregate results into formatted output
        output = _aggregate_results(results, execution_mode, total_time)

        # Build metadata
        successful = [r for r in results if r["status"] == "success"]
        failed = [r for r in results if r["status"] == "error"]

        metadata = {
            "execution_summary": {
                "total_tasks": len(results),
                "successful": len(successful),
                "failed": len(failed),
                "execution_time_seconds": total_time,
                "execution_mode": execution_mode
            },
            "results": results
        }

        logger.info(
            f"Sub-agents completed: {len(successful)}/{len(results)} successful in {total_time:.2f}s"
        )

        return {
            "output": output,
            "metadata": metadata
        }

    except Exception as e:
        logger.error(f"Error running sub-agents: {e}")
        return {"error": f"Error running sub-agents: {str(e)}"}


# Tool definition for loader
RUN_SUBAGENTS_TOOL_DEFINITION = {
    "name": "run_subagents",
    "description": """Execute multiple tasks using independent sub-agents in parallel or sequentially.

Each sub-agent is a full OpusAgent instance with access to all tools (read, write, bash, etc.). Sub-agents cannot spawn additional sub-agents.

Use this tool when you need to:
- Analyze multiple files/logs in parallel
- Perform independent tasks simultaneously
- Break down complex work into parallel subtasks
- Process large datasets by splitting into chunks

Tasks can be simple prompts or structured objects with context:
- Simple: "Analyze error.log for critical issues"
- With file context: {"prompt": "Find errors", "context": {"type": "file", "path": "app.log"}}
- With URL context: {"prompt": "Summarize docs", "context": {"type": "url", "url": "https://..."}}
- With direct context: {"prompt": "Analyze this", "context": "direct text data..."}""",
    "parameters": {
        "type": "object",
        "properties": {
            "tasks": {
                "type": "array",
                "description": """List of tasks to execute. Each task can be:
- A string prompt: "Analyze file.log for errors"
- An object with prompt and context: {"prompt": "...", "context": "..." or {"type": "file", "path": "..."}}""",
                "items": {
                    "oneOf": [
                        {"type": "string"},
                        {
                            "type": "object",
                            "properties": {
                                "prompt": {
                                    "type": "string",
                                    "description": "The task for the sub-agent to execute"
                                },
                                "context": {
                                    "description": "Optional context: direct text string, or object with type='file'/path or type='url'/url",
                                    "oneOf": [
                                        {"type": "string"},
                                        {
                                            "type": "object",
                                            "properties": {
                                                "type": {
                                                    "type": "string",
                                                    "enum": ["file", "url", "files"]
                                                },
                                                "path": {"type": "string"},
                                                "url": {"type": "string"},
                                                "paths": {
                                                    "type": "array",
                                                    "items": {"type": "string"}
                                                }
                                            }
                                        }
                                    ]
                                }
                            },
                            "required": ["prompt"]
                        }
                    ]
                },
                "minItems": 1
            },
            "execution_mode": {
                "type": "string",
                "enum": ["parallel", "sequential"],
                "default": "parallel",
                "description": "Execute tasks in parallel (default) or sequentially"
            },
            "max_turns": {
                "type": "integer",
                "description": "Optional: Maximum iterations per sub-agent (default: 15)",
                "minimum": 1,
                "maximum": 50
            }
        },
        "required": ["tasks"]
    }
}
