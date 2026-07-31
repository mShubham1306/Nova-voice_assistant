"""
NOVA Tool — Smart Notes
Create, search, tag, list, and recall notes with full-text search.
Notes are stored as JSON for easy querying.
"""

from __future__ import annotations

import datetime
import json
from pathlib import Path
from typing import Any

from tools.base_tool import BaseTool, ToolResult, param


class NotesTool(BaseTool):
    name = "notes_tool"
    description = (
        "Create, read, search, tag, and delete personal notes. "
        "Can recall notes from a specific date, list all notes, or find notes by keyword or tag."
    )
    actions = [
        "add_note",
        "list_notes",
        "search_notes",
        "get_recent_notes",
        "delete_note",
        "clear_all_notes",
    ]
    parameters = {
        "add_note": {
            "content": param("string", "The note content to save", required=True),
            "tags": param("string", "Comma-separated tags, e.g. 'work, ideas, todo'"),
            "title": param("string", "Optional short title for the note"),
        },
        "search_notes": {
            "query": param("string", "Keyword or phrase to search in notes", required=True),
        },
        "get_recent_notes": {
            "count": param("integer", "Number of recent notes to retrieve (default 5)"),
            "date": param("string", "Optional specific date in YYYY-MM-DD format, e.g. 'yesterday', '2026-07-30'"),
        },
        "delete_note": {
            "note_id": param("string", "ID of the note to delete (from list_notes)", required=True),
        },
    }
    dangerous_actions = ["clear_all_notes"]

    def __init__(self) -> None:
        from config import settings
        self._notes_file = settings.NOTES_DIR / "notes.json"
        self._ensure_file()

    def _ensure_file(self) -> None:
        if not self._notes_file.exists():
            self._notes_file.write_text("[]", encoding="utf-8")

    def _load(self) -> list[dict]:
        try:
            return json.loads(self._notes_file.read_text(encoding="utf-8"))
        except Exception:
            return []

    def _save(self, notes: list[dict]) -> None:
        self._notes_file.write_text(
            json.dumps(notes, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    def execute(self, action: str, params: dict[str, Any]) -> ToolResult:
        dispatch = {
            "add_note":        self._add_note,
            "list_notes":      self._list_notes,
            "search_notes":    self._search_notes,
            "get_recent_notes": self._get_recent_notes,
            "delete_note":     self._delete_note,
            "clear_all_notes": self._clear_all,
        }
        fn = dispatch.get(action)
        if fn is None:
            return self._not_implemented(action)
        return fn(params)

    def _add_note(self, p: dict) -> ToolResult:
        content = p.get("content", "").strip()
        if not content:
            return ToolResult.fail("Please provide note content.")
        tags_raw = p.get("tags", "")
        tags = [t.strip() for t in tags_raw.split(",") if t.strip()]
        title = p.get("title", "").strip()
        now = datetime.datetime.now()
        note = {
            "id": now.strftime("%Y%m%d%H%M%S%f"),
            "title": title or content[:40],
            "content": content,
            "tags": tags,
            "created_at": now.isoformat(),
            "date": now.strftime("%Y-%m-%d"),
        }
        notes = self._load()
        notes.append(note)
        self._save(notes)
        tag_str = f" [Tags: {', '.join(tags)}]" if tags else ""
        return ToolResult.ok(f"Note saved: '{note['title']}'{tag_str}", data={"note": note})

    def _list_notes(self, p: dict) -> ToolResult:
        notes = self._load()
        if not notes:
            return ToolResult.ok("You have no notes yet. Say 'take note' to create one.")
        count = len(notes)
        recent = notes[-5:]
        summaries = [f"- [{n['date']}] {n['title']}" for n in recent]
        msg = f"You have {count} notes. Most recent: " + "; ".join(n["title"] for n in recent[:3])
        return ToolResult.ok(msg, data={"notes": notes, "count": count}, speak=True)

    def _search_notes(self, p: dict) -> ToolResult:
        query = p.get("query", "").strip().lower()
        if not query:
            return ToolResult.fail("Please provide a search keyword.")
        notes = self._load()
        matches = [
            n for n in notes
            if query in n["content"].lower()
            or query in n["title"].lower()
            or any(query in tag.lower() for tag in n.get("tags", []))
        ]
        if not matches:
            return ToolResult.fail(f"No notes found matching '{query}'.")
        msg = f"Found {len(matches)} note(s) matching '{query}': {matches[0]['title']}"
        if len(matches) > 1:
            msg += f" and {len(matches)-1} more."
        return ToolResult.ok(msg, data={"notes": matches})

    def _get_recent_notes(self, p: dict) -> ToolResult:
        count = int(p.get("count", 5))
        date_str = p.get("date", "").strip().lower()
        notes = self._load()

        if date_str:
            if date_str == "yesterday":
                target = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
            elif date_str == "today":
                target = datetime.datetime.now().strftime("%Y-%m-%d")
            else:
                target = date_str
            notes = [n for n in notes if n.get("date") == target]
            if not notes:
                return ToolResult.ok(f"No notes found for {date_str}.")
            msg = f"Notes from {date_str}: " + "; ".join(n["title"] for n in notes[:3])
            return ToolResult.ok(msg, data={"notes": notes})

        recent = notes[-count:][::-1]
        if not recent:
            return ToolResult.ok("No notes found.")
        msg = f"Your {len(recent)} most recent notes: " + "; ".join(n["title"] for n in recent[:3])
        return ToolResult.ok(msg, data={"notes": recent})

    def _delete_note(self, p: dict) -> ToolResult:
        note_id = p.get("note_id", "").strip()
        notes = self._load()
        before = len(notes)
        notes = [n for n in notes if n["id"] != note_id]
        if len(notes) == before:
            return ToolResult.fail(f"Note ID '{note_id}' not found.")
        self._save(notes)
        return ToolResult.ok("Note deleted.")

    def _clear_all(self, p: dict) -> ToolResult:
        self._save([])
        return ToolResult.ok("All notes cleared.")
