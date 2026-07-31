"""
NOVA Tool — Declarative Workflow Engine (NOVA 3.0)
Multi-step automated workflows driven by declarative JSON/YAML definitions.

Workflows are dynamically loaded from data/workflows/*.json. Users can add custom
workflows without writing a single line of Python code.
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

from tools.base_tool import BaseTool, ToolResult, param

logger = logging.getLogger("nova.workflow_tool")


class WorkflowTool(BaseTool):
    name = "workflow_tool"
    description = (
        "Executes multi-step automated workflows: interview preparation, coding environment, "
        "morning routine, focus mode, study session, and custom declarative JSON workflows."
    )
    actions = [
        "run_workflow",
        "list_workflows",
        "create_workflow",
        "interview_prep",
        "coding_environment",
        "morning_routine",
        "focus_mode",
    ]
    parameters = {
        "run_workflow": {
            "workflow_id": param("string", "ID of the declarative workflow to run (e.g. 'interview_prep', 'morning_routine')", required=True),
            "custom_params": param("object", "Optional parameter overrides for workflow steps"),
        },
        "create_workflow": {
            "name": param("string", "Human readable workflow name", required=True),
            "id": param("string", "Unique snake_case workflow ID", required=True),
            "description": param("string", "One-sentence workflow description"),
            "steps": param("array", "List of step objects: [{tool, action, params}]", required=True),
        },
        "interview_prep": {
            "company": param("string", "Company name for interview prep"),
            "role": param("string", "Role being interviewed for"),
        },
        "coding_environment": {
            "project": param("string", "Project name"),
        },
        "morning_routine": {},
        "focus_mode": {
            "duration": param("string", "Focus duration e.g. '25 minutes'"),
        },
    }
    version = "3.0.0"
    priority = 85

    def __init__(self) -> None:
        from config import settings
        self._settings = settings
        self._workflows_dir = settings.DATA_DIR / "workflows"
        try:
            self._workflows_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass

    def _load_workflow(self, workflow_id: str) -> dict | None:
        """Load declarative workflow JSON file by ID."""
        file_path = self._workflows_dir / f"{workflow_id}.json"
        if file_path.exists():
            try:
                return json.loads(file_path.read_text(encoding="utf-8"))
            except Exception as e:
                logger.error("Failed to parse workflow file %s: %s", file_path, e)
        return None

    def _list_all_workflows(self) -> list[dict]:
        """List all declarative workflows in data/workflows/."""
        wf_list = []
        for p in self._workflows_dir.glob("*.json"):
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                wf_list.append({
                    "id": data.get("id", p.stem),
                    "name": data.get("name", p.stem),
                    "description": data.get("description", ""),
                    "step_count": len(data.get("steps", [])),
                })
            except Exception:
                continue
        return wf_list

    def execute(self, action: str, params: dict[str, Any]) -> ToolResult:
        dispatch = {
            "run_workflow":       self._run_declarative_workflow,
            "list_workflows":     self._list_workflows,
            "create_workflow":   self._create_workflow,
            "interview_prep":     lambda p: self._run_declarative_workflow({"workflow_id": "interview_prep", **p}),
            "coding_environment": lambda p: self._run_declarative_workflow({"workflow_id": "coding_environment", **p}),
            "morning_routine":    lambda p: self._run_declarative_workflow({"workflow_id": "morning_routine", **p}),
            "focus_mode":         self._focus_mode,
        }
        fn = dispatch.get(action)
        if fn is None:
            return self._not_implemented(action)
        return fn(params)

    # ── Declarative Workflow Execution ───────────────────────────────────────

    def _run_declarative_workflow(self, p: dict) -> ToolResult:
        wf_id = p.get("workflow_id", "").strip()
        if not wf_id:
            return ToolResult.fail("Please specify a workflow_id.")

        wf = self._load_workflow(wf_id)
        if not wf:
            available = ", ".join(w["id"] for w in self._list_all_workflows())
            return ToolResult.fail(f"Workflow '{wf_id}' not found. Available workflows: {available}")

        steps = wf.get("steps", [])
        if not steps:
            return ToolResult.fail(f"Workflow '{wf_id}' contains no steps.")

        from core.execution_engine import execution_engine
        results = []
        for idx, step in enumerate(steps, 1):
            tool_name = step.get("tool")
            tool_action = step.get("action")
            step_params = step.get("params", {})
            step_name = step.get("step_name", f"Step {idx}")

            if not tool_name or not tool_action:
                continue

            logger.info("[Workflow:%s] Running Step %d: %s (%s.%s)", wf_id, idx, step_name, tool_name, tool_action)
            res = execution_engine.execute_action(tool_name, tool_action, step_params)
            results.append({
                "step": step_name,
                "tool_action": f"{tool_name}.{tool_action}",
                "success": res.success,
                "message": res.message,
            })

            time.sleep(0.3)

        success_count = sum(1 for r in results if r["success"])
        msg = f"Workflow '{wf.get('name', wf_id)}' completed: {success_count}/{len(results)} steps succeeded."
        return ToolResult.ok(msg, data={"workflow_id": wf_id, "steps": results})

    def _list_workflows(self, p: dict) -> ToolResult:
        wfs = self._list_all_workflows()
        names = ", ".join(f"{w['name']} ({w['id']})" for w in wfs)
        return ToolResult.ok(f"Available workflows ({len(wfs)}): {names}", data={"workflows": wfs})

    def _create_workflow(self, p: dict) -> ToolResult:
        wf_id = p.get("id", "").strip().lower().replace(" ", "_")
        name = p.get("name", "").strip()
        steps = p.get("steps", [])
        description = p.get("description", "")

        if not wf_id or not name or not steps:
            return ToolResult.fail("Please specify 'id', 'name', and 'steps' list.")

        wf_data = {
            "id": wf_id,
            "name": name,
            "description": description,
            "steps": steps,
        }

        file_path = self._workflows_dir / f"{wf_id}.json"
        file_path.write_text(json.dumps(wf_data, indent=2), encoding="utf-8")
        return ToolResult.ok(f"Workflow '{name}' ({wf_id}) created and saved.", data={"workflow": wf_data})

    def _focus_mode(self, p: dict) -> ToolResult:
        duration = p.get("duration", "25 minutes")
        from tools.utility_tool import UtilityTool
        util = UtilityTool()
        res = util.execute("set_timer", {"duration": duration, "label": "Focus Mode"})
        return ToolResult.ok(f"Focus mode activated for {duration}. {res.message}")
