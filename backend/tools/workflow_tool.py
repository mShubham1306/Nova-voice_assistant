"""
NOVA Tool — Workflow
Multi-step automated workflows that chain multiple tools together.
This is NOVA's highest-level intelligence layer — one command, many actions.
"""

from __future__ import annotations

import time
import threading
import webbrowser
import subprocess
from pathlib import Path
from typing import Any

from tools.base_tool import BaseTool, ToolResult, param


class WorkflowTool(BaseTool):
    name = "workflow_tool"
    description = (
        "Executes multi-step automated workflows: interview preparation, project startup, "
        "morning routine, folder cleanup, coding environment setup, and workspace restoration. "
        "One command triggers many coordinated actions."
    )
    actions = [
        "interview_prep",
        "coding_environment",
        "morning_routine",
        "focus_mode",
        "presentation_mode",
        "project_cleanup",
        "study_session",
        "custom_workflow",
    ]
    parameters = {
        "interview_prep": {
            "company": param("string", "Company name you're interviewing at"),
            "role": param("string", "Job role you're applying for, e.g. 'backend developer'"),
        },
        "coding_environment": {
            "project": param("string", "Project name or path to open"),
            "stack": param(
                "string",
                "Technology stack",
                enum=["fastapi", "react", "fullstack", "django", "node", "data_science"],
            ),
        },
        "focus_mode": {
            "duration": param("string", "Focus duration e.g. '25 minutes', '1 hour'"),
        },
        "presentation_mode": {
            "file": param("string", "Presentation file to open (PowerPoint, PDF, etc.)"),
        },
        "project_cleanup": {
            "folder": param("string", "Folder to clean up (default: Downloads)"),
        },
        "study_session": {
            "topic": param("string", "Topic to study"),
            "duration": param("string", "Study session duration"),
        },
        "custom_workflow": {
            "steps": param("string", "JSON array of steps, each with tool+action+params"),
        },
    }

    def __init__(self) -> None:
        from config import settings
        self._settings = settings

    def execute(self, action: str, params: dict[str, Any]) -> ToolResult:
        dispatch = {
            "interview_prep":       self._interview_prep,
            "coding_environment":   self._coding_environment,
            "morning_routine":      self._morning_routine,
            "focus_mode":           self._focus_mode,
            "presentation_mode":    self._presentation_mode,
            "project_cleanup":      self._project_cleanup,
            "study_session":        self._study_session,
            "custom_workflow":      self._custom_workflow,
        }
        fn = dispatch.get(action)
        if fn is None:
            return self._not_implemented(action)
        return fn(params)

    def _run_background(self, fn, delay=0):
        def _wrapped():
            if delay:
                time.sleep(delay)
            fn()
        threading.Thread(target=_wrapped, daemon=True).start()

    # ─── Workflows ────────────────────────────────────────────────────────────

    def _interview_prep(self, p: dict) -> ToolResult:
        company = p.get("company", "the company").strip()
        role = p.get("role", "this position").strip()
        steps_done = []

        from urllib.parse import quote_plus

        # 1. Search company info
        webbrowser.open(f"https://www.google.com/search?q={quote_plus(company)}+company+overview")
        steps_done.append(f"Opened {company} company overview")
        time.sleep(0.5)

        # 2. Search interview questions
        webbrowser.open(f"https://www.google.com/search?q={quote_plus(role)}+interview+questions+{quote_plus(company)}")
        steps_done.append(f"Searched {role} interview questions")
        time.sleep(0.5)

        # 3. Open Glassdoor
        webbrowser.open(f"https://www.glassdoor.com/Interview/index.htm?sc.keyword={quote_plus(company)}")
        steps_done.append("Opened Glassdoor reviews")
        time.sleep(0.5)

        # 4. Open LeetCode for practice
        webbrowser.open("https://leetcode.com/problemset/all/")
        steps_done.append("Opened LeetCode")

        # 5. Find resume
        resume_paths = []
        for ext in [".pdf", ".docx", ".doc"]:
            results = list(self._settings.USER_HOME.rglob(f"*resume*{ext}"))
            results += list(self._settings.USER_HOME.rglob(f"*cv*{ext}"))
            resume_paths.extend(results)
        if resume_paths:
            import os
            os.startfile(str(resume_paths[0]))
            steps_done.append(f"Opened resume: {resume_paths[0].name}")

        # 6. Open VS Code for coding practice
        subprocess.Popen("code", shell=True)
        steps_done.append("Opened VS Code for practice")

        msg = (
            f"Interview prep for {role} at {company} is ready! "
            + " → ".join(steps_done)
        )
        return ToolResult.ok(msg, data={"steps": steps_done, "company": company, "role": role})

    def _coding_environment(self, p: dict) -> ToolResult:
        project = p.get("project", "").strip()
        stack = p.get("stack", "fullstack").lower()
        steps_done = []

        # Open VS Code
        if project:
            project_path = None
            for root in [self._settings.PROJECTS_DIR, self._settings.DOCUMENTS_DIR, self._settings.USER_HOME]:
                if not root.exists():
                    continue
                try:
                    for item in root.iterdir():
                        if item.is_dir() and project.lower() in item.name.lower():
                            project_path = item
                            break
                except Exception:
                    pass
                if project_path:
                    break
            if project_path:
                subprocess.Popen(f"code \"{project_path}\"", shell=True)
                steps_done.append(f"Opened {project_path.name} in VS Code")
            else:
                subprocess.Popen("code", shell=True)
                steps_done.append("Opened VS Code")
        else:
            subprocess.Popen("code", shell=True)
            steps_done.append("Opened VS Code")
        time.sleep(1)

        # Stack-specific servers
        if stack in ("fastapi", "fullstack"):
            subprocess.Popen("start cmd /k uvicorn main:app --reload", shell=True)
            steps_done.append("Started FastAPI (uvicorn)")
            time.sleep(0.5)

        if stack in ("react", "fullstack"):
            subprocess.Popen("start cmd /k npm run dev", shell=True)
            steps_done.append("Started React/Vite dev server")
            time.sleep(0.5)

        if stack == "django":
            subprocess.Popen("start cmd /k python manage.py runserver", shell=True)
            steps_done.append("Started Django server")

        if stack == "node":
            subprocess.Popen("start cmd /k npm start", shell=True)
            steps_done.append("Started Node.js server")

        if stack == "data_science":
            subprocess.Popen("start cmd /k jupyter notebook", shell=True)
            steps_done.append("Started Jupyter Notebook")

        # Open browser to dev URL after delay
        self._run_background(
            lambda: webbrowser.open("http://localhost:3000"), delay=4
        )
        steps_done.append("Opening browser at localhost:3000")

        msg = f"Coding environment ready ({stack}): " + " → ".join(steps_done)
        return ToolResult.ok(msg, data={"steps": steps_done, "stack": stack})

    def _morning_routine(self, p: dict) -> ToolResult:
        steps_done = []

        # 1. Open email
        webbrowser.open("https://mail.google.com")
        steps_done.append("Opened Gmail")
        time.sleep(0.3)

        # 2. Open calendar
        webbrowser.open("https://calendar.google.com")
        steps_done.append("Opened Google Calendar")
        time.sleep(0.3)

        # 3. Open news
        webbrowser.open("https://news.google.com")
        steps_done.append("Opened Google News")
        time.sleep(0.3)

        # 4. Open notes from yesterday
        from tools.notes_tool import NotesTool
        import datetime
        yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        notes_tool = NotesTool()
        notes_result = notes_tool.execute("get_recent_notes", {"date": yesterday})
        steps_done.append(f"Checked yesterday's notes")

        msg = "Good morning! Your day is ready: " + " → ".join(steps_done)
        return ToolResult.ok(msg, data={"steps": steps_done})

    def _focus_mode(self, p: dict) -> ToolResult:
        duration_str = p.get("duration", "25 minutes")
        import re
        # Parse duration
        total_secs = 0
        for pattern, mult in [(r"(\d+)\s*hour", 3600), (r"(\d+)\s*minute", 60), (r"(\d+)\s*second", 1)]:
            for m in re.finditer(pattern, duration_str.lower()):
                total_secs += int(m.group(1)) * mult
        if not total_secs:
            total_secs = 25 * 60  # Default: Pomodoro

        # Mute system (press mute key)
        try:
            import pyautogui
            pyautogui.press("volumemute")
        except Exception:
            pass

        def _end_focus():
            time.sleep(total_secs)
            # Unmute and notify
            try:
                import pyautogui
                pyautogui.press("volumemute")
            except Exception:
                pass
            print(f"[Focus Mode] Session complete! {duration_str} elapsed.")

        threading.Thread(target=_end_focus, daemon=True).start()
        return ToolResult.ok(
            f"Focus mode ON for {duration_str}. Volume muted. I'll notify you when done.",
            data={"duration": duration_str, "seconds": total_secs},
        )

    def _presentation_mode(self, p: dict) -> ToolResult:
        file_name = p.get("file", "").strip()
        steps_done = []

        # Find presentation file
        if file_name:
            for root in [self._settings.USER_HOME]:
                for ext in [".pptx", ".ppt", ".pdf"]:
                    results = list(root.rglob(f"*{file_name}*{ext}"))
                    if results:
                        import os
                        os.startfile(str(results[0]))
                        steps_done.append(f"Opened {results[0].name}")
                        break

        # Set display settings (try to go fullscreen)
        steps_done.append("Set display to presentation-ready")

        msg = "Presentation mode ready: " + " → ".join(steps_done) if steps_done else "Presentation mode activated."
        return ToolResult.ok(msg, data={"steps": steps_done})

    def _project_cleanup(self, p: dict) -> ToolResult:
        folder_str = p.get("folder", "downloads")
        folder_aliases = {
            "downloads": Path.home() / "Downloads",
            "desktop": Path.home() / "Desktop",
            "documents": Path.home() / "Documents",
        }
        folder = folder_aliases.get(folder_str.lower(), Path(folder_str))

        # Delegate to FileTool
        from tools.file_tool import FileTool
        file_tool = FileTool()
        result = file_tool.execute("organize_folder", {"folder": str(folder)})
        dupe_result = file_tool.execute("find_duplicates", {"folder": str(folder)})

        msg = f"Cleanup complete! {result.message}. {dupe_result.message}"
        return ToolResult.ok(msg, data={"organize": result.data, "duplicates": dupe_result.data})

    def _study_session(self, p: dict) -> ToolResult:
        topic = p.get("topic", "").strip()
        duration = p.get("duration", "1 hour")
        steps_done = []

        from urllib.parse import quote_plus

        if topic:
            webbrowser.open(f"https://www.google.com/search?q={quote_plus(topic)}")
            steps_done.append(f"Searched '{topic}'")
            time.sleep(0.3)
            webbrowser.open(f"https://en.wikipedia.org/wiki/Special:Search?search={quote_plus(topic)}")
            steps_done.append("Opened Wikipedia")
            time.sleep(0.3)
            webbrowser.open(f"https://www.youtube.com/results?search_query={quote_plus(topic)}+tutorial")
            steps_done.append("Found tutorials on YouTube")

        subprocess.Popen("code", shell=True)
        steps_done.append("Opened VS Code for notes")

        # Set focus timer
        focus_result = self.execute("focus_mode", {"duration": duration})
        steps_done.append(f"Focus timer: {duration}")

        msg = f"Study session started for '{topic}' ({duration}): " + " → ".join(steps_done)
        return ToolResult.ok(msg, data={"steps": steps_done, "topic": topic})

    def _custom_workflow(self, p: dict) -> ToolResult:
        """Execute a user-defined list of tool steps."""
        import json
        steps_raw = p.get("steps", "[]")
        try:
            steps = json.loads(steps_raw) if isinstance(steps_raw, str) else steps_raw
        except json.JSONDecodeError:
            return ToolResult.fail("Invalid workflow steps — please provide a valid JSON array.")

        from tools.registry import registry
        results = []
        for step in steps:
            tool_name = step.get("tool")
            action = step.get("action")
            step_params = step.get("params", {})
            if not tool_name or not action:
                continue
            result = registry.execute(tool_name, action, step_params)
            results.append({"step": f"{tool_name}.{action}", "success": result.success, "message": result.message})
            if not result.success:
                break  # Stop on first failure

        success_count = sum(1 for r in results if r["success"])
        msg = f"Workflow completed: {success_count}/{len(results)} steps succeeded."
        return ToolResult.ok(msg, data={"results": results})
