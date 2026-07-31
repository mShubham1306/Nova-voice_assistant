"""
NOVA Core — Background Task Manager
Asynchronous background task runner for long-running operations (drive scanning, indexing, cleanup).

Non-blocking background execution with progress tracking (0% to 100%) and Event Bus progress notifications.
"""

from __future__ import annotations

import concurrent.futures
import datetime
import logging
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable

from core.event_bus import event_bus
from tools.base_tool import ToolResult

logger = logging.getLogger("nova.task_manager")


@dataclass
class AsyncTask:
    """Represents a background task."""
    id: str
    name: str
    tool: str
    action: str
    status: str = "queued"  # "queued" | "running" | "completed" | "failed"
    progress: int = 0      # 0 to 100
    message: str = "Task queued..."
    result: dict[str, Any] | None = None
    started_at: str = field(default_factory=lambda: datetime.datetime.now().isoformat())
    completed_at: str | None = None


class TaskManager:
    """
    Background worker pool that executes long operations asynchronously
    and emits progress events to the Event Bus and WebSockets.
    """

    def __init__(self, max_workers: int = 4) -> None:
        self._pool = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="nova_bg_task_")
        self._tasks: dict[str, AsyncTask] = {}

    def submit_task(
        self,
        name: str,
        tool: str,
        action: str,
        func: Callable[[Callable[[int, str], None]], ToolResult],
    ) -> AsyncTask:
        """
        Submit a long-running function to run in the background.
        The function receives a `update_progress(pct, msg)` callback.
        """
        task_id = str(uuid.uuid4())[:8]
        task = AsyncTask(id=task_id, name=name, tool=tool, action=action)
        self._tasks[task_id] = task

        logger.info("[TaskManager] Submitted background task %s (%s)", task_id, name)
        event_bus.publish("task_submitted", {"task_id": task_id, "name": name})

        self._pool.submit(self._run_task, task_id, func)
        return task

    def _run_task(
        self,
        task_id: str,
        func: Callable[[Callable[[int, str], None]], ToolResult],
    ) -> None:
        task = self._tasks.get(task_id)
        if not task:
            return

        task.status = "running"
        event_bus.publish("task_started", {"task_id": task_id, "name": task.name})

        def progress_callback(pct: int, msg: str) -> None:
            task.progress = min(100, max(0, pct))
            task.message = msg
            event_bus.publish("task_progress", {
                "task_id": task_id,
                "name": task.name,
                "progress": task.progress,
                "message": msg,
            })

        try:
            result = func(progress_callback)
            task.status = "completed" if result.success else "failed"
            task.progress = 100
            task.message = result.message
            task.result = result.to_dict()
            task.completed_at = datetime.datetime.now().isoformat()

            event_bus.publish("task_completed", {
                "task_id": task_id,
                "name": task.name,
                "success": result.success,
                "message": result.message,
            })
        except Exception as exc:
            logger.exception("[TaskManager] Background task %s failed", task_id)
            task.status = "failed"
            task.message = f"Task failed: {exc}"
            task.completed_at = datetime.datetime.now().isoformat()

            event_bus.publish("task_failed", {
                "task_id": task_id,
                "name": task.name,
                "error": str(exc),
            })

    def get_task(self, task_id: str) -> AsyncTask | None:
        return self._tasks.get(task_id)

    def list_tasks(self) -> list[dict]:
        return [
            {
                "id": t.id,
                "name": t.name,
                "tool": t.tool,
                "action": t.action,
                "status": t.status,
                "progress": t.progress,
                "message": t.message,
                "started_at": t.started_at,
                "completed_at": t.completed_at,
            }
            for t in self._tasks.values()
        ]


# Singleton instance
task_manager = TaskManager()
