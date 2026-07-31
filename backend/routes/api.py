"""
NOVA API Routes — FastAPI Router (NOVA 3.0 Enterprise Architecture)
REST endpoints for NOVA AI Operating Assistant including Safety Confirmations,
Tool Health Audits, Event Bus stream, Declarative Workflows, and Task Management.
"""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api", tags=["nova"])

# Injected by app.py
_assistant = None


def init_assistant(assistant) -> None:
    global _assistant
    _assistant = assistant


def _get_assistant():
    global _assistant
    if _assistant is None:
        from core.assistant import Assistant
        _assistant = Assistant()
        init_assistant(_assistant)
    return _assistant


# ── Request Models ────────────────────────────────────────────────────────────

class CommandRequest(BaseModel):
    query: str
    skip_speech: bool = True


class ToolCallRequest(BaseModel):
    tool: str
    action: str
    params: dict[str, Any] = {}
    bypass_confirmation: bool = False


class ConfirmationRequest(BaseModel):
    confirmation_id: str
    approved: bool = True


class MemorySetRequest(BaseModel):
    key: str
    value: Any


class WorkflowCreateRequest(BaseModel):
    id: str
    name: str
    description: str = ""
    steps: list[dict[str, Any]]


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/health")
def health_check():
    """Health check for load balancers and system status."""
    a = _assistant
    return {
        "status": "healthy",
        "service": "NOVA 3.0 AI Operating Assistant",
        "version": "3.0.0",
        "brain_available": a.brain.is_available if a else False,
        "tools_loaded": len(a.registry) if a else 0,
        "pending_confirmations": len(a.execution_engine.get_pending_confirmations()) if a else 0,
    }


@router.get("/status")
def get_status():
    """Get full operational status."""
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
    Send a command query to NOVA 3.0 pipeline.
    Routes: Fast Router -> Gemini Brain -> ExecutionEngine (Validation, Safety, EventBus).
    """
    if not body.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
    return _get_assistant().process_command(body.query, skip_speech=body.skip_speech)


@router.post("/tool")
def call_tool_directly(body: ToolCallRequest):
    """
    Direct tool call endpoint routed through ExecutionEngine.
    Enforces validation, safety interceptor, and Event Bus logging.
    """
    a = _get_assistant()
    result = a.execution_engine.execute_action(
        body.tool, body.action, body.params, bypass_confirmation=body.bypass_confirmation
    )
    return result.to_dict()


# ── Safety & Permission Confirmation Endpoints ───────────────────────────────

@router.get("/confirm/pending")
def list_pending_confirmations():
    """List all dangerous actions waiting for user confirmation."""
    return {"pending": _get_assistant().execution_engine.get_pending_confirmations()}


@router.post("/confirm")
def confirm_pending_action(body: ConfirmationRequest):
    """Approve or reject a pending dangerous action."""
    result = _get_assistant().execution_engine.confirm_action(
        body.confirmation_id, approved=body.approved
    )
    return result.to_dict()


# ── Tool Health & Metadata API ────────────────────────────────────────────────

@router.get("/tools")
def list_tools():
    """List all registered tools."""
    return {
        "tools": _get_assistant().registry.list_tools(),
        "total": len(_get_assistant().registry),
    }


@router.get("/tools/health")
def tool_health_audit():
    """Diagnostic health audit of all loaded tools (status, dependencies, priority, version)."""
    a = _get_assistant()
    health_reports = [tool.health() for tool in a.registry._tools.values()]
    healthy_count = sum(1 for h in health_reports if h["status"] == "healthy")
    return {
        "tools": health_reports,
        "total_tools": len(health_reports),
        "healthy_count": healthy_count,
        "degraded_count": len(health_reports) - healthy_count,
    }


# ── Event Bus & Observability ─────────────────────────────────────────────────

@router.get("/events")
def list_recent_events(limit: int = 50):
    """View recent system events from the Event Bus."""
    return {"events": _get_assistant().event_bus.get_recent_events(limit)}


# ── Background Task Management ────────────────────────────────────────────────

@router.get("/tasks")
def list_background_tasks():
    """View active and completed background tasks."""
    return {"tasks": _get_assistant().task_manager.list_tasks()}


# ── Declarative Workflows API ─────────────────────────────────────────────────

@router.get("/workflows")
def list_declarative_workflows():
    """List all declarative JSON workflows."""
    a = _get_assistant()
    wf_tool = a.registry.get_tool("workflow_tool")
    if not wf_tool:
        return {"workflows": []}
    res = wf_tool.execute("list_workflows", {})
    return res.data


@router.post("/workflows")
def create_declarative_workflow(body: WorkflowCreateRequest):
    """Create a new declarative JSON workflow file."""
    a = _get_assistant()
    wf_tool = a.registry.get_tool("workflow_tool")
    if not wf_tool:
        raise HTTPException(status_code=500, detail="Workflow tool unavailable.")
    res = wf_tool.execute("create_workflow", body.model_dump())
    return res.to_dict()


# ── Memory & History ──────────────────────────────────────────────────────────

@router.get("/history")
def get_history():
    """Get recent command history."""
    return {"history": _get_assistant().get_history()}


@router.get("/memory")
def get_memory():
    """Get memory state."""
    return _get_assistant().get_memory()


@router.delete("/memory")
def clear_memory():
    """Clear memory state."""
    a = _get_assistant()
    a.memory.clear_session()
    a.memory.clear_persistent()
    a.brain.reset_chat()
    return {"status": "cleared", "message": "All memory cleared."}


# ── Metadata & Configuration Endpoints ────────────────────────────────────────

@router.get("/features")
def get_features():
    """Get NOVA features and command capabilities."""
    return {
        "categories": [
            {
                "name": "AI Chat",
                "icon": "🤖",
                "color": "#8b5cf6",
                "commands": [
                    {"cmd": "Tell me about black holes", "desc": "Ask anything"},
                    {"cmd": "Explain quantum computing", "desc": "Deep explanations"},
                    {"cmd": "How to learn Python?", "desc": "Get advice"},
                    {"cmd": "Who are you?", "desc": "Meet Nova"},
                ]
            },
            {
                "name": "Web & Search",
                "icon": "🌐",
                "color": "#06b6d4",
                "commands": [
                    {"cmd": "Search Google for...", "desc": "Google search"},
                    {"cmd": "Search YouTube for...", "desc": "YouTube search"},
                    {"cmd": "Wikipedia...", "desc": "Look up Wikipedia"},
                    {"cmd": "Open website...", "desc": "Visit any site"},
                ]
            },
            {
                "name": "Information",
                "icon": "📚",
                "color": "#10b981",
                "commands": [
                    {"cmd": "What time is it?", "desc": "Current time"},
                    {"cmd": "What's the date?", "desc": "Today's date"},
                    {"cmd": "Weather in London", "desc": "Weather updates"},
                    {"cmd": "Tell me a joke", "desc": "Random humor"},
                    {"cmd": "Fun fact", "desc": "Interesting facts"},
                    {"cmd": "Motivational quote", "desc": "Get inspired"},
                    {"cmd": "Flip a coin", "desc": "Heads or tails"},
                    {"cmd": "Roll a dice", "desc": "Random 1-6"},
                ]
            },
            {
                "name": "Utilities",
                "icon": "🛠️",
                "color": "#f59e0b",
                "commands": [
                    {"cmd": "Calculate 5 plus 3", "desc": "Math calculations"},
                    {"cmd": "Take note...", "desc": "Save a note"},
                ]
            },
        ],
        "total_commands": 20,
        "wake_word": "Hey Nova",
    }


@router.get("/languages")
def get_languages():
    """Get supported language mappings."""
    langs = {
        "hi": "Hindi", "gu": "Gujarati", "bn": "Bengali", "ta": "Tamil",
        "te": "Telugu", "kn": "Kannada", "ml": "Malayalam", "mr": "Marathi",
        "pa": "Punjabi", "en": "English", "fr": "French", "de": "German",
        "es": "Spanish", "it": "Italian", "pt": "Portuguese", "ru": "Russian",
        "zh": "Chinese", "ja": "Japanese", "ko": "Korean", "ar": "Arabic",
    }
    return {
        "languages": langs,
        "total": len(langs),
        "description": "Nova understands 40+ languages. Speak or type — Nova auto-detects and replies in the same language."
    }


@router.post("/wake-word")
def toggle_wake_word():
    """Toggle wake word status."""
    return {"wake_word_mode": False, "message": "Wake word runs client-side in the browser."}

