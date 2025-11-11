# Tool Parameter Schema Guide

This guide explains how to use JSON Schema to define parameters for custom Opus tools.

## Why Use JSON Schema?

JSON Schema provides **strong guidance to the LLM** about valid parameter values. This helps the LLM:

1. **Know valid options** - When you use `enum`, the LLM knows exactly what values are acceptable
2. **Prompt users correctly** - The LLM can ask users to choose from specific options
3. **Validate inputs** - Invalid values are caught before execution
4. **Self-document** - Tools become more discoverable and easier to use

## Using Enums

Enums constrain a parameter to a specific set of values.

### Example: Application Names

Without enum (bad):
```yaml
parameters:
  type: object
  properties:
    app:
      type: string
      description: Application name (e.g., "api", "worker", "scheduler")
```

**Problem:** The LLM doesn't know which apps exist. If the user says "fetch logs for the API", the LLM might guess "API", "api-service", "api", etc.

With enum (good):
```yaml
parameters:
  type: object
  properties:
    app:
      type: string
      enum: ["api", "worker", "scheduler", "frontend", "database"]
      description: Application name to fetch logs from
```

**Benefit:** The LLM knows exactly which apps exist and can prompt: "Which app? (api, worker, scheduler, frontend, database)"

## Other Useful JSON Schema Features

### Default Values

Provide sensible defaults for optional parameters:

```yaml
parameters:
  type: object
  properties:
    limit:
      type: integer
      default: 100
      description: Maximum number of logs to return
    format:
      type: string
      enum: ["json", "text", "csv"]
      default: "json"
      description: Output format
```

### Number Constraints

Constrain numeric values:

```yaml
parameters:
  type: object
  properties:
    port:
      type: integer
      minimum: 1024
      maximum: 65535
      description: Port number
    timeout:
      type: number
      minimum: 0.1
      maximum: 300
      description: Timeout in seconds
```

### String Patterns

Use regex patterns for validation:

```yaml
parameters:
  type: object
  properties:
    email:
      type: string
      pattern: "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
      description: Email address
    version:
      type: string
      pattern: "^v?\\d+\\.\\d+\\.\\d+$"
      description: Semantic version (e.g., "1.2.3" or "v1.2.3")
```

### Boolean Flags

```yaml
parameters:
  type: object
  properties:
    verbose:
      type: boolean
      default: false
      description: Enable verbose output
    follow:
      type: boolean
      default: false
      description: Follow log output in real-time
```

## Real-World Example

Here's a complete example for a deployment tool:

```yaml
name: deploy_service
description: Deploy a service to a specific environment

script: ./scripts/deploy.sh {service} {environment} {version} {--rollback}

parameters:
  type: object
  properties:
    service:
      type: string
      enum: ["api", "worker", "frontend", "database-migrations"]
      description: Service name to deploy

    environment:
      type: string
      enum: ["dev", "staging", "production"]
      description: Target environment

    version:
      type: string
      pattern: "^v?\\d+\\.\\d+\\.\\d+$"
      description: Version to deploy (semantic version)

    rollback:
      type: boolean
      default: false
      description: Rollback to previous version instead of deploying

    wait_for_health:
      type: boolean
      default: true
      description: Wait for service to become healthy before returning

    timeout:
      type: integer
      minimum: 30
      maximum: 600
      default: 300
      description: Deployment timeout in seconds

  required:
    - service
    - environment
    - version
```

## Benefits in Practice

### Without Enums

**User:** "Deploy the API to prod"
**LLM:** "Deploying to production..." ❌ (guesses "prod" vs "production")
**Result:** Error - invalid environment name

### With Enums

**User:** "Deploy the API to prod"
**LLM:** "I'll deploy the api service. Which environment? (dev, staging, production)"
**User:** "production"
**LLM:** "Deploying..." ✅
**Result:** Success!

## Best Practices

1. **Always use enums** for finite sets of values (environments, services, formats, etc.)
2. **Provide defaults** for optional parameters
3. **Use patterns** to validate formats (versions, emails, URLs, etc.)
4. **Add constraints** to prevent invalid values (port ranges, timeouts, etc.)
5. **Write clear descriptions** - they're shown to the LLM and help guide correct usage

## More Information

- [JSON Schema Reference](https://json-schema.org/understanding-json-schema/)
- [JSON Schema Validation](https://json-schema.org/understanding-json-schema/reference/string.html)
