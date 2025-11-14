"""
Demonstration of sub-agent functionality

This script creates sample log files and shows how to use the run_subagents tool
to analyze them in parallel.
"""

import asyncio
import tempfile
from pathlib import Path

# Create sample log files
def create_sample_logs():
    """Create sample log files for demonstration"""
    temp_dir = Path(tempfile.mkdtemp(prefix="opus_demo_"))

    # App log with errors
    app_log = temp_dir / "app.log"
    app_log.write_text("""2024-11-14 10:00:01 INFO Starting application
2024-11-14 10:00:05 ERROR Database connection failed: timeout after 30s
2024-11-14 10:00:10 WARN Retrying database connection
2024-11-14 10:00:15 INFO Database connected successfully
2024-11-14 10:01:00 ERROR User authentication failed for user: admin
2024-11-14 10:01:30 ERROR Invalid API token provided
2024-11-14 10:02:00 INFO Request processed successfully
2024-11-14 10:03:00 ERROR OutOfMemoryError: heap space
""")

    # API log with performance issues
    api_log = temp_dir / "api.log"
    api_log.write_text("""2024-11-14 10:00:01 INFO API server started on port 8080
2024-11-14 10:00:05 INFO GET /api/users - 200 OK - 45ms
2024-11-14 10:00:10 WARN GET /api/reports - 200 OK - 5230ms (slow)
2024-11-14 10:00:15 INFO POST /api/login - 200 OK - 120ms
2024-11-14 10:00:20 ERROR GET /api/data - 500 Internal Server Error - 100ms
2024-11-14 10:00:25 WARN GET /api/export - 200 OK - 8950ms (slow)
2024-11-14 10:00:30 INFO GET /api/health - 200 OK - 5ms
""")

    # Worker log with task info
    worker_log = temp_dir / "worker.log"
    worker_log.write_text("""2024-11-14 10:00:01 INFO Worker started, ready to process tasks
2024-11-14 10:00:05 INFO Processing task: generate_report
2024-11-14 10:00:10 ERROR Task failed: generate_report - file not found
2024-11-14 10:00:15 INFO Processing task: send_email
2024-11-14 10:00:20 INFO Task completed: send_email
2024-11-14 10:00:25 ERROR Task failed: backup_database - permission denied
2024-11-14 10:00:30 INFO Processing task: cleanup_temp_files
2024-11-14 10:00:35 INFO Task completed: cleanup_temp_files
""")

    print(f"📁 Created sample logs in: {temp_dir}")
    print(f"   - {app_log.name}")
    print(f"   - {api_log.name}")
    print(f"   - {worker_log.name}")
    print()

    return temp_dir, [app_log, api_log, worker_log]


def print_example_usage(log_files):
    """Print example usage"""
    print("=" * 80)
    print("EXAMPLE: Using run_subagents tool for parallel log analysis")
    print("=" * 80)
    print()

    print("You can now use the opus CLI with a prompt like:")
    print()
    print(f'  opus -m "Use run_subagents to analyze these log files in parallel:')
    for log_file in log_files:
        print(f"  - {log_file}")
    print()
    print('  For each file, identify:')
    print('  1. Total number of ERROR lines')
    print('  2. Most common error type')
    print('  3. Any critical issues')
    print('  ')
    print('  Then summarize the findings across all logs."')
    print()
    print("=" * 80)
    print()

    print("Or you can call the tool directly from Python:")
    print()
    print("```python")
    print("from opus.tools.run_subagents import execute_run_subagents")
    print()
    print("result = await execute_run_subagents({")
    print("    'tasks': [")
    print("        {")
    print("            'prompt': 'Count ERROR lines and identify the most critical issue',")
    print(f"            'context': {{'type': 'file', 'path': '{log_files[0]}'}} ")
    print("        },")
    print("        {")
    print("            'prompt': 'Find slow API requests (>5000ms) and count errors',")
    print(f"            'context': {{'type': 'file', 'path': '{log_files[1]}'}} ")
    print("        },")
    print("        {")
    print("            'prompt': 'Identify failed tasks and summarize',")
    print(f"            'context': {{'type': 'file', 'path': '{log_files[2]}'}} ")
    print("        }")
    print("    ],")
    print("    'execution_mode': 'parallel'")
    print("})")
    print()
    print("# Result includes aggregated summary of all sub-agent analyses")
    print("print(result['output'])")
    print("```")
    print()


def print_tool_info():
    """Print information about the run_subagents tool"""
    print("=" * 80)
    print("RUN_SUBAGENTS TOOL OVERVIEW")
    print("=" * 80)
    print()
    print("✨ General-purpose sub-agent orchestration tool")
    print()
    print("Features:")
    print("  • Parallel execution: Run N sub-agents simultaneously")
    print("  • Sequential execution: Run sub-agents one after another")
    print("  • Full agent capabilities: Each sub-agent can use all tools")
    print("  • Flexible context: Pass file paths, URLs, or direct text")
    print("  • Automatic aggregation: Results combined into summary")
    print("  • Error handling: Failed sub-agents don't block others")
    print()
    print("Use cases:")
    print("  • Log analysis across multiple files")
    print("  • Code review of multiple modules")
    print("  • Parallel data processing")
    print("  • Multi-file search and analysis")
    print("  • Concurrent API testing")
    print()
    print("Parameters:")
    print("  • tasks: Array of task specs (strings or {prompt, context})")
    print("  • execution_mode: 'parallel' (default) or 'sequential'")
    print("  • max_turns: Optional max iterations per sub-agent (default: 15)")
    print()


def main():
    """Main demonstration"""
    print("\n🎯 SUB-AGENT SYSTEM DEMONSTRATION\n")

    # Print tool overview
    print_tool_info()

    # Create sample logs
    temp_dir, log_files = create_sample_logs()

    # Print usage examples
    print_example_usage(log_files)

    print(f"📝 Sample log files are ready in: {temp_dir}")
    print()
    print("💡 TIP: The agent will automatically use run_subagents when it detects")
    print("        multiple independent tasks that can be parallelized.")
    print()


if __name__ == "__main__":
    main()
