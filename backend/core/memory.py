"""
NOVA Core — Memory
Session and persistent memory for NOVA.

Session memory: what's happening right now (cleared on restart)
Persistent memory: what NOVA remembers across restarts (stored in data/memory.json)

Memory is fed as context to the Gemini Brain so it can give
contextually aware responses.
"""

from __future__ import annotations

import datetime
import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger("nova.memory")


class Memory:
    """
    Two-level memory store:
      - session:    in-memory dict, reset on restart
      - persistent: JSON-backed dict, survives restarts
    """

    def __init__(self, memory_file: Path) -> None:
        self._file = memory_file
        self._session: dict[str, Any] = {
            "started_at": datetime.datetime.now().isoformat(),
            "command_count": 0,
            "last_command": None,
            "last_tool": None,
            "open_apps": [],
        }
        self._persistent: dict[str, Any] = self._load_persistent()

    # ── Persistent Storage ────────────────────────────────────────────────────

    def _load_persistent(self) -> dict:
        if self._file.exists():
            try:
                return json.loads(self._file.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {
            "user_name": "",
            "preferred_projects": [],
            "favorite_apps": [],
            "notes_count": 0,
            "command_history": [],   # Last 100 commands
            "preferences": {},
            "last_session": None,
        }

    def _save_persistent(self) -> None:
        try:
            self._file.parent.mkdir(parents=True, exist_ok=True)
            self._file.write_text(
                json.dumps(self._persistent, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except Exception as e:
            logger.warning("Could not save persistent memory: %s", e)

    # ── Session Memory ────────────────────────────────────────────────────────

    def get_session(self, key: str, default: Any = None) -> Any:
        return self._session.get(key, default)

    def set_session(self, key: str, value: Any) -> None:
        self._session[key] = value

    # ── Persistent Memory ─────────────────────────────────────────────────────

    def get(self, key: str, default: Any = None) -> Any:
        return self._persistent.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._persistent[key] = value
        self._save_persistent()

    def remember(self, key: str, value: Any) -> None:
        """Convenience alias for set()."""
        self.set(key, value)

    def recall(self, key: str) -> Any:
        """Convenience alias for get()."""
        return self.get(key)

    # ── Command History ───────────────────────────────────────────────────────

    def log_command(self, query: str, result_type: str, tool: str | None = None) -> None:
        """Record a command to both session and persistent history."""
        entry = {
            "query": query,
            "type": result_type,
            "tool": tool,
            "timestamp": datetime.datetime.now().isoformat(),
        }

        # Session
        self._session["command_count"] += 1
        self._session["last_command"] = query
        self._session["last_tool"] = tool

        # Persistent
        history: list = self._persistent.setdefault("command_history", [])
        history.append(entry)
        if len(history) > 100:
            history = history[-100:]
        self._persistent["command_history"] = history
        self._persistent["last_session"] = datetime.datetime.now().isoformat()
        self._save_persistent()

    def get_recent_commands(self, n: int = 10) -> list[dict]:
        history = self._persistent.get("command_history", [])
        return history[-n:][::-1]

    # ── Context Summary ───────────────────────────────────────────────────────

    def get_context_summary(self) -> str:
        """
        Returns a brief context string fed to Gemini Brain
        so it can give contextually aware responses.
        """
        parts = []

        # User name
        name = self._persistent.get("user_name")
        if name:
            parts.append(f"User name: {name}")

        # Current session
        count = self._session.get("command_count", 0)
        if count > 0:
            parts.append(f"Commands this session: {count}")

        last = self._session.get("last_command")
        if last:
            parts.append(f"Last command: '{last}'")

        last_tool = self._session.get("last_tool")
        if last_tool:
            parts.append(f"Last tool used: {last_tool}")

        # Recent history (last 3 commands)
        recent = self.get_recent_commands(3)
        if recent:
            recent_strs = [f"'{r['query']}'" for r in recent[:3]]
            parts.append(f"Recent commands: {', '.join(recent_strs)}")

        return "; ".join(parts) if parts else ""

    def get_full_status(self) -> dict:
        """Return full memory state for the /api/memory endpoint."""
        return {
            "session": self._session,
            "persistent": {
                k: v for k, v in self._persistent.items()
                if k != "command_history"  # Exclude for brevity
            },
            "recent_commands": self.get_recent_commands(20),
        }

    def clear_session(self) -> None:
        self._session = {
            "started_at": datetime.datetime.now().isoformat(),
            "command_count": 0,
            "last_command": None,
            "last_tool": None,
            "open_apps": [],
        }

    def clear_persistent(self) -> None:
        self._persistent = {}
        self._save_persistent()
