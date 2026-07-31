"""
NOVA 3.0 Enterprise Architecture Verification Test Suite
Validates EventBus, ExecutionEngine, Safety Interceptor, Pending Confirmation Queue,
Declarative JSON Workflows, Tool Health Audits, TaskManager, and LLM Resiliency.
"""

import sys
import time
from pathlib import Path

# Ensure UTF-8 output encoding for Windows terminal
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Add backend root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import settings
from core.event_bus import event_bus, Event
from core.execution_engine import execution_engine
from core.task_manager import task_manager
from core.assistant import Assistant
from tools.registry import registry


def test_event_bus():
    print("\n--- 1. Testing Event Bus Pub-Sub System ---")
    events_received = []

    def on_event(event: Event):
        events_received.append(event)

    event_bus.subscribe("test_event", on_event)
    event_bus.publish("test_event", {"msg": "hello event bus"})

    assert len(events_received) == 1
    assert events_received[0].payload["msg"] == "hello event bus"
    print("  * Published and received 'test_event' successfully!")
    print("[OK] Event Bus pub-sub verified!")


def test_tool_health_audits():
    print("\n--- 2. Testing Tool Health Diagnostic Audits ---")
    tools = list(registry._tools.values())
    health_reports = [t.health() for t in tools]
    
    assert len(health_reports) >= 9
    for h in health_reports:
        assert "name" in h
        assert "version" in h
        assert "status" in h
        assert "priority" in h
        print(f"  * {h['name']} (v{h['version']}) -> status: {h['status']}, priority: {h['priority']}")
    
    print("[OK] Tool Health Audit system verified!")


def test_safety_interceptor_and_confirmations():
    print("\n--- 3. Testing Safety Interceptor & Pending Confirmation Queue ---")
    
    # Trigger dangerous action (delete_file)
    res = execution_engine.execute_action("file_tool", "delete_file", {"filename": "non_existent.pdf"})
    assert res.requires_confirmation
    assert "confirmation_id" in res.data
    confirm_id = res.data["confirmation_id"]
    print(f"  * Intercepted dangerous action! Prompt: '{res.confirmation_prompt}' (ID: {confirm_id})")

    # Check pending list
    pending = execution_engine.get_pending_confirmations()
    assert len(pending) == 1
    assert pending[0]["id"] == confirm_id

    # User cancels/rejects action
    cancel_res = execution_engine.confirm_action(confirm_id, approved=False)
    assert cancel_res.success
    assert len(execution_engine.get_pending_confirmations()) == 0
    print("  * Pending action successfully cancelled upon user rejection!")

    print("[OK] Safety Interceptor & Confirmation Queue verified!")


def test_declarative_json_workflows():
    print("\n--- 4. Testing Declarative JSON Workflows ---")
    wf_tool = registry.get_tool("workflow_tool")
    assert wf_tool is not None

    # List workflows
    res = wf_tool.execute("list_workflows", {})
    assert res.success
    wfs = res.data.get("workflows", [])
    print(f"  * Found {len(wfs)} declarative workflow(s): {', '.join(w['name'] for w in wfs)}")
    assert len(wfs) >= 3

    # Run declarative coding_environment workflow
    wf_res = wf_tool.execute("run_workflow", {"workflow_id": "coding_environment"})
    assert wf_res.success
    print(f"  * Executed declarative workflow 'coding_environment': {wf_res.message}")

    print("[OK] Declarative JSON Workflows verified!")


def test_task_manager():
    print("\n--- 5. Testing Background Task Manager & Progress Tracking ---")
    progress_updates = []

    def mock_long_task(progress_cb):
        progress_cb(10, "Starting scan...")
        time.sleep(0.1)
        progress_cb(50, "Halfway done...")
        time.sleep(0.1)
        progress_cb(100, "Scan complete!")
        from tools.base_tool import ToolResult
        return ToolResult.ok("Scan finished successfully.")

    task = task_manager.submit_task("Mock Scan", "file_tool", "find_duplicates", mock_long_task)
    print(f"  * Submitted background task ID: {task.id}")
    time.sleep(0.3)

    updated_task = task_manager.get_task(task.id)
    assert updated_task is not None
    assert updated_task.status == "completed"
    assert updated_task.progress == 100
    print(f"  * Background task finished with status '{updated_task.status}' and progress {updated_task.progress}%!")

    print("[OK] Background Task Manager verified!")


def test_assistant_integration_v3():
    print("\n--- 6. Testing Full Assistant NOVA 3.0 Integration ---")
    assistant = Assistant()
    
    # Process text query through ExecutionEngine & EventBus
    res = assistant.process_command("what is the time", skip_speech=True)
    assert res["type"] == "success"
    print(f"  * Query 'what is the time' -> Response: {res['response']}")

    status = assistant.get_status()
    assert status["name"] == "Nova"
    print(f"  * Assistant Status -> Pending confirmations: {status['pending_confirmations']}, Tools: {status['tools_loaded']}")

    print("[OK] Full Assistant NOVA 3.0 Integration verified!")


if __name__ == "__main__":
    print("==================================================")
    print("   RUNNING NOVA 3.0 ENTERPRISE TEST SUITE         ")
    print("==================================================")
    try:
        test_event_bus()
        test_tool_health_audits()
        test_safety_interceptor_and_confirmations()
        test_declarative_json_workflows()
        test_task_manager()
        test_assistant_integration_v3()
        print("\n*** ALL NOVA 3.0 ENTERPRISE TESTS PASSED SUCCESSFULLY! ***\n")
    except Exception as e:
        print(f"\n[FAIL] TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
