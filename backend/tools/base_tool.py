"""
BaseTool — Abstract base class every NOVA tool must implement.

Design goals:
  • Each tool is a fully self-contained "service" with typed actions.
  • Tools self-describe via get_schema() which is fed to Gemini as
    function-calling declarations — Gemini knows exactly what each tool
    can do without any hardcoded prompts.
  • execute() is the single entry point; routing to the right method
    happens inside each tool.
  • ToolResult is a standard dataclass returned by every action so the
    Assistant can speak, emit, and log in a uniform way.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("nova.tool")


# ─── Standard Result Object ───────────────────────────────────────────────────

@dataclass
class ToolResult:
    """Uniform response from every tool action."""
    success: bool
    message: str                        # Human-readable response (spoken + shown)
    data: dict[str, Any] = field(default_factory=dict)   # Extra structured data for frontend
    action_taken: str = ""              # e.g. "file_tool.open_file" — for memory/history
    speak: bool = True                  # Set False for silent background actions
    requires_confirmation: bool = False # If True, frontend must confirm before executing
    confirmation_prompt: str = ""       # What to ask the user

    @classmethod
    def ok(cls, message: str, data: dict | None = None, action: str = "", speak: bool = True) -> "ToolResult":
        return cls(success=True, message=message, data=data or {}, action_taken=action, speak=speak)

    @classmethod
    def fail(cls, message: str, data: dict | None = None, action: str = "") -> "ToolResult":
        return cls(success=False, message=message, data=data or {}, action_taken=action, speak=True)

    @classmethod
    def confirm(cls, prompt: str, action: str = "") -> "ToolResult":
        """Request user confirmation before proceeding."""
        return cls(
            success=False,
            message=prompt,
            action_taken=action,
            requires_confirmation=True,
            confirmation_prompt=prompt,
            speak=True,
        )

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "message": self.message,
            "data": self.data,
            "action_taken": self.action_taken,
            "speak": self.speak,
            "requires_confirmation": self.requires_confirmation,
            "confirmation_prompt": self.confirmation_prompt,
        }


# ─── Parameter Schema Helper ─────────────────────────────────────────────────

def param(
    ptype: str,
    description: str,
    enum: list[str] | None = None,
    required: bool = False,
) -> dict:
    """Helper to build a Gemini-compatible parameter schema entry."""
    schema: dict[str, Any] = {"type": ptype, "description": description}
    if enum:
        schema["enum"] = enum
    return schema


# ─── BaseTool ABC ─────────────────────────────────────────────────────────────

class BaseTool(ABC):
    """
    Every NOVA tool must subclass this and implement:
      - name         : unique snake_case identifier  e.g. "file_tool"
      - description  : what this tool does           (fed to Gemini)
      - actions      : list of action strings        (fed to Gemini)
      - parameters   : dict of param schemas per action
      - execute()    : routes action → method and returns ToolResult
    """

    # ── Subclass must define these ──────────────────────────────────────────

    #: Unique tool name used by Gemini and the registry
    name: str = ""

    #: One-sentence description fed to Gemini as the function description
    description: str = ""

    #: List of action strings this tool supports
    actions: list[str] = []

    #: Per-action parameter schemas for Gemini function calling
    parameters: dict[str, dict[str, dict]] = {}

    #: Actions that need confirmation before executing (e.g. delete, shutdown)
    dangerous_actions: list[str] = []

    #: Plugin Version (default 2.0.0)
    version: str = "2.0.0"

    #: Execution Priority (1-100, higher = tried first if tools conflict)
    priority: int = 50

    # ── Interface ────────────────────────────────────────────────────────────

    @abstractmethod
    def execute(self, action: str, params: dict[str, Any]) -> ToolResult:
        """
        Route the action to the correct internal method.
        All tools must implement this as their single public entry point.
        """

    def dependencies_satisfied(self) -> tuple[bool, str]:
        """Check if all OS/Python dependencies for this tool are met."""
        return True, "All dependencies met."

    def health(self) -> dict:
        """Return diagnostic health check metadata for this tool."""
        satisfied, reason = self.dependencies_satisfied()
        status = "healthy" if satisfied else "degraded"
        return {
            "name": self.name,
            "version": self.version,
            "priority": self.priority,
            "status": status,
            "reason": reason,
            "action_count": len(self.actions),
            "dangerous_actions": self.dangerous_actions,
        }


    # ── Auto-derived helpers ─────────────────────────────────────────────────

    def get_schema(self) -> dict:
        """
        Returns a Gemini-compatible function declaration dict.
        This is what gets passed to the model so it knows what this tool does.
        """
        properties: dict[str, Any] = {
            "tool": {"type": "string", "enum": [self.name], "description": "Which tool to use"},
            "action": {"type": "string", "enum": self.actions, "description": "Which action to perform"},
        }
        required_base = ["tool", "action"]

        # Merge all action parameters into the top-level properties
        # (Gemini uses a flat parameter space per function)
        all_params: dict[str, Any] = {}
        for action_params in self.parameters.values():
            for k, v in action_params.items():
                all_params[k] = v

        properties.update(all_params)

        return {
            "name": self.name,
            "description": f"{self.description} Supported actions: {', '.join(self.actions)}.",
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required_base,
            },
        }

    def is_dangerous(self, action: str) -> bool:
        return action in self.dangerous_actions

    def _not_implemented(self, action: str) -> ToolResult:
        return ToolResult.fail(f"Action '{action}' is not yet implemented in {self.name}.")

    def __repr__(self) -> str:
        return f"<Tool:{self.name} actions={self.actions}>"
