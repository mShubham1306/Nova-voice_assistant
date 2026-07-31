"""
NOVA Backend 2.0 Verification Test Suite
Tests tool discovery, registry schemas, Layer 1 fast routing, Layer 2 brain schemas, memory logging, and tool execution.
"""

import sys
import os
from pathlib import Path

# Ensure UTF-8 output encoding for Windows terminal
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure backend root is on path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import settings
from tools.registry import registry
from core.router import fast_route
from core.memory import Memory
from core.assistant import Assistant


def test_tool_registry():
    print("\n--- 1. Testing Tool Registry & Auto-Discovery ---")
    tools = registry.list_tools()
    print(f"Loaded {len(tools)} tools:")
    for t in tools:
        print(f"  * {t['name']}: {len(t['actions'])} actions ({', '.join(t['actions'][:4])}...)")
    
    assert len(tools) >= 9, f"Expected at least 9 tools, found {len(tools)}"
    print("[OK] Tool registry discovery verified!")


def test_gemini_schemas():
    print("\n--- 2. Testing Gemini Function Declarations ---")
    schemas = registry.get_all_schemas()
    assert len(schemas) >= 9, "Missing tool schemas"
    for schema in schemas:
        assert "name" in schema
        assert "description" in schema
        assert "parameters" in schema
        props = schema["parameters"]["properties"]
        assert "tool" in props
        assert "action" in props
    print(f"[OK] Generated {len(schemas)} valid Gemini function calling schemas!")


def test_fast_router():
    print("\n--- 3. Testing Layer 1 Fast Router (Regex <1ms) ---")
    test_cases = [
        ("volume up", ("system_tool", "volume_up")),
        ("lock screen", ("system_tool", "lock_screen")),
        ("take screenshot", ("utility_tool", "screenshot")),
        ("what is the time", ("info_tool", "get_time")),
        ("tell me a joke", ("info_tool", "tell_joke")),
        ("open downloads", ("file_tool", "open_folder")),
        ("morning routine", ("workflow_tool", "morning_routine")),
        ("git status", ("dev_tool", "git_status")),
    ]
    
    for query, (expected_tool, expected_action) in test_cases:
        res = fast_route(query)
        assert res is not None, f"Fast route failed for: '{query}'"
        tool, action, params = res
        assert tool == expected_tool, f"Expected {expected_tool}, got {tool} for '{query}'"
        assert action == expected_action, f"Expected {expected_action}, got {action} for '{query}'"
        print(f"  * '{query}' -> {tool}.{action} (params={params})")
    
    print("[OK] Layer 1 Fast Router verified!")


def test_assistant_execution():
    print("\n--- 4. Testing End-to-End Command Execution ---")
    assistant = Assistant()
    
    # Test text query execution via L1
    res1 = assistant.process_command("what is the time", skip_speech=True)
    print(f"  Query: 'what is the time' -> Response: {res1['response']}")
    assert res1["type"] == "success"
    
    # Test info tool quote
    res2 = assistant.process_command("motivational quote", skip_speech=True)
    print(f"  Query: 'motivational quote' -> Response: {res2['response']}")
    assert res2["type"] == "success"
    
    # Test calculator via tool
    res3 = assistant.registry.execute("utility_tool", "calculate", {"expression": "25 * 4"})
    print(f"  Direct Tool Call utility_tool.calculate(25 * 4) -> Response: {res3.message}")
    assert "100" in res3.message

    # Test Notes Tool
    res4 = assistant.registry.execute("notes_tool", "add_note", {"content": "Prepare for python interview", "tags": "interview, python"})
    print(f"  Direct Tool Call notes_tool.add_note -> Response: {res4.message}")
    assert res4.success

    # Test Dev Tool Git Log
    res5 = assistant.registry.execute("dev_tool", "git_log", {"count": 2})
    print(f"  Direct Tool Call dev_tool.git_log -> Response: {res5.message}")
    assert res5.success

    print("[OK] End-to-End Execution verified!")


def test_memory():
    print("\n--- 5. Testing Session & Persistent Memory ---")
    mem = Memory(settings.MEMORY_FILE)
    mem.log_command("test command", "success", "info_tool.get_time")
    history = mem.get_recent_commands(5)
    assert len(history) > 0
    print(f"  Recent history count: {len(history)}")
    print(f"  Context Summary: {mem.get_context_summary()}")
    print("[OK] Memory subsystem verified!")


if __name__ == "__main__":
    print("==================================================")
    print("   RUNNING NOVA BACKEND 2.0 VERIFICATION SUITE   ")
    print("==================================================")
    try:
        test_tool_registry()
        test_gemini_schemas()
        test_fast_router()
        test_assistant_execution()
        test_memory()
        print("\n*** ALL BACKEND VERIFICATION TESTS PASSED SUCCESSFULLY! ***\n")
    except Exception as e:
        print(f"\n[FAIL] TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
