# Tools

Tools are the actions that Opus can take to complete tasks. Opus comes with several built-in tools for common operations, and you can create custom tools to integrate your own scripts and services.

## Built-in Tools

Opus includes these built-in tools that are always available:

**bash** - Execute shell commands
The AI can run shell commands to perform system operations, manage files, or run other programs. You can require approval for bash commands to maintain control over what gets executed.

**file_read** - Read files from disk
Reads file contents so the AI can analyze code, configuration files, logs, or any other text files.

**file_write** - Create or overwrite files
Creates new files or completely replaces existing files with new content. Useful for generating code, configuration, or documentation.

**file_edit** - Edit existing files
Makes targeted changes to existing files by finding and replacing specific text. More precise than rewriting entire files.

**fetch_url** - Fetch content from URLs
Downloads web pages and converts them to markdown for analysis. Useful for reading documentation, fetching data, or checking endpoints.

**run_recipe** - Execute recipes
Loads and executes recipe templates that provide specialized expertise for specific tasks.

**get_current_time** - Get current date and time
Returns the current date and time, which helps the AI work with time-sensitive operations or include timestamps in output.

**run_subagents** - Spawn parallel agents
Creates multiple independent AI agents that can work on separate tasks in parallel. Useful for analyzing multiple files, processing batches, or doing parallel research.

All built-in tools are enabled by default. You can disable them or configure approval settings in your config file.

## Configuring Tools

Tools can be configured in your config file to control whether they're enabled and whether they require user approval:

```yaml
tools:
  bash:
    enabled: true
    approval: true  # Require approval before running

  file_read:
    enabled: true
    approval: false  # Auto-approve (safe operation)

  file_write:
    enabled: true
    approval: true  # Ask before creating/overwriting files
```

When a tool requires approval, Opus will show you what the AI wants to do and wait for confirmation before executing it. This gives you control over potentially risky operations.

## Creating Custom Tools

You can create custom tools to make your own scripts and services available to the AI. A custom tool is defined in a YAML file that describes the tool's name, what it does, and how to call it.

Here's a complete example:

```yaml
# tools/deploy.yaml
name: deploy_service
description: Deploy a service to a specific environment

script: ./scripts/deploy.sh {service} {environment}

parameters:
  type: object
  properties:
    service:
      type: string
      enum: ["api", "worker", "frontend"]
      description: Which service to deploy
    environment:
      type: string
      enum: ["staging", "production"]
      description: Target environment
  required:
    - service
    - environment

timeout: 300
```

The key parts are:

**name** - The tool's identifier. This is how the AI refers to the tool.

**description** - A clear explanation of what the tool does. The AI uses this to understand when to use the tool.

**script** - The command to execute. Use `{parameter_name}` placeholders for parameters that will be filled in when the tool runs.

**parameters** - A JSON Schema definition of the tool's inputs. This tells the AI what information it needs to provide when calling the tool.

**timeout** - How long to wait (in seconds) before canceling a long-running tool execution.

## Using Custom Tools

After creating a tool definition, reference it in your config file:

```yaml
tools:
  deploy_service:
    enabled: true
    approval: true
    source: ./tools/deploy.yaml
```

The `source` path can be relative (to your config file) or absolute. Once configured, the AI can use your custom tool just like any built-in tool.

For example, you might ask: "Deploy the api service to staging" and the AI will understand it should use the deploy_service tool with the appropriate parameters.

## Parameter Schema

The parameters section uses JSON Schema to define what inputs the tool accepts. This helps the AI understand what values are valid and required.

**Basic types:**
```yaml
parameters:
  type: object
  properties:
    name:
      type: string
      description: User's name
    age:
      type: number
      description: User's age
    active:
      type: boolean
      description: Whether the account is active
```

**Required vs optional:**
```yaml
parameters:
  type: object
  properties:
    required_param:
      type: string
      description: This must be provided
    optional_param:
      type: string
      default: "default value"
      description: This is optional
  required:
    - required_param
```

**Enums for specific choices:**
```yaml
parameters:
  type: object
  properties:
    environment:
      type: string
      enum: ["dev", "staging", "production"]
      description: Target environment
```

Using enums is particularly helpful because it constrains the AI to valid values and helps it understand the available options.

## Script Execution

The script can be any executable command. Common patterns:

**Shell script:**
```yaml
script: ./scripts/backup.sh {database} {destination}
```

**Python script:**
```yaml
script: python ./scripts/analyze.py --input {input_file} --format {format}
```

**Direct command:**
```yaml
script: curl -X POST https://api.example.com/deploy -d '{"service": "{service}"}'
```

**uv inline script:**
```yaml
script: uv run fetch_logs.py {app} {from_time} {to_time}
```

Parameters are substituted directly into the script command. The AI fills in the `{parameter_name}` placeholders with actual values when it calls the tool.

## Tool Security

Be careful with tools that execute arbitrary commands or access sensitive systems. Use approval settings to maintain control:

```yaml
tools:
  # Safe tools - auto-approve
  file_read:
    approval: false

  # Potentially risky - require approval
  bash:
    approval: true

  deploy_service:
    approval: true
```

When approval is enabled, you'll see exactly what the tool is going to do before it runs. You can approve, reject, or modify the request.

## Example Custom Tools

The `examples/tools/` directory contains example tool definitions:

**Log Fetching** (`examples/tools/fetch-logs.yaml`)
Demonstrates a tool that fetches application logs from a logging service. Shows how to use enums to constrain parameter values and how to set custom timeouts.

**UV Inline Script** (`examples/tools/uv-inline-script.yaml`)
Shows how to run Python scripts using uv, which lets you specify dependencies inline in the script file.

## Tips for Creating Tools

Keep the description clear and specific. The AI uses this to decide when to use the tool, so explain exactly what it does and when it's appropriate.

Use enums to constrain parameters to valid values. This prevents errors and helps the AI understand the available options.

Set reasonable timeouts. Quick operations might need 30 seconds, while deployments might need several minutes. The default timeout is 30 seconds if not specified.

Test your tools manually first. Make sure the script works correctly before giving it to the AI. This helps you catch issues with parameter substitution or command syntax.

Consider approval settings based on risk. Read operations can usually be auto-approved, while write operations or deployments should probably require approval.

## Advanced: Python Callables

In addition to shell scripts, you can create tools as Python functions. This is more advanced but gives you more control over tool behavior. The tool definition references a Python file and function name instead of a script command. See the source code for built-in tools like `file_read.py` for examples of this approach.
