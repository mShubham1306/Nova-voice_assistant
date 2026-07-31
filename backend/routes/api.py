"""
NOVA API Routes — FastAPI router
REST endpoints for the NOVA voice assistant backend.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Any

router = APIRouter(prefix="/api", tags=["nova"])

# Injected by app.py at startup
_assistant = None


def init_assistant(assistant) -> None:
    global _assistant
    _assistant = assistant


def _get_assistant():
    if _assistant is None:
        raise HTTPException(status_code=503, detail="Assistant not initialized.")
    return _assistant


# ── Request Models ────────────────────────────────────────────────────────────

class CommandRequest(BaseModel):
    query: str
    skip_speech: bool = True  # Text commands skip TTS by default


class ToolCallRequest(BaseModel):
    tool: str
    action: str
    params: dict[str, Any] = {}


class MemorySetRequest(BaseModel):
    key: str
    value: Any


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/health")
def health_check():
    """Health check for load balancers and monitoring."""
    a = _assistant
    return {
        "status": "healthy",
        "service": "NOVA AI Operating Assistant",
        "brain_available": a.brain.is_available if a else False,
        "tools_loaded": len(a.registry) if a else 0,
    }


@router.get("/status")
def get_status():
    """Get full assistant status."""
    return _get_assistant().get_status()


@router.post("/start")
def start_assistant():
    """Start voice listening loop."""
    return _get_assistant().start()


@router.post("/stop")
def stop_assistant():
    """Stop voice listening loop."""
    return _get_assistant().stop()


@router.post("/command")
def send_command(body: CommandRequest):
    """
    Send a text command to NOVA.
    Routes through the 3-layer pipeline (fast router → brain → tool registry).
    """
    if not body.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
    return _get_assistant().process_command(body.query, skip_speech=body.skip_speech)


@router.post("/tool")
def call_tool_directly(body: ToolCallRequest):
    """
    Directly call a specific tool action — bypasses Gemini entirely.
    Useful for frontend buttons and confirmed actions.
    """
    a = _get_assistant()
    result = a.registry.execute(body.tool, body.action, body.params)
    return result.to_dict()


@router.get("/tools")
def list_tools():
    """List all registered tools and their actions."""
    return {
        "tools": _get_assistant().registry.list_tools(),
        "total": len(_get_assistant().registry),
    }


@router.get("/tools/{tool_name}/schema")
def get_tool_schema(tool_name: str):
    """Get the Gemini function-calling schema for a specific tool."""
    a = _get_assistant()
    tool = a.registry.get_tool(tool_name)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found.")
    return tool.get_schema()


@router.get("/history")
def get_history():
    """Get recent command history (last 50)."""
    return {"history": _get_assistant().get_history()}


@router.get("/memory")
def get_memory():
    """Get current memory state (session + persistent)."""
    return _get_assistant().get_memory()


@router.delete("/memory")
def clear_memory():
    """Clear all memory (session and persistent)."""
    a = _get_assistant()
    a.memory.clear_session()
    a.memory.clear_persistent()
    a.brain.reset_chat()
    return {"status": "cleared", "message": "All memory has been cleared."}


@router.post("/memory")
def set_memory(body: MemorySetRequest):
    """Set a persistent memory value."""
    _get_assistant().memory.set(body.key, body.value)
    return {"status": "saved", "key": body.key}


@router.post("/wake-word")
def toggle_wake_word():
    """Toggle wake word listening mode."""
    a = _get_assistant()
    a.wake_word_mode = not a.wake_word_mode
    return {
        "wake_word_mode": a.wake_word_mode,
        "message": f"Wake word mode {'enabled' if a.wake_word_mode else 'disabled'}.",
    }


@router.post("/reset-chat")
def reset_chat():
    """Reset Gemini conversation history."""
    _get_assistant().brain.reset_chat()
    return {"status": "reset", "message": "Conversation history cleared."}


@router.get("/features")
def get_features():
    """Get all NOVA features grouped by tool for the frontend."""
    a = _get_assistant()
    categories = []
    tool_meta = {
        "system_tool":   {"icon": "⚙️",  "color": "#6366f1", "label": "System Control"},
        "file_tool":     {"icon": "📁",  "color": "#f59e0b", "label": "File Manager"},
        "browser_tool":  {"icon": "🌐",  "color": "#06b6d4", "label": "Web & Search"},
        "media_tool":    {"icon": "🎵",  "color": "#8b5cf6", "label": "Media Control"},
        "utility_tool":  {"icon": "🛠️",  "color": "#10b981", "label": "Utilities"},
        "info_tool":     {"icon": "📚",  "color": "#ec4899", "label": "Information"},
        "notes_tool":    {"icon": "📝",  "color": "#84cc16", "label": "Smart Notes"},
        "dev_tool":      {"icon": "💻",  "color": "#f97316", "label": "Developer"},
        "workflow_tool": {"icon": "⚡",  "color": "#a855f7", "label": "Workflows"},
    }
    for t in a.registry.list_tools():
        meta = tool_meta.get(t["name"], {"icon": "🔧", "color": "#64748b", "label": t["name"]})
        categories.append({
            "name": meta["label"],
            "tool": t["name"],
            "icon": meta["icon"],
            "color": meta["color"],
            "description": "",
            "actions": t["actions"],
            "action_count": len(t["actions"]),
        })
    return {
        "categories": categories,
        "total_tools": len(categories),
        "total_actions": sum(c["action_count"] for c in categories),
        "brain_enabled": a.brain.is_available,
    }
