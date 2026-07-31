"""
NOVA Tool Registry — Auto-discovers and manages all tools.

How it works:
  1. On startup, scans the tools/ directory for any *_tool.py file.
  2. Imports each module and finds subclasses of BaseTool.
  3. Registers them by name — no manual imports needed.
  4. Exposes get_all_schemas() for Gemini function-calling declarations.
  5. Exposes execute(tool_name, action, params) as the single dispatch point.
"""

from __future__ import annotations

import importlib
import inspect
import logging
import pkgutil
from pathlib import Path
from typing import TYPE_CHECKING

from tools.base_tool import BaseTool, ToolResult

if TYPE_CHECKING:
    pass

logger = logging.getLogger("nova.registry")


class ToolRegistry:
    """
    Singleton registry that holds all discovered tools.
    New tools are auto-loaded — drop a *_tool.py file and restart NOVA.
    """

    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}
        self._load_all_tools()

    # ── Discovery ─────────────────────────────────────────────────────────────

    def _load_all_tools(self) -> None:
        """Scan tools/ package, import every module, find BaseTool subclasses."""
        tools_pkg_path = Path(__file__).parent
        package_name = "tools"

        for finder, module_name, is_pkg in pkgutil.iter_modules([str(tools_pkg_path)]):
            if not module_name.endswith("_tool"):
                continue  # Skip base_tool, registry, __init__

            full_name = f"{package_name}.{module_name}"
            try:
                module = importlib.import_module(full_name)
            except Exception as exc:
                logger.warning("Could not import %s: %s", full_name, exc)
                continue

            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (
                    inspect.isclass(attr)
                    and issubclass(attr, BaseTool)
                    and attr is not BaseTool
                    and not inspect.isabstract(attr)
                ):
                    try:
                        instance: BaseTool = attr()
                        if instance.name:
                            self._tools[instance.name] = instance
                            logger.info("Registered tool: %s (%d actions)", instance.name, len(instance.actions))
                    except Exception as exc:
                        logger.warning("Could not instantiate %s: %s", attr_name, exc)

        logger.info("Tool registry ready — %d tools loaded.", len(self._tools))

    # ── Gemini Schema Export ──────────────────────────────────────────────────

    def get_all_schemas(self) -> list[dict]:
        """Return list of Gemini function-calling declarations for all tools."""
        return [tool.get_schema() for tool in self._tools.values()]

    # ── Execution ─────────────────────────────────────────────────────────────

    def execute(self, tool_name: str, action: str, params: dict) -> ToolResult:
        """Dispatch an action to the named tool."""
        tool = self._tools.get(tool_name)
        if not tool:
            available = ", ".join(self._tools.keys())
            return ToolResult.fail(
                f"Unknown tool '{tool_name}'. Available tools: {available}"
            )

        logger.info("Executing %s.%s with params=%s", tool_name, action, params)
        try:
            result = tool.execute(action, params)
        except Exception as exc:
            logger.exception("Tool %s.%s raised an exception", tool_name, action)
            result = ToolResult.fail(f"Something went wrong in {tool_name}: {exc}")

        result.action_taken = f"{tool_name}.{action}"
        return result

    # ── Introspection ─────────────────────────────────────────────────────────

    def list_tools(self) -> list[dict]:
        """Return metadata about all registered tools for the /api/tools endpoint."""
        return [
            {
                "name": t.name,
                "description": t.description,
                "actions": t.actions,
                "dangerous_actions": t.dangerous_actions,
            }
            for t in self._tools.values()
        ]

    def get_tool(self, name: str) -> BaseTool | None:
        return self._tools.get(name)

    def is_dangerous(self, tool_name: str, action: str) -> bool:
        tool = self._tools.get(tool_name)
        return tool.is_dangerous(action) if tool else False

    def __len__(self) -> int:
        return len(self._tools)

    def __repr__(self) -> str:
        return f"<ToolRegistry tools={list(self._tools.keys())}>"


# ── Module-level singleton ────────────────────────────────────────────────────
registry = ToolRegistry()
