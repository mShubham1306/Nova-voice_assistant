"""
NOVA Tool — Developer Workflow
Git operations, project startup, server management, and dev environment automation.
This is the tool that turns NOVA into a true developer assistant.
"""

from __future__ import annotations

import os
import subprocess
import time
import threading
from pathlib import Path
from typing import Any

from tools.base_tool import BaseTool, ToolResult, param


class DevTool(BaseTool):
    name = "dev_tool"
    description = (
        "Developer workflow automation: start project environments, run Git commands, "
        "launch dev servers, open IDEs, manage processes, and automate multi-step dev setups."
    )
    actions = [
        "start_project",
        "git_status",
        "git_log",
        "git_pull",
        "git_push",
        "git_branch",
        "git_diff",
        "run_command",
        "open_in_vscode",
        "start_server",
        "kill_port",
        "list_ports",
    ]
    parameters = {
        "start_project": {
            "project_name": param("string", "Name or path of the project to start", required=True),
            "profile": param(
                "string",
                "Startup profile: 'fastapi', 'react', 'fullstack', 'django', 'node', 'custom'",
                enum=["fastapi", "react", "fullstack", "django", "node", "custom"],
            ),
        },
        "git_status": {
            "project_path": param("string", "Path to the git repo (defaults to current project)"),
        },
        "git_log": {
            "project_path": param("string", "Path to the git repo"),
            "count": param("integer", "Number of commits to show (default 5)"),
        },
        "git_pull": {
            "project_path": param("string", "Path to the git repo"),
            "branch": param("string", "Branch to pull from (default: current branch)"),
        },
        "git_push": {
            "project_path": param("string", "Path to the git repo"),
            "message": param("string", "Commit message for any staged changes"),
        },
        "git_branch": {
            "project_path": param("string", "Path to the git repo"),
            "new_branch": param("string", "Name of the new branch to create (optional)"),
        },
        "git_diff": {
            "project_path": param("string", "Path to the git repo"),
        },
        "run_command": {
            "command": param("string", "Shell command to run", required=True),
            "cwd": param("string", "Working directory for the command"),
            "background": param("string", "Set to 'true' to run in background"),
        },
        "open_in_vscode": {
            "path": param("string", "File or folder path to open in VS Code"),
        },
        "start_server": {
            "server_type": param(
                "string",
                "Type of server to start",
                enum=["fastapi", "django", "react", "node", "vite", "mongodb", "redis"],
            ),
            "port": param("integer", "Port to run on"),
            "cwd": param("string", "Working directory"),
        },
        "kill_port": {
            "port": param("integer", "Port number to free up", required=True),
        },
        "list_ports": {},
    }
    dangerous_actions = ["kill_port", "run_command"]

    def __init__(self) -> None:
        from config import settings
        self._settings = settings

    def execute(self, action: str, params: dict[str, Any]) -> ToolResult:
        dispatch = {
            "start_project":   self._start_project,
            "git_status":      self._git_status,
            "git_log":         self._git_log,
            "git_pull":        self._git_pull,
            "git_push":        self._git_push,
            "git_branch":      self._git_branch,
            "git_diff":        self._git_diff,
            "run_command":     self._run_command,
            "open_in_vscode":  self._open_vscode,
            "start_server":    self._start_server,
            "kill_port":       self._kill_port,
            "list_ports":      self._list_ports,
        }
        fn = dispatch.get(action)
        if fn is None:
            return self._not_implemented(action)
        return fn(params)

    # ── Project Discovery ─────────────────────────────────────────────────────

    def _find_project(self, name: str) -> Path | None:
        """Search common project locations for a matching folder."""
        search_roots = [
            self._settings.PROJECTS_DIR,
            self._settings.DOCUMENTS_DIR,
            self._settings.USER_HOME / "projects",
            self._settings.USER_HOME / "code",
            self._settings.USER_HOME / "work",
            Path("C:/"),
        ]
        name_lower = name.lower()
        for root in search_roots:
            if not root.exists():
                continue
            try:
                for item in root.iterdir():
                    if item.is_dir() and name_lower in item.name.lower():
                        return item
            except PermissionError:
                continue
        # Try as direct path
        p = Path(name)
        if p.exists() and p.is_dir():
            return p
        return None

    # ── Start Project ─────────────────────────────────────────────────────────

    def _start_project(self, p: dict) -> ToolResult:
        project_name = p.get("project_name", "").strip()
        profile = p.get("profile", "fullstack").lower()

        project_path = self._find_project(project_name)
        if not project_path:
            return ToolResult.fail(
                f"Could not find project '{project_name}'. "
                "Check the name or specify a full path."
            )

        actions_done = []

        # Always: Open VS Code
        try:
            subprocess.Popen(f"code \"{project_path}\"", shell=True)
            actions_done.append("Opened VS Code")
            time.sleep(1)
        except Exception:
            pass

        # Profile-based startup
        if profile in ("fastapi", "fullstack"):
            self._run_in_terminal("python -m uvicorn main:app --reload", project_path)
            actions_done.append("Started FastAPI server")

        if profile in ("react", "fullstack"):
            frontend_paths = [project_path / "frontend", project_path / "client", project_path]
            for fp in frontend_paths:
                if (fp / "package.json").exists():
                    self._run_in_terminal("npm run dev", fp)
                    actions_done.append("Started React/Vite dev server")
                    break

        if profile == "django":
            self._run_in_terminal("python manage.py runserver", project_path)
            actions_done.append("Started Django dev server")

        if profile == "node":
            self._run_in_terminal("npm start", project_path)
            actions_done.append("Started Node.js server")

        # Open browser after a brief delay
        import webbrowser
        threading.Thread(
            target=lambda: (time.sleep(3), webbrowser.open("http://localhost:3000")),
            daemon=True
        ).start()
        actions_done.append("Opening browser at localhost:3000")

        return ToolResult.ok(
            f"Starting project '{project_path.name}': " + ", ".join(actions_done),
            data={"project": str(project_path), "actions": actions_done},
        )

    def _run_in_terminal(self, command: str, cwd: Path) -> None:
        """Open a new terminal window with the given command."""
        try:
            subprocess.Popen(
                f"start cmd /k cd /d \"{cwd}\" && {command}",
                shell=True
            )
        except Exception:
            pass

    # ── Git Operations ────────────────────────────────────────────────────────

    def _get_cwd(self, params: dict) -> Path:
        cwd = params.get("project_path") or params.get("cwd")
        if cwd:
            p = Path(cwd)
            if p.exists():
                return p
        return Path.cwd()

    def _git_run(self, args: list[str], cwd: Path) -> tuple[bool, str]:
        try:
            r = subprocess.run(
                ["git"] + args, capture_output=True, text=True, cwd=str(cwd)
            )
            return r.returncode == 0, (r.stdout + r.stderr).strip()
        except FileNotFoundError:
            return False, "Git is not installed or not in PATH."

    def _git_status(self, p: dict) -> ToolResult:
        cwd = self._get_cwd(p)
        ok, output = self._git_run(["status", "--short"], cwd)
        if not ok:
            return ToolResult.fail(f"Git status failed: {output}")
        if not output:
            return ToolResult.ok("Working tree is clean — no changes.", data={"status": "clean"})
        line_count = output.count("\n") + 1
        return ToolResult.ok(
            f"{line_count} changed file(s). Run 'git diff' for details.",
            data={"status": output},
        )

    def _git_log(self, p: dict) -> ToolResult:
        cwd = self._get_cwd(p)
        count = int(p.get("count", 5))
        ok, output = self._git_run(
            ["log", f"-{count}", "--oneline", "--decorate"], cwd
        )
        if not ok:
            return ToolResult.fail(f"Git log failed: {output}")
        commits = [line.strip() for line in output.splitlines() if line.strip()]
        msg = f"Last {len(commits)} commit(s): " + "; ".join(commits[:2])
        if len(commits) > 2:
            msg += f" and {len(commits) - 2} more."
        return ToolResult.ok(msg, data={"commits": commits})

    def _git_pull(self, p: dict) -> ToolResult:
        cwd = self._get_cwd(p)
        branch = p.get("branch", "")
        args = ["pull"]
        if branch:
            args += ["origin", branch]
        ok, output = self._git_run(args, cwd)
        if ok:
            return ToolResult.ok(f"Git pull successful. {output[:100]}", data={"output": output})
        return ToolResult.fail(f"Git pull failed: {output}")

    def _git_push(self, p: dict) -> ToolResult:
        cwd = self._get_cwd(p)
        message = p.get("message", "")
        if message:
            # Stage all and commit first
            self._git_run(["add", "."], cwd)
            self._git_run(["commit", "-m", message], cwd)
        ok, output = self._git_run(["push"], cwd)
        if ok:
            return ToolResult.ok("Pushed to remote successfully.", data={"output": output})
        return ToolResult.fail(f"Git push failed: {output}")

    def _git_branch(self, p: dict) -> ToolResult:
        cwd = self._get_cwd(p)
        new_branch = p.get("new_branch", "")
        if new_branch:
            ok, out = self._git_run(["checkout", "-b", new_branch], cwd)
            if ok:
                return ToolResult.ok(f"Created and switched to branch '{new_branch}'.")
            return ToolResult.fail(f"Could not create branch: {out}")
        ok, out = self._git_run(["branch", "--show-current"], cwd)
        all_ok, all_out = self._git_run(["branch"], cwd)
        branches = [b.strip().lstrip("* ") for b in all_out.splitlines()]
        return ToolResult.ok(
            f"Current branch: {out.strip()}. All branches: {', '.join(branches)}",
            data={"current": out.strip(), "branches": branches},
        )

    def _git_diff(self, p: dict) -> ToolResult:
        cwd = self._get_cwd(p)
        ok, output = self._git_run(["diff", "--stat"], cwd)
        if not ok or not output:
            return ToolResult.ok("No diff — working tree is clean.", data={"diff": ""})
        return ToolResult.ok(f"Changes: {output[:200]}", data={"diff": output}, speak=False)

    # ── General Command ───────────────────────────────────────────────────────

    def _run_command(self, p: dict) -> ToolResult:
        command = p.get("command", "").strip()
        cwd_str = p.get("cwd", "").strip()
        background = str(p.get("background", "false")).lower() == "true"
        if not command:
            return ToolResult.fail("Please provide a command to run.")
        cwd = Path(cwd_str) if cwd_str and Path(cwd_str).exists() else Path.cwd()
        try:
            if background:
                subprocess.Popen(command, shell=True, cwd=str(cwd))
                return ToolResult.ok(f"Running in background: {command}")
            r = subprocess.run(command, shell=True, capture_output=True, text=True, cwd=str(cwd), timeout=30)
            output = (r.stdout + r.stderr).strip()
            success = r.returncode == 0
            msg = f"Command finished. " + (output[:200] if output else "No output.")
            return ToolResult.ok(msg, data={"output": output, "returncode": r.returncode}) if success \
                else ToolResult.fail(f"Command failed: {output[:200]}")
        except subprocess.TimeoutExpired:
            return ToolResult.fail("Command timed out after 30 seconds.")
        except Exception as e:
            return ToolResult.fail(f"Command error: {e}")

    # ── IDE & Server ──────────────────────────────────────────────────────────

    def _open_vscode(self, p: dict) -> ToolResult:
        path = p.get("path", "").strip() or "."
        try:
            subprocess.Popen(f"code \"{path}\"", shell=True)
            return ToolResult.ok(f"Opened '{path}' in VS Code.")
        except Exception as e:
            return ToolResult.fail(f"Could not open VS Code: {e}")

    def _start_server(self, p: dict) -> ToolResult:
        stype = p.get("server_type", "").lower()
        port = p.get("port")
        cwd = p.get("cwd", ".")

        commands = {
            "fastapi":  f"uvicorn main:app --reload{f' --port {port}' if port else ''}",
            "django":   f"python manage.py runserver{f' {port}' if port else ''}",
            "react":    "npm start",
            "node":     "node index.js",
            "vite":     f"npm run dev{f' -- --port {port}' if port else ''}",
            "mongodb":  "mongod",
            "redis":    "redis-server",
        }
        cmd = commands.get(stype)
        if not cmd:
            return ToolResult.fail(f"Unknown server type '{stype}'. Try: fastapi, react, node, django, vite, mongodb, redis.")
        self._run_in_terminal(cmd, Path(cwd))
        return ToolResult.ok(f"Starting {stype} server{f' on port {port}' if port else ''}.")

    # ── Port Management ───────────────────────────────────────────────────────

    def _kill_port(self, p: dict) -> ToolResult:
        port = p.get("port")
        if not port:
            return ToolResult.fail("Please specify the port number.")
        r = subprocess.run(
            f"netstat -ano | findstr :{port}", shell=True, capture_output=True, text=True
        )
        if not r.stdout.strip():
            return ToolResult.ok(f"No process found on port {port}.")
        pids = set()
        for line in r.stdout.splitlines():
            parts = line.split()
            if parts:
                pids.add(parts[-1])
        for pid in pids:
            subprocess.run(f"taskkill /f /pid {pid}", shell=True, capture_output=True)
        return ToolResult.ok(f"Freed port {port}. Killed PID(s): {', '.join(pids)}.")

    def _list_ports(self, p: dict) -> ToolResult:
        r = subprocess.run(
            "netstat -ano | findstr LISTENING", shell=True, capture_output=True, text=True
        )
        lines = r.stdout.splitlines()[:20]
        ports = []
        for line in lines:
            parts = line.split()
            if len(parts) >= 2:
                addr = parts[1]
                port = addr.split(":")[-1]
                if port.isdigit():
                    ports.append(port)
        ports = sorted(set(ports))
        msg = f"Active listening ports: {', '.join(ports[:15])}" if ports else "No listening ports found."
        return ToolResult.ok(msg, data={"ports": ports}, speak=False)
