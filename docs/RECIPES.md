# Recipes

Recipes are reusable prompt templates that package expertise and best practices for specific tasks. They help the AI agent excel at complex work by providing detailed context and guidance.

## What is a Recipe?

A recipe is a YAML file that contains instructions for handling a particular type of task. Think of it as an expert guide that helps the AI understand what to look for, how to approach the problem, and what kind of output you expect.

For example, a code review recipe might include guidelines about security vulnerabilities to check for, performance patterns to look for, and how to structure the feedback. The AI uses this context to provide more thorough and consistent reviews than it would with a generic prompt.

## Using Recipes

You can ask the AI to use a recipe in natural language:

```bash
opus -m "Review src/app.py using the python-code-review recipe"
```

The AI will load the recipe, understand the context and guidelines it provides, and then use its normal tools (reading files, searching code, etc.) to complete the task according to the recipe's instructions.

## Recipe Format

Recipes are YAML files with a simple structure:

```yaml
title: Python Code Review
description: Comprehensive code review for Python projects

instructions: You are a senior Python developer conducting thorough code reviews with a focus on security, performance, and maintainability.

parameters:
  file_path:
    type: string
    required: true
    description: Path to the Python file or directory to review

  focus:
    type: string
    required: false
    default: all
    description: Focus area (security, performance, style, all)

prompt: |
  Review the Python code at {{ file_path }} with focus on {{ focus }}.

  Check for common issues like:
  - Security vulnerabilities (SQL injection, XSS, command injection)
  - Performance problems (inefficient algorithms, N+1 queries)
  - Code style and PEP 8 compliance
  - Error handling and edge cases

  Provide specific feedback with file paths and line numbers.
  Include code examples showing how to fix issues.

  Structure your review as:
  - Summary of overall code quality
  - Critical issues that must be fixed
  - Important improvements to consider
  - Minor suggestions for polish
```

The recipe has four main sections:

**Title and Description** give a quick overview of what the recipe does.

**Instructions** set the role or persona for the AI. This helps establish the right mindset and expertise level for the task.

**Parameters** define the inputs the recipe needs. Each parameter has a type, whether it's required, and a description. You can also provide default values for optional parameters.

**Prompt** contains the actual task instructions and guidance. You can reference parameters using `{{ parameter_name }}` syntax. This is where you provide the detailed context about what to check, how to approach the task, and what format the output should take.

## Creating Your Own Recipes

To create a recipe, make a YAML file in `~/.opus/recipes/`:

```yaml
title: My Custom Recipe
description: What this recipe does

parameters:
  target:
    type: string
    required: true
    description: What to analyze

prompt: |
  Your task is to analyze {{ target }}.

  Follow these steps:
  1. First, understand the context
  2. Look for specific patterns or issues
  3. Provide clear, actionable feedback

  Format your response with:
  - Summary of findings
  - Detailed analysis
  - Recommendations
```

The key to a good recipe is providing enough context and structure to guide the AI without being overly rigid. Describe what to look for, what good looks like, and how to present the results. The AI will use this guidance along with its reasoning abilities to complete the task.

## Built-in Example Recipes

Opus includes several example recipes:

**Python Code Review** (`examples/recipes/python-code-review.yaml`)
A comprehensive code review recipe that checks for security issues, performance problems, style compliance, and best practices. It provides structured feedback with specific file and line number references.

**API Specification Review** (`examples/recipes/api-spec-review.yaml`)
Reviews API specifications for design quality, security, documentation completeness, and consistency. Useful for OpenAPI/Swagger specs.

**Weekly Engineering Report** (`examples/recipes/weekly-report.yaml`)
Generates weekly engineering reports by analyzing git commits, pull requests, and project activity. Produces a structured report with achievements, work in progress, and upcoming priorities.

## Tips for Writing Recipes

Start with clear instructions about the role and expertise level. This helps the AI understand what perspective to take.

Be specific about what to look for, but don't try to script every step. The AI can reason and adapt, so provide guidance and let it figure out the details.

Include examples of good output when possible. Showing the format you want makes it easier for the AI to match your expectations.

Use parameters to make recipes reusable. Instead of hardcoding paths or values, make them parameters so the recipe works in different situations.

Test your recipe with different inputs to make sure it works reliably. Try it on simple cases and complex ones to see if the guidance is sufficient.

## Sharing Recipes

You can share recipes by putting them in a Git repository. Create a collection of recipes for your team or project:

```bash
# Clone team recipes
git clone git@github.com:yourteam/opus-recipes.git ~/.opus/recipes/team

# Use a team recipe
opus -m "Use team/security-audit recipe on src/auth.py"
```

This lets teams build up a library of expertise that anyone can use.
