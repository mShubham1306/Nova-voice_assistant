"""
NOVA Assistant — Thin Orchestrator (NOVA 3.0 Enterprise Architecture)
Routes input through the 3-layer pipeline and passes all tool actions
through the ExecutionEngine (Validation -> Safety Interceptor -> Retry -> Timeout -> Event Bus).
"""

from __future__ import annotations

import datetime
import logging
import threading
from typing import Any

from config import settings
from core.brain import Brain
from core.event_bus import event_bus
from core.execution_engine import execution_engine
from core.memory import Memory
from core.router import fast_route
from core.task_manager import task_manager
from core.voice_engine import VoiceEngine
from tools.base_tool import ToolResult
from tools.registry import registry


logger = logging.getLogger("nova.assistant")


class Assistant:
    """
    NOVA's central command orchestrator.
    Receives text/voice commands, routes them, delegates execution to ExecutionEngine,
    and publishes events to the EventBus.
    """

    def __init__(self, socketio=None) -> None:
        self.socketio = socketio
        self.is_running = False
        self.silent_mode = False
        self.wake_word_mode = False
        self._thread: threading.Thread | None = None

        logger.info("[Assistant] Initializing NOVA 3.0 Core...")

        self.voice = VoiceEngine(socketio)
        self.registry = registry
        self.memory = Memory(settings.MEMORY_FILE)
        self.brain = Brain(self.registry.get_all_schemas())
        self.execution_engine = execution_engine
        self.event_bus = event_bus
        self.task_manager = task_manager

        # Subscribe Memory to EventBus events for auto-logging
        self.event_bus.subscribe("tool_executed", self._on_tool_executed_event)

        logger.info("[Assistant] NOVA 3.0 ready. %d tools loaded.", len(self.registry))

    def _on_tool_executed_event(self, event) -> None:
        """Auto-log tool execution to memory."""
        payload = event.payload
        tool = payload.get("tool")
        action = payload.get("action")
        success = payload.get("success", False)
        if tool and action:
            self.memory.log_command(
                query=f"{tool}.{action}",
                result_type="success" if success else "error",
                tool=f"{tool}.{action}",
            )

    # ── Main Entry Point ──────────────────────────────────────────────────────

    def process_command(self, query: str, skip_speech: bool = False) -> dict:
        """
        3-Layer Command Processing Pipeline:
          Layer 1: Fast Router (sub-ms regex)
          Layer 2: Gemini Brain (Function Calling)
          Layer 3: ExecutionEngine (Validation, Safety Interceptor, Retries, Timeout, EventBus)
        """
        if not query or not query.strip():
            return self._build_response("I didn't catch that.", "error")

        original_query = query.strip()
        query_lower = original_query.lower()

        if skip_speech:
            self.voice.muted = True

        try:
            # ── Silent Mode ──────────────────────────────────────────────────
            if self.silent_mode:
                wake_words = ["hey nova", "nova", "wake up", "hello nova", "i need you"]
                if any(w in query_lower for w in wake_words):
                    self.silent_mode = False
                    self.voice.speak("I'm back! How can I help?")
                    return self._build_response("I'm awake and ready!", "wake")
                return self._build_response("(silent mode)", "silent")

            # ── Control Directives ───────────────────────────────────────────
            if any(w in query_lower for w in ["stop nova", "exit nova", "quit nova", "goodbye nova"]):
                self.voice.speak("Goodbye! Have a great day!")
                self.is_running = False
                return self._build_response("Shutting down. Goodbye!", "exit")

            if any(w in query_lower for w in ["shut up", "be quiet", "stay silent", "silent mode"]):
                self.silent_mode = True
                self.voice.speak("Going silent. Say 'Hey Nova' to wake me up.")
                return self._build_response("Silent mode activated.", "silent")

            # ── LAYER 1: Fast Router ──────────────────────────────────────────
            fast_result = fast_route(query_lower)
            if fast_result:
                tool_name, action, params = fast_result
                logger.info("[L1] Fast route -> %s.%s", tool_name, action)

                tool_result = self.execution_engine.execute_action(tool_name, action, params)
                return self._handle_tool_result(tool_result, original_query, layer="fast_router")

            # ── LAYER 2: Gemini Brain ─────────────────────────────────────────
            context = self.memory.get_context_summary()
            brain_response = self.brain.think(original_query, context)

            if brain_response["type"] == "tool_call":
                tool_name = brain_response["tool"]
                action = brain_response["action"]
                params = brain_response.get("params", {})
                logger.info("[L2] Brain -> %s.%s", tool_name, action)

                tool_result = self.execution_engine.execute_action(tool_name, action, params)
                return self._handle_tool_result(tool_result, original_query, layer="gemini_brain")

            elif brain_response["type"] == "text":
                text = brain_response["response"]
                self.voice.speak(text)
                self.memory.log_command(original_query, "ai_chat")
                return self._build_response(text, "ai_chat")

            # ── LAYER 3 FALLBACK: Direct AI Chat ──────────────────────────────
            fallback_text = self.brain.simple_chat(original_query)
            self.voice.speak(fallback_text)
            return self._build_response(fallback_text, "ai_chat")

        except Exception as exc:
            logger.exception("[Assistant] Unhandled error processing '%s'", original_query)
            return self._build_response("Something went wrong. Please try again.", "error")
        finally:
            if skip_speech:
                self.voice.muted = False

    # ── Tool Result Handling ──────────────────────────────────────────────────

    def _handle_tool_result(self, result: ToolResult, query: str, layer: str) -> dict:
        if result.speak and not self.voice.muted:
            self.voice.speak(result.message)

        self._emit("command_result", result.to_dict())

        return {
            "response": result.message,
            "type": "success" if result.success else ("confirm" if result.requires_confirmation else "error"),
            "tool": result.action_taken,
            "layer": layer,
            "data": result.data,
            "requires_confirmation": result.requires_confirmation,
            "confirmation_prompt": result.confirmation_prompt,
        }

    def _build_response(self, message: str, rtype: str, **extra) -> dict:
        return {"response": message, "type": rtype, **extra}

    # ── Voice Loop ────────────────────────────────────────────────────────────

    def start_voice_loop(self) -> None:
        self.is_running = True
        self._emit("assistant_started", {"name": settings.ASSISTANT_NAME, "status": "ready"})
        self.voice.speak(f"Hello! I'm {settings.ASSISTANT_NAME}, your AI Operating Assistant. How can I help?")

        while self.is_running:
            try:
                if self.wake_word_mode:
                    if not self.voice.listen_for_wake_word():
                        continue

                query = self.voice.listen()
                if query:
                    self._emit("command_received", {"query": query})
                    result = self.process_command(query)
                    self._emit("command_result", result)

                    if not self.is_running:
                        break
            except Exception as e:
                logger.error("[Loop] Error: %s", e)
                continue

    def start(self) -> dict:
        if self._thread and self._thread.is_alive():
            return {"status": "already_running"}
        self._thread = threading.Thread(target=self.start_voice_loop, daemon=True)
        self._thread.start()
        return {"status": "started", "name": settings.ASSISTANT_NAME}

    def stop(self) -> dict:
        self.is_running = False
        self.voice.stop_wake_word()
        self._emit("assistant_stopped", {})
        return {"status": "stopped"}

    def get_status(self) -> dict:
        return {
            "is_running": self.is_running,
            "is_listening": self.voice.is_listening,
            "is_speaking": self.voice.is_speaking,
            "silent_mode": self.silent_mode,
            "wake_word_mode": self.wake_word_mode,
            "brain_available": self.brain.is_available,
            "tools_loaded": len(self.registry),
            "pending_confirmations": len(self.execution_engine.get_pending_confirmations()),
            "name": settings.ASSISTANT_NAME,
            "commands_this_session": self.memory.get_session("command_count", 0),
        }

    def get_history(self) -> list[dict]:
        return self.memory.get_recent_commands(50)

    def get_memory(self) -> dict:
        return self.memory.get_full_status()

    def _emit(self, event: str, data: Any) -> None:
        if self.socketio:
            try:
                self.socketio.emit(event, data)
            except Exception:
                pass
