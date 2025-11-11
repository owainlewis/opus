# How to Use Recipes - Practical Guide

## Quick Start

### 1. Use an Existing Recipe

```bash
# Basic usage
opus -m "Review my code using the python-code-review recipe"

# With specific file
opus -m "Review src/app.py using the python-code-review recipe"

# With parameters
opus -m "Review src/api.py with the python-code-review recipe, focus on security"
```

### 2. See Available Recipes

```bash
ls ~/.opus/recipes/
```

Current recipes:
- `python-code-review.yaml` - Python code review
- `api-spec-review.yaml` - API design review
- `weekly-report.yaml` - Engineering reports

## Creating Your First Recipe

### Example: JavaScript Code Review

```bash
# Create the file
cat > ~/.opus/recipes/javascript-review.yaml << 'EOF'
title: JavaScript Code Review
description: Review JavaScript/TypeScript code for quality and best practices

parameters:
  file_path:
    type: string
    required: true
    description: Path to JS/TS file to review

  framework:
    type: string
    required: false
    default: none
    description: Framework (react, vue, angular, none)

prompt: |
  Review the JavaScript code at {{ file_path }}.
  Framework: {{ framework }}

  ## What to Check

  ### Code Quality
  - ESLint compliance
  - Consistent naming (camelCase for variables, PascalCase for components)
  - Proper use of const/let (avoid var)
  - Arrow functions vs function declarations

  ### React-Specific (if framework is react)
  - Proper hook usage (useEffect, useState, etc.)
  - Component composition
  - Props validation
  - Key props in lists

  ### Common Issues
  - Equality checks (=== vs ==)
  - Async/await vs promises
  - Error handling in async code
  - Memory leaks (event listeners, timers)

  ### Security
  - XSS vulnerabilities (dangerouslySetInnerHTML)
  - Eval usage
  - User input sanitization

  ## Process

  1. Read the file at {{ file_path }}
  2. Check for the issues above
  3. Provide specific line numbers
  4. Show code examples for fixes

  ## Output Format

  ### Critical Issues
  - Security vulnerabilities
  - Bugs that could cause crashes

  ### Important Improvements
  - Best practice violations
  - Performance issues

  ### Minor Suggestions
  - Style improvements
  - Code organization

  Be specific and constructive!
EOF
```

### Use Your New Recipe

```bash
opus -m "Review src/App.jsx using javascript-review recipe with framework=react"
```

## Common Patterns

### Pattern 1: Language-Specific Code Review

```yaml
title: [Language] Code Review
description: Review [Language] code

parameters:
  file_path:
    type: string
    required: true
    description: File to review

prompt: |
  Review {{ file_path }} for:
  - Language-specific best practices
  - Security issues
  - Performance problems
  - Testing coverage

  Provide line numbers and examples.
```

### Pattern 2: Specification Review

```yaml
title: [Type] Spec Review
description: Review specifications

parameters:
  spec_path:
    type: string
    required: true
    description: Path to spec file

prompt: |
  Review the specification at {{ spec_path }}.

  Check for:
  - Completeness
  - Consistency
  - Clarity
  - Standards compliance

  Provide specific recommendations.
```

### Pattern 3: Report Generation

```yaml
title: [Report Type] Report
description: Generate reports

parameters:
  period:
    type: string
    default: last_week
    description: Time period

prompt: |
  Generate a {{ period }} report.

  Include:
  - Key metrics
  - Achievements
  - Issues
  - Next steps

  Gather data from git, tickets, etc.
```

## Real-World Examples

### Example 1: Security Audit

```bash
# Create the recipe
cat > ~/.opus/recipes/security-audit.yaml << 'EOF'
title: Security Audit
description: Comprehensive security review

parameters:
  target:
    type: string
    required: true
    description: File, directory, or system to audit

prompt: |
  Conduct a security audit of {{ target }}.

  Check for OWASP Top 10:
  1. Injection (SQL, command, LDAP)
  2. Broken authentication
  3. Sensitive data exposure
  4. XML external entities
  5. Broken access control
  6. Security misconfiguration
  7. XSS
  8. Insecure deserialization
  9. Components with known vulnerabilities
  10. Insufficient logging

  For each vulnerability found:
  - Describe the risk
  - Show the vulnerable code
  - Provide secure alternative
  - Rate severity (Critical/High/Medium/Low)

  Focus on critical and high severity issues first.
EOF

# Use it
opus -m "Run security-audit recipe on src/api/"
```

### Example 2: Dockerfile Review

```bash
cat > ~/.opus/recipes/dockerfile-review.yaml << 'EOF'
title: Dockerfile Review
description: Review Dockerfile for best practices

parameters:
  dockerfile:
    type: string
    required: true
    description: Path to Dockerfile

prompt: |
  Review the Dockerfile at {{ dockerfile }}.

  Best Practices:
  - Use specific base image tags (not :latest)
  - Multi-stage builds for smaller images
  - Run as non-root user
  - Minimize layers (combine RUN commands)
  - Use .dockerignore
  - COPY vs ADD usage
  - Proper caching strategy
  - Health checks
  - No secrets in image

  Security:
  - Scan for vulnerabilities in base image
  - Check for hardcoded credentials
  - Proper file permissions

  Provide before/after examples for improvements.
EOF

opus -m "Review Dockerfile using dockerfile-review recipe"
```

### Example 3: Database Migration Review

```bash
cat > ~/.opus/recipes/migration-review.yaml << 'EOF'
title: Database Migration Review
description: Review database migrations for safety

parameters:
  migration_file:
    type: string
    required: true
    description: Path to migration file

prompt: |
  Review the database migration at {{ migration_file }}.

  Safety Checks:
  - No data loss (ALTER TABLE DROP COLUMN)
  - Backwards compatible
  - Handles existing data
  - Proper indexes
  - Rollback plan included

  Performance:
  - Migrations on large tables (needs batching?)
  - Locking concerns
  - Index creation (CONCURRENTLY in Postgres)

  Best Practices:
  - Descriptive migration names
  - Comments explaining complex changes
  - Transactions where appropriate
  - Test data considerations

  For each issue:
  - Explain the risk
  - Suggest safer approach
EOF
```

## Tips & Tricks

### 1. Start Simple, Iterate

```yaml
# Version 1: Basic
title: Quick Code Check
prompt: |
  Review {{ file }} for obvious issues.

# Version 2: Add structure
title: Quick Code Check
prompt: |
  Review {{ file }} for:
  - Syntax errors
  - Security issues
  - Basic best practices

# Version 3: Add detail
title: Quick Code Check
prompt: |
  Review {{ file }} systematically:

  1. Security (injection, XSS, auth)
  2. Quality (naming, structure)
  3. Performance (algorithms, queries)

  Provide examples for each issue found.
```

### 2. Use Parameters for Flexibility

```yaml
parameters:
  severity:
    type: string
    default: medium
    description: Minimum severity (low, medium, high)

prompt: |
  Focus on {{ severity }} severity and above.

  {% if severity == "high" %}
  Only report critical security issues and bugs.
  {% else %}
  Report all issues including style and optimization.
  {% endif %}
```

### 3. Include Examples in Prompts

```yaml
prompt: |
  Provide feedback like this:

  - `src/app.py:42` - SQL injection risk
    ```python
    # Current (unsafe)
    query = f"SELECT * FROM users WHERE id = {user_id}"

    # Fixed
    query = "SELECT * FROM users WHERE id = ?"
    cursor.execute(query, (user_id,))
    ```
```

### 4. Guide Tool Usage

```yaml
prompt: |
  Process:
  1. Use Read to examine {{ file }}
  2. Use Grep to search for patterns like "eval(" or "pickle.load"
  3. Use Bash to run linters: `pylint {{ file }}`
  4. Analyze results and provide recommendations
```

## Advanced Usage

### Chaining Recipes

```bash
# First, review the code
opus -m "Review src/api.py using python-code-review recipe"

# Then, run security audit
opus -m "Run security-audit recipe on src/api.py"

# Finally, generate report
opus -m "Generate a security report for src/api.py"
```

### Team Workflows

```bash
# 1. Clone team recipes
git clone git@github.com:company/recipes.git ~/.opus/recipes/team

# 2. Use team standards
opus -m "Review my PR using team/code-review/python recipe"

# 3. Create your own, contribute back
cp ~/.opus/recipes/my-recipe.yaml ~/.opus/recipes/team/
cd ~/.opus/recipes/team
git add my-recipe.yaml
git commit -m "Add my-recipe for X"
git push
```

### Recipe Collections

```bash
# Organize by purpose
~/.opus/recipes/
├── code-review/
│   ├── python.yaml
│   ├── javascript.yaml
│   └── go.yaml
├── security/
│   ├── audit.yaml
│   ├── dependency-check.yaml
│   └── owasp-top10.yaml
├── infrastructure/
│   ├── dockerfile.yaml
│   ├── terraform.yaml
│   └── kubernetes.yaml
└── reports/
    ├── weekly.yaml
    ├── sprint.yaml
    └── incident.yaml

# Use nested recipes
opus -m "Review using code-review/python recipe"
```

## Troubleshooting

### Recipe Not Found

```bash
# Check it exists
ls ~/.opus/recipes/my-recipe.yaml

# Check filename matches what you're asking for
opus -m "Use my-recipe"  # Looks for my-recipe.yaml or my-recipe.yml
```

### Missing Parameters

```bash
# Error: Missing required parameter: file_path

# Fix: Provide the parameter
opus -m "Use recipe with file_path=src/app.py"
```

### Recipe Not Loading

```bash
# Check YAML syntax
python3 -c "import yaml; yaml.safe_load(open('.opus/recipes/my-recipe.yaml'))"

# Common issues:
# - Indentation (use 2 spaces)
# - Missing colons
# - Quotes in multi-line strings
```

## Best Practices Summary

✅ **Do:**
- Provide rich context and domain knowledge
- Specify output format
- Include examples in prompts
- Make recipes parameterized
- Start simple, iterate based on results

❌ **Don't:**
- Create rigid step-by-step procedures
- Make recipes too specific (hard to reuse)
- Forget to document parameters
- Skip validation and error cases

## Getting Help

```bash
# View recipe documentation
opus --help recipes

# List available recipes
opus -m "What recipes are available?"

# Get recipe info
opus -m "Tell me about the python-code-review recipe"
```

## Next Steps

1. **Try the built-in recipes** on your code
2. **Create your first custom recipe** for something you do often
3. **Share recipes** with your team
4. **Iterate and improve** based on results

Happy coding! 🚀
