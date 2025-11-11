# Recipe Quick Start Guide

## What Are Recipes?

Recipes are **expert prompt packages** that give the AI agent specialized knowledge for specific tasks. They're like having an expert guide the agent through complex work.

## Using Recipes (3 Ways)

### 1. Simple - Just Ask

```bash
opus -m "Review my code using python-code-review recipe"
```

### 2. Specific - Name the File

```bash
opus -m "Review src/app.py using python-code-review recipe"
```

### 3. Focused - Add Parameters

```bash
opus -m "Review src/api.py with python-code-review recipe, focus on security"
```

## Built-In Recipes

### Python Code Review
```bash
opus -m "Review src/app.py using python-code-review recipe"
```
Checks: PEP 8, security, performance, testing, type hints

### API Spec Review
```bash
opus -m "Review api/openapi.yaml using api-spec-review recipe"
```
Checks: REST principles, security, consistency, documentation

### Weekly Report
```bash
opus -m "Generate weekly report using weekly-report recipe for backend team"
```
Creates: Achievements, metrics, WIP, blockers, next steps

## Creating Your Own Recipe

### 1. Create the File

```bash
nano ~/.opus/recipes/my-recipe.yaml
```

### 2. Write the Recipe

```yaml
title: My Recipe Name
description: What this recipe does

parameters:
  file_path:
    type: string
    required: true
    description: What file to process

prompt: |
  You are an expert at [your domain].

  Review {{ file_path }} for:
  - Thing 1
  - Thing 2
  - Thing 3

  Provide specific feedback with line numbers.
  Show code examples for improvements.
```

### 3. Use It

```bash
opus -m "Use my-recipe on src/file.py"
```

## Recipe Template (Copy & Paste)

```yaml
title: [Your Recipe Name]
description: [What it does]

parameters:
  target:
    type: string
    required: true
    description: [What to analyze]

prompt: |
  Review {{ target }} for [your domain].

  Check for:
  - [Criterion 1]
  - [Criterion 2]
  - [Criterion 3]

  Process:
  1. Read {{ target }}
  2. Check each criterion
  3. Provide specific feedback

  Output:
  - Critical Issues: [Must fix]
  - Improvements: [Should fix]
  - Suggestions: [Nice to have]

  Include line numbers and code examples.
```

## Common Recipe Patterns

### Code Review (Any Language)
```yaml
title: [Language] Code Review
parameters:
  file_path:
    type: string
    required: true
prompt: |
  Review {{ file_path }} for:
  - Best practices
  - Security issues
  - Performance
  - Testing
```

### Specification Review
```yaml
title: [Spec Type] Review
parameters:
  spec_path:
    type: string
    required: true
prompt: |
  Review {{ spec_path }} for:
  - Completeness
  - Consistency
  - Standards compliance
```

### Security Audit
```yaml
title: Security Audit
parameters:
  target:
    type: string
    required: true
prompt: |
  Audit {{ target }} for OWASP Top 10:
  - Injection attacks
  - Broken auth
  - XSS
  - [etc]
```

## What Happens When You Use a Recipe

1. **Agent loads recipe** → Gets expert context and guidance
2. **Agent reads your files** → Uses Read, Grep, or other tools
3. **Agent analyzes** → Applies the recipe's checklist
4. **You get results** → Structured, comprehensive feedback

## Tips

✅ **Do:**
- Make recipes reusable (use parameters)
- Provide examples in prompts
- Specify output format
- Include best practices

❌ **Don't:**
- Make rigid step-by-step scripts
- Hardcode file paths
- Forget to document parameters

## Examples You Can Try Right Now

### Review Python Code
```bash
# Create a test file
echo 'def calc(x): return x*2' > test.py

# Review it
opus -m "Review test.py using python-code-review recipe"
```

### Create Custom Recipe
```bash
# Create a JSON review recipe
cat > ~/.opus/recipes/json-review.yaml << 'EOF'
title: JSON Review
description: Review JSON files for validity and best practices

parameters:
  file_path:
    type: string
    required: true
    description: Path to JSON file

prompt: |
  Review the JSON file at {{ file_path }}.

  Check for:
  - Valid JSON syntax
  - Consistent formatting
  - Appropriate data types
  - No sensitive data
  - Schema compliance (if applicable)

  Provide specific recommendations.
EOF

# Use it
opus -m "Review package.json using json-review recipe"
```

## Where Recipes Live

```bash
# User recipes
~/.opus/recipes/
├── python-code-review.yaml
├── api-spec-review.yaml
├── weekly-report.yaml
└── your-custom-recipe.yaml

# Project recipes (optional)
./.opus/recipes/
└── project-specific-recipe.yaml
```

## Getting Help

```bash
# List available recipes
ls ~/.opus/recipes/

# Read a recipe
cat ~/.opus/recipes/python-code-review.yaml

# Ask the agent
opus -m "What recipes are available?"
opus -m "How do I use the python-code-review recipe?"
```

## Next Steps

1. ✅ Try a built-in recipe on your code
2. ✅ Create a recipe for something you review often
3. ✅ Share recipes with your team
4. ✅ Build a library of recipes for common tasks

---

**Pro Tip:** Recipes are just YAML files. Start simple, iterate based on results, and build up your library over time!
