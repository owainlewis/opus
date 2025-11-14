# Sub-Agent System

The sub-agent system allows Opus to execute multiple independent tasks in parallel or sequentially using fully-capable agent instances. This is particularly useful for log analysis, code review, and any scenario where work can be split into parallel subtasks.

## Overview

**Tool Name:** `run_subagents`

**Purpose:** Execute N independent tasks using separate OpusAgent instances, each with full access to all tools.

**Key Features:**
- ✅ Parallel or sequential execution
- ✅ Full agent capabilities per sub-agent (Read, Grep, Bash, etc.)
- ✅ Flexible context passing (files, URLs, or direct text)
- ✅ Automatic result aggregation
- ✅ Graceful error handling (failed tasks don't block others)
- ✅ Recursion prevention (sub-agents can't spawn more sub-agents)

## When to Use

### Ideal Use Cases
- **Log analysis**: Analyze multiple log files in parallel
- **Code review**: Review multiple files/modules simultaneously
- **Data processing**: Process datasets by splitting into chunks
- **Multi-file search**: Search across multiple files concurrently
- **Parallel testing**: Test multiple scenarios simultaneously

### Not Recommended For
- Single, indivisible tasks
- Tasks that require shared state
- Simple queries that don't benefit from parallelization

## Tool Interface

### Basic Usage

#### Simple Prompts
```python
{
    "tasks": [
        "Analyze error.log and count ERROR lines",
        "Check access.log for suspicious activity",
        "Review app.log for performance issues"
    ],
    "execution_mode": "parallel"  # or "sequential"
}
```

#### Structured Tasks with Context

##### File Context
```python
{
    "tasks": [
        {
            "prompt": "Find all critical errors and their timestamps",
            "context": {"type": "file", "path": "/var/log/app/error.log"}
        },
        {
            "prompt": "Identify slow requests (>5s)",
            "context": {"type": "file", "path": "/var/log/app/api.log"}
        }
    ]
}
```

##### URL Context
```python
{
    "tasks": [
        {
            "prompt": "Summarize the key features",
            "context": {"type": "url", "url": "https://example.com/docs"}
        }
    ]
}
```

##### Direct Text Context
```python
{
    "tasks": [
        {
            "prompt": "Count how many errors are in this log",
            "context": "ERROR: Connection failed\nINFO: Retry...\nERROR: Timeout"
        }
    ]
}
```

##### Multiple Files
```python
{
    "tasks": [
        {
            "prompt": "Review all these files for security issues",
            "context": {
                "type": "files",
                "paths": ["auth.py", "db.py", "api.py"]
            }
        }
    ]
}
```

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `tasks` | Array | Yes | - | List of tasks (strings or objects with prompt/context) |
| `execution_mode` | String | No | `"parallel"` | Execute tasks in parallel or sequential |
| `max_turns` | Integer | No | 15 | Maximum iterations per sub-agent |

### Response Format

```python
{
    "output": "Formatted summary of all sub-agent results",
    "metadata": {
        "execution_summary": {
            "total_tasks": 3,
            "successful": 3,
            "failed": 0,
            "execution_time_seconds": 12.4,
            "execution_mode": "parallel"
        },
        "results": [
            {
                "task_id": 0,
                "prompt": "Analyze error.log...",
                "status": "success",
                "output": "Found 15 errors...",
                "execution_time": 4.2
            },
            // ... more results
        ]
    }
}
```

## Configuration

Add to your `config.yaml`:

```yaml
# Sub-agent settings
subagent_max_turns: 15       # Max iterations per sub-agent (vs 25 for parent)
subagent_timeout: 300        # 5 minutes per sub-agent

tools:
  run_subagents:
    enabled: true
    approval: false  # Auto-approve for efficiency
```

## Examples

### Example 1: Parallel Log Analysis

```bash
opus -m "Use run_subagents to analyze app.log, api.log, and worker.log in parallel.
For each, count errors and identify the most critical issue."
```

The agent will:
1. Detect multiple independent analysis tasks
2. Call `run_subagents` with 3 tasks
3. Each sub-agent reads its log file and analyzes it
4. Results are aggregated and summarized

### Example 2: Code Review

```bash
opus -m "Review src/auth.py, src/db.py, and src/api.py for security vulnerabilities.
Use sub-agents to review them in parallel."
```

### Example 3: Sequential Data Processing

```python
await execute_run_subagents({
    "tasks": [
        "Process batch 1: records 0-1000",
        "Process batch 2: records 1000-2000",
        "Process batch 3: records 2000-3000"
    ],
    "execution_mode": "sequential",  # Process in order
    "max_turns": 10  # Simple processing tasks
})
```

## Architecture

### How It Works

1. **Tool Invocation**: Parent agent calls `run_subagents` with task list
2. **Context Preparation**: Files/URLs are loaded into text context
3. **Agent Spawning**: N independent `OpusAgent` instances created
4. **Parallel Execution**: Tasks run via `asyncio.gather()` (or sequentially)
5. **Result Aggregation**: All results combined into formatted summary
6. **Return to Parent**: Parent agent receives aggregated results

### Sub-Agent Constraints

- **Max iterations**: Configurable, defaults to 15 (vs parent's 25)
- **No recursion**: `run_subagents` tool is filtered out for sub-agents
- **Timeout**: 5 minutes per sub-agent (configurable)
- **Isolation**: Each sub-agent has independent message history
- **Full tools**: Access to all other tools (Read, Bash, Grep, etc.)

### Context Passing

Sub-agents receive context via **initial message history**:

```python
[
    {"role": "user", "content": "Here is the context: <file contents>"},
    {"role": "user", "content": "<actual task prompt>"}
]
```

This approach:
- Provides natural conversation flow
- Doesn't consume tool call quota
- Allows large context (within model limits)

## Performance Considerations

### Parallel Execution
- **Best for**: Independent tasks without dependencies
- **Throughput**: N tasks complete in ~time of slowest task
- **Resource usage**: N concurrent LLM API calls

### Sequential Execution
- **Best for**: Dependent tasks or rate-limited scenarios
- **Throughput**: Sum of all task times
- **Resource usage**: 1 LLM API call at a time

### Token Usage
- Each sub-agent is a full conversation (system prompt + tools + messages)
- Large contexts count against each sub-agent's token limit
- Consider breaking very large files into smaller chunks

## Troubleshooting

### "Sub-agent timed out"
- Increase `subagent_timeout` in config
- Reduce `max_turns` for simpler tasks
- Break complex tasks into smaller pieces

### "Tool 'run_subagents' not found"
- Ensure `run_subagents` is in `BUILTIN_TOOLS` (should be by default)
- Check config doesn't explicitly disable it
- Verify you're using latest version of Opus

### Sub-agents can't spawn more sub-agents
- **This is intentional** to prevent infinite recursion
- Sub-agents automatically have `run_subagents` filtered out
- Design your tasks to be executable by a single agent level

## Implementation Details

### Files Modified
- `src/opus/tools/run_subagents.py` - Core tool implementation
- `src/opus/agent.py` - Sub-agent support (`is_subagent`, `initial_messages`)
- `src/opus/tools/loader.py` - Tool registration
- `src/opus/config.py` - Built-in tool list + config options

### Key Functions
- `execute_run_subagents(args)` - Main entry point
- `_spawn_subagent(task_spec)` - Create and run one sub-agent
- `_prepare_context(context_spec)` - Load files/URLs into text
- `_aggregate_results(results)` - Format summary output

## See Also

- [Tool Development Guide](./tools.md)
- [Configuration Reference](./configuration.md)
- [Examples](../examples/)
