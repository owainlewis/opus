# Recipes

Recipes are **step-by-step guides** that combine knowledge, context, and executable steps. They can be operational runbooks (incident response, debugging) or knowledge guides (how to perform code reviews, onboarding procedures).

## What are Recipes?

Think of recipes as **intelligent guides** that:
- Combine context and knowledge with actionable steps
- Can be executed automatically by the AI agent with your approval
- Work for both technical operations and non-technical procedures
- Are written in familiar Markdown format
- Include both automated commands and manual instructions

**Key Insight:** Recipes leverage the AI agent's capabilities. You ask the agent to run a recipe, approve it once, and the agent executes all steps automatically while assisting you throughout the process.

## Quick Start

### Ask the agent to run a recipe

```bash
opus -m "Run the health-check recipe"
```

The agent will:
1. Find the recipe
2. Ask for your approval to execute it
3. Run each step automatically
4. Report results back to you

### In a conversation

```
You: We're having issues with the API service in production
Agent: Let me help. I'll run the incident-triage recipe...
```

## Recipe Format

Recipes are Markdown files stored in `~/.opus/recipes/`.

### Basic Structure

```markdown
# Recipe Name

Description of what this recipe does. Include context, background information,
and knowledge that helps understand the purpose and approach.

**Parameters:**
- param_name (required): Description of parameter
- another_param (default: value): Optional parameter with default

## Step 1: Step Name

Description of what this step does and why it's important.

```bash
command $param_name
\```

## Step 2: Manual Step

This is a manual step with instructions for you to follow:

1. Do this action
2. Check that result
3. Verify the outcome

## Step 3: Another Command

More context about this step.

```bash
another-command --option $another_param
\```
```

### Convention-Based Parsing

The agent parses recipes using these conventions:

- `# Title` → Recipe name
- `**Parameters:**` section → Input parameters
- `## Step N: Name` → Step headers
- ` ```bash code blocks` → Executable commands
- Other text → Manual instructions and context

### Parameters

Define inputs that can be provided when running the recipe:

```markdown
**Parameters:**
- service (required): Service name to investigate
- namespace (default: production): Kubernetes namespace
- severity (default: P2): Incident severity (P1, P2, P3)
```

**In commands**, reference parameters with `$param`:

```bash
kubectl get pods -n $namespace -l app=$service
```

Both `$var` and `${var}` syntax work.

## Step Types

### Executable Steps

Steps with code blocks are executed automatically:

```markdown
## Step 1: Check pod status

```bash
kubectl get pod $pod -n $namespace
\```
```

The agent executes the bash command and shows you the output.

### Manual Steps

Steps without code blocks are manual instructions:

```markdown
## Step 2: Review dashboard

Open Grafana and check:
1. Error rate panel
2. Latency graphs
3. Resource usage

Note any anomalies or spikes.
```

The agent shows you these instructions and waits for your confirmation.

### Mixed Knowledge and Execution

Recipes can combine context, knowledge, and commands:

```markdown
## Step 3: Check database connection pool

Database connection issues often manifest as increased latency.
Common causes include:
- Pool exhaustion (all connections in use)
- Connection leaks (not being returned)
- Network issues between app and database

```bash
psql -c "SELECT count(*) FROM pg_stat_activity WHERE application_name='$service'"
\```

If count exceeds pool size (default: 20), you have a connection leak.
```

## Example Recipes

### Operational Runbook: Kubernetes Debug

```markdown
# Kubernetes Pod Debug

Debug a failing Kubernetes pod through systematic investigation.

**Parameters:**
- namespace (required): Kubernetes namespace
- pod (required): Pod name to debug

## Step 1: Get pod status

Check current state, restarts, and node placement.

```bash
kubectl get pod $pod -n $namespace -o wide
\```

## Step 2: Get recent logs

Look for error patterns and exceptions.

```bash
kubectl logs $pod -n $namespace --tail=100
\```

## Step 3: Check events

View Kubernetes events for scheduling issues or errors.

```bash
kubectl get events -n $namespace --field-selector involvedObject.name=$pod
\```

## Step 4: Analyze findings

Review the output above:
1. What is the pod's status?
2. Any error messages in logs?
3. What do events indicate?
4. Resource limits exceeded?

Determine next troubleshooting steps based on findings.
```

### Knowledge Guide: Code Review

```markdown
# Code Review Best Practices

Guidelines for conducting thorough and constructive code reviews.

## Step 1: Understand context

Before reviewing code:
- Read the PR description thoroughly
- Understand the problem being solved
- Check linked tickets or issues
- Review the acceptance criteria

## Step 2: Architecture review

Consider these questions:
- Does this change follow existing patterns?
- Are new dependencies introduced appropriately?
- Will this scale with increased load?
- Are there simpler alternatives?

## Step 3: Code quality check

Run automated checks:

```bash
npm run lint
npm run test
npm run test:coverage
\```

Look for:
- Clear, descriptive variable names
- Appropriate comments for complex logic
- Consistent code style
- Adequate test coverage (>80%)

## Step 4: Security review

Check for common vulnerabilities:
- Input validation and sanitization
- SQL injection risks
- XSS (cross-site scripting) vulnerabilities
- Secrets or credentials in code
- Proper authentication/authorization

## Step 5: Leave constructive feedback

When commenting:
- Be specific about what needs changing
- Explain the reasoning behind suggestions
- Acknowledge good patterns you see
- Ask questions rather than making demands
- Separate "must fix" from "nice to have"

Remember: Code review is about maintaining quality AND helping teammates grow.
```

### Non-Technical: Manager Onboarding

```markdown
# Engineering Manager Onboarding

Guide for onboarding a new engineering manager to the team.

**Parameters:**
- manager_name (required): New manager's name
- team_name (required): Team they'll be managing

## Step 1: Send welcome email

Email $manager_name with:
- Team roster and org chart
- Meeting schedule template
- Access request forms
- First week agenda

Use the "New Manager Welcome" email template in Gmail.

## Step 2: Schedule 1-on-1s

Set up 30-minute intro meetings with each $team_name member:

1. Check team calendar for availability
2. Send calendar invites with agenda
3. Space them out over first 2 weeks

Meeting agenda:
- Team member's background
- Current projects
- Communication preferences
- What they need from their manager

## Step 3: Grant access

Submit access requests (2-3 days processing):
- GitHub org admin access
- JIRA project lead role
- PagerDuty manager permissions
- Slack admin role

```bash
# Submit IT ticket for access
opus-tools submit-ticket --category access --user $manager_name
\```

## Step 4: Review team context

With outgoing manager or tech lead, review:
- Current sprint goals
- Upcoming deadlines
- Known issues or risks
- Team dynamics and relationships
- Individual performance contexts

## Step 5: Week 1 check-in

Schedule check-in with $manager_name's manager:
- How are 1-on-1s going?
- Any surprises or concerns?
- Access issues resolved?
- Questions about team or company?

Be honest - it's okay to not have all the answers yet!
```

## How It Works

### 1. Agent Discovers Recipe

You ask the agent to run a recipe by name:

```
You: Run the incident-triage recipe for the api service
```

### 2. Agent Calls Recipe Tool

The agent identifies this request and calls the `recipe` tool:

```
recipe(
  recipe_name="incident-triage",
  params={"service": "api"}
)
```

### 3. You Approve Once

Opus asks for your approval:

```
● Recipe(recipe_name='incident-triage', params={'service': 'api'})
  Approve? (y/n):
```

Type `y` to approve.

### 4. Agent Executes Steps

The agent:
- Reads the recipe
- Interpolates parameters (`$service` → `api`)
- Executes each step automatically
- Shows you output and asks for input on manual steps
- Reports final results

### 5. Results Returned

You see a summary:

```
Recipe 'incident-triage' execution complete:
- Completed: 5/7
- Failed: 1
- Skipped: 1

✓ Check service health - completed
✓ Gather logs - completed
✗ Check metrics - failed (connection timeout)
...
```

## Creating Your Own Recipes

### 1. Create a new Markdown file

```bash
touch ~/.opus/recipes/my-recipe.md
```

### 2. Write your recipe

Follow the conventions:

```markdown
# My Recipe

What this recipe does and when to use it.

**Parameters:**
- param1 (required): Description

## Step 1: First Action

```bash
command $param1
\```
```

### 3. Use it

Ask the agent:

```bash
opus -m "Run my-recipe with param1 set to foo"
```

## Best Practices

### 1. Descriptive Names

✅ Good:
```markdown
## Step 1: Check error rate in last hour
## Step 2: Restart failed pods
## Step 3: Verify service is responding
```

❌ Bad:
```markdown
## Step 1: Check stuff
## Step 2: Do things
```

### 2. Add Context

Help the agent (and humans) understand:

```markdown
## Step 3: Check database connections

Connection pool exhaustion is a common cause of API timeouts.
The default pool size is 20. If active connections exceed this,
new requests will queue and eventually timeout.

```bash
psql -c "SELECT count(*) FROM pg_stat_activity"
\```

If count > 20, investigate connection leaks in application code.
```

### 3. Parameterize Everything

Make recipes reusable:

❌ Hardcoded:
```bash
kubectl logs api-gateway -n production
```

✅ Parameterized:
```bash
kubectl logs $service -n $namespace
```

### 4. Mix Automation and Guidance

Not everything should be automated:

```markdown
## Step 4: Review monitoring

```bash
curl $service/metrics | jq '.error_rate'
\```

Expected value: < 0.01 (1%)

If elevated:
1. Check recent deployments
2. Review error logs
3. Compare to baseline
4. Escalate if sustained
```

### 5. Document Expected Outcomes

Help users interpret results:

```markdown
## Step 2: Check disk space

```bash
df -h
\```

**Healthy:** < 80% used
**Warning:** 80-90% used
**Critical:** > 90% used

If critical, clear logs or expand volume.
```

## Use Cases

### Operations & SRE

- **Incident Response:** `incident-triage.md`, `service-degradation.md`
- **Debugging:** `k8s-pod-debug.md`, `high-latency-debug.md`
- **Health Checks:** `health-check.md`, `pre-deploy-checklist.md`
- **Maintenance:** `certificate-renewal.md`, `database-migration.md`

### Development

- **Code Quality:** `code-review.md`, `refactoring-checklist.md`
- **Debugging:** `production-bug-debug.md`, `memory-leak-investigation.md`
- **Deployment:** `deploy-to-staging.md`, `rollback-deployment.md`

### Management

- **Onboarding:** `manager-onboarding.md`, `engineer-onboarding.md`
- **Process:** `sprint-planning.md`, `incident-postmortem.md`
- **Reviews:** `performance-review-guide.md`, `promotion-packet.md`

## Storage and Sharing

### Local Recipes

Store in `~/.opus/recipes/`:

```bash
ls ~/.opus/recipes/
health-check.md
incident-triage.md
k8s-pod-debug.md
```

### Team Recipes

Share via Git:

```bash
# Team repository
team-recipes/
├── incident-response/
│   ├── api-down.md
│   ├── database-recovery.md
│   └── network-issues.md
├── debugging/
│   ├── k8s-pod-debug.md
│   └── high-cpu-debug.md
└── onboarding/
    ├── engineer-onboarding.md
    └── manager-onboarding.md

# Clone to local recipes dir
git clone git@github.com:company/recipes.git ~/.opus/recipes/team
```

## Troubleshooting

### Recipe not found

```
Error: Recipe not found: my-recipe
```

**Solution:** Check file exists:
```bash
ls ~/.opus/recipes/my-recipe.md
```

### Missing required parameter

```
Error: Missing required parameter: namespace
```

**Solution:** Provide all required parameters:
```
opus -m "Run k8s-pod-debug with namespace=production and pod=api-123"
```

### Step execution failed

```
✗ Check service logs - failed (command not found: kubectl)
```

**Solution:** Ensure required tools are installed:
```bash
which kubectl
```

## Tips

### 1. Start Simple

Create simple recipes with 3-5 steps. Add complexity as needed.

### 2. Iterate Based on Use

Update recipes after each use based on what worked and what didn't.

### 3. Document Tribal Knowledge

Capture expert knowledge as recipes before it's lost:

```markdown
# Database Recovery

Steps learned from the 2024-03-15 incident.
Author: Jane Doe (based on incident #1234)
```

### 4. Use for Onboarding

New team members can run recipes to learn procedures:

```bash
opus -m "Run the deploy-to-staging recipe"
```

### 5. Version Control

Keep recipes in Git to track changes and collaborate:

```bash
git commit -m "Update incident-triage recipe with new escalation paths"
```

## Related Documentation

- [Configuration](./CONFIGURATION.md) - Configuring Opus
- [Tools Guide](./TOOLS.md) - Creating custom tools

## Examples

All example recipes are in `~/.opus/recipes/`:

```bash
ls ~/.opus/recipes/
health-check.md
incident-triage.md
k8s-pod-debug.md
```

View any recipe to see the format:

```bash
cat ~/.opus/recipes/health-check.md
```
