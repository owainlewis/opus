# Sub-agents

The sub-agent system lets Opus split work into multiple independent tasks that can run in parallel. This is useful when you have several things that can be done at the same time, like analyzing multiple log files or reviewing several code modules.

## What are Sub-agents?

A sub-agent is a separate instance of Opus that handles one specific task. Each sub-agent has access to all the same tools as the main agent (reading files, running commands, etc.) and can work independently. The main agent can spawn multiple sub-agents, let them work in parallel, and then collect all their results.

For example, if you need to analyze three log files for errors, the main agent can spawn three sub-agents, give each one a log file to analyze, and get all three analyses back at once instead of doing them one at a time.

## When to Use Sub-agents

Sub-agents are most useful when you have multiple independent tasks that don't depend on each other.

Good use cases include analyzing multiple log files in parallel, reviewing several code files at once, processing data in chunks, searching across multiple files simultaneously, or testing different scenarios in parallel.

Sub-agents are not helpful for single tasks that can't be broken down, for tasks that share state or need to coordinate with each other, or for simple operations that are already fast.

## Using Sub-agents

You can ask Opus to use sub-agents in natural language:

```bash
opus -m "Analyze error.log, access.log, and api.log in parallel and tell me the most critical issues"
```

Opus will recognize that these are independent tasks and automatically use the `run_subagents` tool to process them in parallel.

You can also be explicit about using sub-agents:

```bash
opus -m "Use sub-agents to review src/auth.py, src/db.py, and src/api.py for security issues"
```

## How It Works

When Opus uses sub-agents, it creates separate agent instances for each task. Each sub-agent gets its own task description and any necessary context (like file contents or data to analyze). The sub-agents run independently, using all the same tools available to the main agent. When all sub-agents finish, the main agent collects their results and presents a combined summary.

By default, sub-agents run in parallel to save time. You can also request sequential execution if tasks need to run in a specific order, though this is less common.

## Configuration

You can configure sub-agent behavior in your config file:

```yaml
# Maximum conversation turns for each sub-agent
subagent_max_turns: 15

# Timeout for sub-agent execution (seconds)
subagent_timeout: 300

tools:
  run_subagents:
    enabled: true
    approval: false  # Auto-approve for efficiency
```

Sub-agents have a lower turn limit (15 by default) compared to the main agent (25 by default) since they typically handle simpler, focused tasks. The timeout prevents any single sub-agent from running too long.

## Examples

**Parallel log analysis:**
```bash
opus -m "Analyze app.log, api.log, and worker.log in parallel.
For each, count errors and identify the most critical issue."
```

Each log file gets its own sub-agent. All three analyses happen at the same time, and you get a combined report with findings from all three logs.

**Code review:**
```bash
opus -m "Review src/auth.py, src/db.py, and src/api.py for security vulnerabilities.
Use sub-agents to review them in parallel."
```

Each file gets reviewed independently by its own sub-agent, all running at the same time.

**Data processing:**
```bash
opus -m "Process these three data files in parallel: data1.csv, data2.csv, data3.csv.
Calculate summary statistics for each."
```

Each data file gets processed by a separate sub-agent.

## Context Passing

Sub-agents can receive context in several ways. You can give them files to read by specifying file paths. You can provide URLs that they should fetch. Or you can pass text data directly in the task description.

The main agent handles loading files or URLs and passes the content to sub-agents as part of their initial context. This means the sub-agent starts with the information it needs already available.

## Limitations

Sub-agents cannot spawn more sub-agents. This prevents infinite recursion and keeps the system manageable. If a sub-agent tries to use the `run_subagents` tool, it won't have access to it.

Each sub-agent runs independently and cannot communicate with other sub-agents. They don't share state or coordinate with each other. This is by design since sub-agents are meant for truly independent tasks.

Sub-agents have a conversation limit (15 turns by default) and a timeout (5 minutes by default). This prevents any single sub-agent from consuming too many resources.

## Performance Considerations

Running sub-agents in parallel means making multiple LLM API calls at the same time. This is faster than sequential execution, but uses more API quota and costs more tokens overall. Each sub-agent has its own conversation with the full system prompt and tool definitions, so token usage scales with the number of sub-agents.

For example, if three sub-agents each use 5,000 tokens, that's 15,000 tokens total. Sequential execution would use roughly the same amount but take three times as long. Parallel execution trades money (tokens) for time (speed).

Keep this in mind when deciding whether to use sub-agents. For large numbers of sub-agents (10+), the token cost can add up quickly.

## Sequential Execution

While parallel execution is the default, you can request sequential execution if tasks need to happen in order:

```bash
opus -m "Process these files sequentially: first validate data.json,
then transform it with transform.py, then upload the result"
```

Sequential execution is useful when later tasks depend on earlier ones, or when you want to limit API rate usage.

## Error Handling

If a sub-agent fails or times out, the other sub-agents continue running. The main agent collects results from successful sub-agents and reports which ones failed. This means one failure doesn't block the entire operation.

You'll get partial results from the sub-agents that succeeded, along with information about any that failed.

## Tips

Start with a clear description of each independent task. The clearer you are about what each sub-agent should do, the better results you'll get.

Use sub-agents when tasks truly are independent. If tasks need to share information or build on each other, sequential execution by the main agent is usually better.

Be aware of token costs with large numbers of sub-agents. Three to five sub-agents is usually fine, but ten or twenty can get expensive.

Consider timeouts for long-running tasks. If sub-agents might take a while (like analyzing large files), increase the `subagent_timeout` setting.

Remember that sub-agents can't spawn more sub-agents. Design your tasks so they can be completed by a single level of sub-agents.
