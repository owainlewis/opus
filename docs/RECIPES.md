# Recipes

Recipes are **reusable prompt packages** that provide specialized expertise and context for specific tasks. Think of them as expert guides that help the AI agent excel at complex tasks.

## What are Recipes?

Recipes are **specialized skills** that:
- Package domain expertise into reusable prompts
- Provide comprehensive context and instructions
- Guide the agent through complex tasks effectively
- Work like expert advisors for specific scenarios
- Can be shared across teams and projects

**Key Philosophy:** Recipes leverage the AI agent's reasoning abilities by providing rich context and expert guidance, rather than constraining it with rigid step-by-step procedures.

## Quick Start

### Using a recipe

Ask the agent to use a recipe:

```bash
opus -m "Review src/app.py using the python-code-review recipe"
```

Or more naturally:

```
You: Can you review src/api.py for security issues?
Agent: I'll use the python-code-review recipe to conduct a thorough review...
```

The agent will:
1. Load the recipe (getting expert context and instructions)
2. Use its normal tools to complete the task
3. Follow the guidance from the recipe
4. Provide comprehensive results

## Recipe Format

Recipes use **YAML format** for simplicity and clarity.

### Basic Structure

```yaml
title: Recipe Name
description: What this recipe does and when to use it

instructions: You are an expert at [domain] with deep knowledge of [specific area].

parameters:
  param_name:
    type: string
    required: true
    description: What this parameter is for

  optional_param:
    type: string
    required: false
    default: default_value
    description: Optional parameter with default

prompt: |
  This is the actual task guidance that the agent receives.

  It can include:
  - Context and background knowledge
  - Step-by-step process to follow
  - Best practices and reminders
  - Output format specifications
  - Common pitfalls to avoid

  Use {{ param_name }} to reference parameters.
  The agent will use this guidance to complete the task effectively.
```

**Key Fields:**
- `title`: Recipe name
- `description`: What the recipe does
- `instructions`: (Optional) System-level role/persona - sets the context for who the agent is
- `parameters`: Input parameters
- `prompt`: Task-specific instructions and context

### Example Recipe

```yaml
title: Python Code Review
description: Comprehensive Python code review with security focus

instructions: You are a senior Python developer conducting thorough code reviews with a focus on security, performance, and maintainability.

parameters:
  file_path:
    type: string
    required: true
    description: Path to Python file to review

  focus:
    type: string
    required: false
    default: all
    description: Focus area (security, performance, style, all)

prompt: |
  Review the Python code at {{ file_path }} with focus on {{ focus }}.

  Check for:
  - PEP 8 compliance
  - Security vulnerabilities
  - Performance issues
  - Test coverage

  Provide specific feedback with line numbers and code examples.
```

## How It Works

### 1. Agent Loads Recipe

When you ask the agent to use a recipe:

```
You: "Review my API using the api-spec-review recipe"
```

### 2. Recipe Provides Context

The agent loads the recipe and receives:
- Expert context about API design
- Comprehensive review checklist
- Best practices to apply
- Output format to follow

### 3. Agent Completes Task

The agent then:
- Reads the necessary files
- Analyzes using the recipe's guidance
- Uses all available tools (Read, Grep, Bash, etc.)
- Provides thorough, expert-level results

### 4. Results

You get comprehensive output following the recipe's structure:
- Systematic analysis
- Specific findings with examples
- Actionable recommendations
- Consistent format

## Recipe Parameters

### Defining Parameters

Parameters make recipes reusable:

```yaml
parameters:
  file_path:
    type: string           # string, number, or boolean
    required: true         # Must be provided
    description: Path to file to review

  severity:
    type: string
    required: false        # Optional
    default: medium        # Used if not provided
    description: Minimum severity level
```

### Using Parameters in Prompts

Reference parameters with `{{ parameter_name }}`:

```yaml
prompt: |
  Review the file at {{ file_path }}.
  Focus on issues with {{ severity }} severity or higher.

  If {{ severity }} is "high", only report critical issues.
```

### Providing Parameters

When using a recipe:

```bash
# Explicit parameters
opus -m "Run python-code-review recipe with file_path=src/app.py and focus=security"

# Natural language (agent extracts params)
opus -m "Review src/app.py using the code review recipe, focus on security"
```

## Built-in Example Recipes

### Python Code Review

Expert Python code review with focus on:
- PEP 8 style compliance
- Security vulnerabilities
- Performance optimization
- Test coverage
- Best practices

**Usage:**
```bash
opus -m "Review src/app.py using python-code-review recipe"
opus -m "Security review of src/api.py using python-code-review recipe with focus=security"
```

### API Specification Review

Comprehensive API design review covering:
- REST principles and resource design
- Security and authentication
- Documentation quality
- Consistency and standards
- Performance considerations

**Usage:**
```bash
opus -m "Review api/openapi.yaml using api-spec-review recipe"
```

### Weekly Engineering Report

Generate thorough weekly engineering reports including:
- Key achievements and metrics
- Work in progress
- Blockers and risks
- Team highlights
- Next week's priorities

**Usage:**
```bash
opus -m "Generate weekly report using weekly-report recipe for backend team"
opus -m "Create a weekly report for last week using the weekly-report recipe"
```

## Creating Your Own Recipes

### 1. Create a YAML file

```bash
touch ~/.opus/recipes/my-recipe.yaml
```

### 2. Define the recipe

```yaml
title: My Custom Recipe
description: What this recipe does

parameters:
  target:
    type: string
    required: true
    description: What to target

prompt: |
  You are an expert at [domain].

  Your task: [describe the task]
  Target: {{ target }}

  Process:
  1. [Step or consideration]
  2. [Step or consideration]
  3. [Step or consideration]

  Provide:
  - [Expected output 1]
  - [Expected output 2]

  Best practices:
  - [Important reminder]
  - [Common pitfall to avoid]
```

### 3. Use it

```bash
opus -m "Use my-recipe with target=foo"
```

## Recipe Design Best Practices

### 1. Separate Role from Task

Use `instructions` for the role/persona and `prompt` for the task:

❌ **Don't** mix role and task:
```yaml
prompt: |
  You are a senior security engineer reviewing API security.

  Review the API at {{ api_path }} and check for...
```

✅ **Do** separate them:
```yaml
instructions: You are a senior security engineer with expertise in API security and OWASP Top 10 vulnerabilities.

prompt: |
  Review the API at {{ api_path }}.

  Check for:
  - Authentication mechanisms
  - Input validation
  - Rate limiting
```

**Why?** This gives the LLM clearer context about its role while keeping task instructions focused.

### 2. Rich Context Over Rigid Steps

❌ **Don't** create rigid procedures:
```yaml
prompt: |
  Step 1: Run this command
  Step 2: Check this file
  Step 3: Run that command
```

✅ **Do** provide rich context:
```yaml
instructions: You are an expert at reviewing API security.

prompt: |
  Key areas to examine:
  - Authentication mechanisms
  - Input validation
  - Rate limiting

  Look for common vulnerabilities like...
  Provide specific recommendations with examples...
```

### 3. Provide Expert Knowledge

Include domain expertise the agent should know:

```yaml
prompt: |
  Python security best practices:
  - Never use pickle.loads() on untrusted data
  - Always use parameterized queries for SQL
  - Validate and sanitize all user input

  When reviewing code at {{ file_path }}, check for...
```

### 4. Specify Output Format

Help the agent structure its response:

```yaml
prompt: |
  Provide your review in this format:

  ## Summary
  [Overall assessment]

  ## Critical Issues
  [Must-fix items with line numbers]

  ## Recommendations
  [Suggestions with examples]
```

### 5. Include Examples

Show what good looks like:

```yaml
prompt: |
  When providing feedback, use this format:

  - `src/app.py:42` - Issue description
    ```python
    # Current (problematic)
    password = request.args.get('password')

    # Suggested
    password = request.form.get('password')
    ```
```

### 6. Make it Parameterized

Enable reuse with parameters:

```yaml
parameters:
  language:
    type: string
    default: python
    description: Programming language

prompt: |
  Review {{ language }} code focusing on {{ language }}-specific best practices...
```

### 7. Add Context About Tools

Guide the agent on what tools to use:

```yaml
prompt: |
  Process:
  1. Use Read to examine {{ file_path }}
  2. Use Grep to search for security patterns
  3. Use Bash to run linters if needed

  Analyze the results and provide recommendations...
```

## Use Cases

### Development

- **Code Review:** `python-code-review`, `javascript-code-review`, `go-code-review`
- **Architecture Review:** `architecture-review`, `design-doc-review`
- **API Design:** `api-spec-review`, `graphql-schema-review`
- **Security Audit:** `security-audit`, `dependency-review`
- **Performance Analysis:** `performance-review`, `database-optimization`

### Operations & SRE

- **Incident Response:** `incident-triage`, `postmortem-analysis`
- **Infrastructure Review:** `terraform-review`, `kubernetes-config-review`
- **Monitoring Setup:** `metrics-review`, `alert-configuration`

### Documentation & Process

- **Documentation Review:** `readme-review`, `api-docs-review`
- **Process Documentation:** `runbook-creation`, `onboarding-guide`

### Reporting & Analysis

- **Status Reports:** `weekly-report`, `sprint-summary`, `quarterly-review`
- **Metrics Analysis:** `metrics-dashboard`, `trend-analysis`
- **Technical Debt:** `tech-debt-audit`, `refactoring-plan`

## Sharing Recipes

### Personal Recipes

Store in `~/.opus/recipes/`:

```bash
~/.opus/recipes/
├── python-code-review.yaml
├── api-spec-review.yaml
└── my-custom-recipe.yaml
```

### Team Recipes

Share via Git repository:

```bash
# Team repository
company-recipes/
├── code-review/
│   ├── python-code-review.yaml
│   ├── javascript-code-review.yaml
│   └── go-code-review.yaml
├── api-design/
│   ├── api-spec-review.yaml
│   └── graphql-review.yaml
└── reports/
    └── weekly-report.yaml

# Clone to your recipes directory
git clone git@github.com:company/recipes.git ~/.opus/recipes/company

# Use team recipes
opus -m "Use company/code-review/python-code-review recipe"
```

### Recipe Collections

Create themed collections:

```bash
~/.opus/recipes/
├── security/          # Security-focused recipes
├── performance/       # Performance optimization
├── best-practices/    # Code quality and standards
└── reporting/         # Status and metrics reports
```

## Advanced Features

### Conditional Logic in Prompts

Use parameters to change behavior:

```yaml
parameters:
  mode:
    type: string
    default: standard
    description: Review mode (quick, standard, thorough)

prompt: |
  Review mode: {{ mode }}

  {% if mode == "quick" %}
  Focus only on critical issues.
  {% elif mode == "thorough" %}
  Conduct comprehensive analysis of all aspects.
  {% else %}
  Balance thoroughness with efficiency.
  {% endif %}
```

### Multi-Language Recipes

Support multiple languages:

```yaml
parameters:
  language:
    type: string
    required: true
    description: Programming language (python, javascript, go, rust)

prompt: |
  Review {{ language }} code at {{ file_path }}.

  Apply {{ language }}-specific best practices:
  {% if language == "python" %}
  - PEP 8 style guide
  - Type hints
  {% elif language == "javascript" %}
  - ESLint rules
  - Async/await patterns
  {% elif language == "go" %}
  - gofmt formatting
  - Error handling patterns
  {% endif %}
```

## Troubleshooting

### Recipe Not Found

```
Error: Recipe not found: my-recipe
```

**Solutions:**
- Check file exists: `ls ~/.opus/recipes/my-recipe.yaml`
- Check filename matches (case-sensitive)
- Ensure file has `.yaml` or `.yml` extension

### Missing Required Parameter

```
Error: Missing required parameter: file_path
```

**Solution:** Provide the parameter:
```bash
opus -m "Use recipe with file_path=src/app.py"
```

### Parameter Type Mismatch

```
Error: Parameter 'count' must be a number
```

**Solution:** Ensure parameter matches expected type:
```yaml
parameters:
  count:
    type: number    # Must provide numeric value
```

## Migration from Old Format

If you have legacy Markdown recipes (step-by-step format), they still work but are deprecated.

**Old format (Markdown, step-by-step):**
```markdown
# Recipe Name

## Step 1: Do this
```bash
command
```

## Step 2: Do that
Instructions...
```

**New format (YAML, prompt-centric):**
```yaml
title: Recipe Name
description: What it does

prompt: |
  Context and expert guidance...
  Process to follow...
  Use your tools to complete the task.
```

The new format is **simpler**, **more flexible**, and **better leverages AI reasoning**.

## Tips

### 1. Start Simple

Begin with basic recipes and add complexity as needed:

```yaml
title: Simple Code Review
description: Basic code review

parameters:
  file_path:
    type: string
    required: true
    description: File to review

prompt: |
  Review {{ file_path }} for common issues.
  Provide specific feedback with line numbers.
```

### 2. Iterate Based on Results

Run the recipe, see what works, refine the prompt:
- Add more context if agent misses things
- Clarify output format if results are messy
- Add examples if agent doesn't follow patterns

### 3. Test with Different Inputs

Try your recipe with various parameters:
```bash
opus -m "Use recipe with file_path=small.py"
opus -m "Use recipe with file_path=large.py"
opus -m "Use recipe with file_path=complex.py"
```

### 4. Document Your Recipes

Add helpful descriptions:

```yaml
title: Python Security Audit
description: |
  Comprehensive security review of Python code.

  Use this for:
  - Security-sensitive code
  - Production systems
  - User-facing APIs

  Focuses on OWASP Top 10 vulnerabilities.
```

### 5. Build a Library

Create recipes for recurring tasks:
- Code reviews (per language)
- Architecture reviews
- Security audits
- Documentation reviews
- Weekly reports
- Onboarding guides

## Related Documentation

- [Configuration](./CONFIGURATION.md) - Configuring Opus
- [Tools Guide](./TOOLS.md) - Creating custom tools

## Community Recipes

Share your recipes! Create a PR to add your recipe to the community collection:

https://github.com/your-username/opus-recipes

**Popular community recipes:**
- Database migration review
- Dockerfile optimization
- Kubernetes manifest review
- CI/CD pipeline audit
- Dependency security scan
- Technical design doc review
- Architecture decision record (ADR) template
