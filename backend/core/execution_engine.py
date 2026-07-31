"""
NOVA Core — Execution Engine
Centralized command execution engine for NOVA 3.0.

Responsibility:
  • Validation: Parameter presence and type checking
  • Permission Guard & Safety Interceptor: Intercepts dangerous actions, queues pending confirmation
  • Retry Logic: Automatic retries with backoff for transient tool errors
  • Timeout Protection: Guards against hung tool execution
  • Event Bus Dispatch: Publishes events for observability
  • Audit Logging: Logs every execution attempt and result
"""

from __future__ import annotations

import concurrent.futures
import datetime
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable

from core.event_bus import event_bus
from tools.base_tool import ToolResult
from tools.registry import registry

logger = logging.getLogger("nova.execution_engine")


@dataclass
class PendingAction:
    """Represents a dangerous action waiting for user confirmation."""
    id: str
    tool: str
    action: str
    params: dict[str, Any]
    prompt: str
    requested_at: str = field(default_factory=lambda: datetime.datetime.now().isoformat())


class ExecutionEngine:
    """
    The central execution authority.
    Intercepts and manages all tool calls from Gemini and Fast Router.
    """

    def __init__(self, timeout_seconds: float = 15.0, max_retries: int = 1) -> None:
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self._pending_confirmations: dict[str, PendingAction] = {}
        self._thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=8, thread_name_prefix="nova_exec_")

    # ── Confirmation Management ───────────────────────────────────────────────

    def get_pending_confirmations(self) -> list[dict]:
        """Return list of actions currently waiting for user approval."""
        return [
            {
                "id": pa.id,
                "tool": pa.tool,
                "action": pa.action,
                "params": pa.params,
                "prompt": pa.prompt,
                "requested_at": pa.requested_at,
            }
            for pa in self._pending_confirmations.values()
        ]

    def confirm_action(self, confirmation_id: str, approved: bool = True) -> ToolResult:
        """Execute or cancel a pending dangerous action after user confirmation."""
        pending = self._pending_confirmations.pop(confirmation_id, None)
        if not pending:
            return ToolResult.fail(f"Confirmation ID '{confirmation_id}' not found or expired.")

        if not approved:
            event_bus.publish("danger_action_cancelled", {"tool": pending.tool, "action": pending.action})
            return ToolResult.ok(f"Action '{pending.tool}.{pending.action}' cancelled by user.")

        logger.info("[ExecutionEngine] User approved pending action %s (%s.%s)", confirmation_id, pending.tool, pending.action)
        # Execute bypassing danger guard
        return self._execute_direct(pending.tool, pending.action, pending.params, is_confirmed=True)

    # ── Parameter Validation ──────────────────────────────────────────────────

    def _validate_params(self, tool_name: str, action: str, params: dict) -> tuple[bool, str]:
        tool = registry.get_tool(tool_name)
        if not tool:
            return False, f"Unknown tool '{tool_name}'"

        if action not in tool.actions:
            return False, f"Action '{action}' is not supported by tool '{tool_name}'"

        action_schema = tool.parameters.get(action, {})
        for param_name, schema in action_schema.items():
            if schema.get("required") and param_name not in params:
                return False, f"Missing required parameter '{param_name}' for {tool_name}.{action}"

        return True, "Valid"

    # ── Primary Execution Method ──────────────────────────────────────────────

    def execute_action(
        self,
        tool_name: str,
        action: str,
        params: dict[str, Any] | None = None,
        bypass_confirmation: bool = False,
    ) -> ToolResult:
        """
        Public entry point to execute any tool action through the full pipeline:
        Validation → Permission Interceptor → Timeout → Retry → Event Bus.
        """
        params = params or {}

        # 1. Validation
        valid, reason = self._validate_params(tool_name, action, params)
        if not valid:
            logger.warning("[ExecutionEngine] Validation failed for %s.%s: %s", tool_name, action, reason)
            return ToolResult.fail(f"Invalid request: {reason}")

        # 2. Safety & Permission Interceptor
        is_dangerous = registry.is_dangerous(tool_name, action)
        if is_dangerous and not bypass_confirmation:
            confirm_id = str(uuid.uuid4())[:8]
            prompt = f"Safety Check: Are you sure you want to perform '{tool_name}.{action}' with parameters {params}?"
            pending = PendingAction(
                id=confirm_id, tool=tool_name, action=action, params=params, prompt=prompt
            )
            self._pending_confirmations[confirm_id] = pending

            event_bus.publish("danger_action_requested", {
                "confirmation_id": confirm_id,
                "tool": tool_name,
                "action": action,
                "params": params,
                "prompt": prompt,
            })

            result = ToolResult.confirm(prompt, action=f"{tool_name}.{action}")
            result.data["confirmation_id"] = confirm_id
            return result

        # 3. Direct execution with timeout and retries
        return self._execute_direct(tool_name, action, params)

    def _execute_direct(
        self,
        tool_name: str,
        action: str,
        params: dict[str, Any],
        is_confirmed: bool = False,
    ) -> ToolResult:
        event_bus.publish("tool_executing", {"tool": tool_name, "action": action, "params": params})

        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                # Run execution in thread pool with strict timeout
                future = self._thread_pool.submit(registry.execute, tool_name, action, params)
                result: ToolResult = future.result(timeout=self.timeout_seconds)

                # Event Bus dispatch based on result action
                self._dispatch_event(tool_name, action, result, params)
                return result

            except concurrent.futures.TimeoutError:
                last_error = f"Execution of {tool_name}.{action} timed out after {self.timeout_seconds}s."
                logger.error("[ExecutionEngine] %s", last_error)
                event_bus.publish("tool_timeout", {"tool": tool_name, "action": action})

            except Exception as exc:
                last_error = str(exc)
                logger.warning("[ExecutionEngine] Attempt %d failed for %s.%s: %s", attempt + 1, tool_name, action, exc)
                time.sleep(0.2 * (2 ** attempt))

        result = ToolResult.fail(f"Failed to execute {tool_name}.{action}: {last_error}")
        event_bus.publish("tool_failed", {"tool": tool_name, "action": action, "error": last_error})
        return result

    # ── Event Dispatcher ──────────────────────────────────────────────────────

    def _dispatch_event(self, tool_name: str, action: str, result: ToolResult, params: dict) -> None:
        """Publish granular domain events over the Event Bus."""
        event_bus.publish("tool_executed", {
            "tool": tool_name,
            "action": action,
            "success": result.success,
            "message": result.message,
            "params": params,
        })

        # Specialized domain events for app/file/music/dev actions
        if action == "open_app" and result.success:
            event_bus.publish("app_opened", {"app": params.get("app_name")})

        elif action in ("open_file", "search_file") and result.success:
            event_bus.publish("file_accessed", {"filename": params.get("filename") or params.get("query")})

        elif action in ("play_pause", "play_on_youtube", "play_on_spotify") and result.success:
            event_bus.publish("music_playback_changed", {"query": params.get("query")})

        elif action == "start_project" and result.success:
            event_bus.publish("project_started", {"project": params.get("project_name")})


# Singleton instance
execution_engine = ExecutionEngine()
