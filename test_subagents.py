"""Test script for sub-agent functionality"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from opus.tools.run_subagents import execute_run_subagents


async def test_simple_parallel():
    """Test basic parallel execution with simple prompts"""
    print("=" * 80)
    print("TEST 1: Simple parallel execution")
    print("=" * 80)

    args = {
        "tasks": [
            "What is 2 + 2? Just answer with the number.",
            "What is the capital of France? Just answer with the city name.",
            "What color is the sky on a clear day? Just answer with the color."
        ],
        "execution_mode": "parallel",
        "max_turns": 5
    }

    result = await execute_run_subagents(args)

    if "error" in result:
        print(f"❌ ERROR: {result['error']}")
        return False

    print(result["output"])
    print("\nMetadata:", result["metadata"]["execution_summary"])

    # Check success
    summary = result["metadata"]["execution_summary"]
    success = summary["successful"] == 3 and summary["failed"] == 0
    print(f"\n{'✅ PASS' if success else '❌ FAIL'}")
    return success


async def test_sequential_execution():
    """Test sequential execution"""
    print("\n" + "=" * 80)
    print("TEST 2: Sequential execution")
    print("=" * 80)

    args = {
        "tasks": [
            "Count to 3, one number per line.",
            "List 2 colors, one per line."
        ],
        "execution_mode": "sequential",
        "max_turns": 5
    }

    result = await execute_run_subagents(args)

    if "error" in result:
        print(f"❌ ERROR: {result['error']}")
        return False

    print(result["output"])
    print("\nMetadata:", result["metadata"]["execution_summary"])

    # Check that it's sequential
    summary = result["metadata"]["execution_summary"]
    success = summary["execution_mode"] == "sequential" and summary["successful"] == 2
    print(f"\n{'✅ PASS' if success else '❌ FAIL'}")
    return success


async def test_file_context():
    """Test with file context"""
    print("\n" + "=" * 80)
    print("TEST 3: File context")
    print("=" * 80)

    # Create test files
    test_dir = Path("/tmp/opus_test")
    test_dir.mkdir(exist_ok=True)

    file1 = test_dir / "log1.txt"
    file2 = test_dir / "log2.txt"

    file1.write_text("ERROR: Database connection failed\nINFO: Starting service\nERROR: Timeout")
    file2.write_text("WARN: Low memory\nINFO: Request processed\nERROR: Invalid input")

    args = {
        "tasks": [
            {
                "prompt": "Count how many ERROR lines are in this log file. Just answer with the number.",
                "context": {"type": "file", "path": str(file1)}
            },
            {
                "prompt": "Count how many ERROR lines are in this log file. Just answer with the number.",
                "context": {"type": "file", "path": str(file2)}
            }
        ],
        "execution_mode": "parallel",
        "max_turns": 5
    }

    result = await execute_run_subagents(args)

    if "error" in result:
        print(f"❌ ERROR: {result['error']}")
        return False

    print(result["output"])
    print("\nMetadata:", result["metadata"]["execution_summary"])

    summary = result["metadata"]["execution_summary"]
    success = summary["successful"] == 2
    print(f"\n{'✅ PASS' if success else '❌ FAIL'}")
    return success


async def test_direct_context():
    """Test with direct text context"""
    print("\n" + "=" * 80)
    print("TEST 4: Direct text context")
    print("=" * 80)

    args = {
        "tasks": [
            {
                "prompt": "How many words are in this text? Just answer with the number.",
                "context": "The quick brown fox jumps over the lazy dog"
            },
            {
                "prompt": "What is the first word in this text?",
                "context": "Hello world from sub-agents"
            }
        ],
        "execution_mode": "parallel",
        "max_turns": 5
    }

    result = await execute_run_subagents(args)

    if "error" in result:
        print(f"❌ ERROR: {result['error']}")
        return False

    print(result["output"])
    print("\nMetadata:", result["metadata"]["execution_summary"])

    summary = result["metadata"]["execution_summary"]
    success = summary["successful"] == 2
    print(f"\n{'✅ PASS' if success else '❌ FAIL'}")
    return success


async def test_error_handling():
    """Test error handling with invalid file"""
    print("\n" + "=" * 80)
    print("TEST 5: Error handling (invalid file)")
    print("=" * 80)

    args = {
        "tasks": [
            {
                "prompt": "Analyze this file",
                "context": {"type": "file", "path": "/nonexistent/file.txt"}
            },
            "This task should succeed"
        ],
        "execution_mode": "parallel",
        "max_turns": 5
    }

    result = await execute_run_subagents(args)

    if "error" in result:
        print(f"❌ ERROR: {result['error']}")
        return False

    print(result["output"])
    print("\nMetadata:", result["metadata"]["execution_summary"])

    # Should have 1 success and 1 failure
    summary = result["metadata"]["execution_summary"]
    success = summary["successful"] == 1 and summary["failed"] == 1
    print(f"\n{'✅ PASS (expected partial failure)' if success else '❌ FAIL'}")
    return success


async def main():
    """Run all tests"""
    print("\n🧪 TESTING SUB-AGENT SYSTEM\n")

    tests = [
        ("Simple parallel execution", test_simple_parallel),
        ("Sequential execution", test_sequential_execution),
        ("File context", test_file_context),
        ("Direct text context", test_direct_context),
        ("Error handling", test_error_handling),
    ]

    results = []
    for name, test_func in tests:
        try:
            success = await test_func()
            results.append((name, success))
        except Exception as e:
            print(f"\n❌ TEST CRASHED: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {name}")

    total = len(results)
    passed = sum(1 for _, success in results if success)
    print(f"\nTotal: {passed}/{total} tests passed")

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
