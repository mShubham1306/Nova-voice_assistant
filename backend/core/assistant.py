"""
NOVA Assistant — Thin Orchestrator
The central brain that wires all 3 layers together.

Processing pipeline for every command:
  1. Layer 1 — Fast Router (regex, <1ms, no API)
     → Simple commands: volume, lock, screenshot, etc.

  2. Layer 2 — Gemini Brain (function calling)
     → Complex commands: "find my resume and open it", "start my project"

  3. Layer 3 — Tool Registry
     → Executes the tool + action returned by layers 1 or 2

  4. Fallback — Direct AI chat
     → Pure conversational responses (jokes, greetings, explanations)

This class is intentionally thin — it delegates everything.
"""

from __future__ import annotations

import datetime
import logging
import threading
from typing import Any

from config import settings
from core.router import fast_route
from core.brain import Brain
from core.memory import Memory
from core.voice_engine import VoiceEngine
from tools.registry import ToolRegistry
from tools.base_tool import ToolResult

logger = logging.getLogger("nova.assistant")


class Assistant:
    """
    NOVA's central command orchestrator.
    Receives text commands, routes them, executes tools, and responds.
    """

    def __init__(self, socketio=None) -> None:
        self.socketio = socketio
        self.is_running = False
        self.silent_mode = False
        self.wake_word_mode = False
        self._thread: threading.Thread | None = None

        logger.info("[Assistant] Initializing NOVA...")

        # Initialize all subsystems
        self.voice = VoiceEngine(socketio)
        self.registry = ToolRegistry()
        self.memory = Memory(settings.MEMORY_FILE)
        self.brain = Brain(self.registry.get_all_schemas())

        logger.info("[Assistant] NOVA ready. %d tools loaded.", len(self.registry))

    # ── Main Entry Point ──────────────────────────────────────────────────────

    def process_command(self, query: str, skip_speech: bool = False) -> dict:
        """
        The 3-layer command processing pipeline.
        Returns a uniform result dict for the API/WebSocket.
        """
        if not query or not query.strip():
            return self._build_response("I didn't catch that.", "error")

        original_query = query.strip()
        query_lower = original_query.lower()
        timestamp = datetime.datetime.now().isoformat()

        if skip_speech:
            self.voice.muted = True

        try:
            # ── Silent mode guard ─────────────────────────────────────────────
            if self.silent_mode:
                wake_words = ["hey nova", "nova", "wake up", "hello nova", "i need you",
                              "हे नोवा", "नोवा", "ノバ", "노바"]
                if any(w in query_lower for w in wake_words):
                    self.silent_mode = False
                    self.voice.speak("I'm back! How can I help?")
                    return self._build_response("I'm awake and ready!", "wake")
                return self._build_response("(silent mode)", "silent")

            # ── Special commands ──────────────────────────────────────────────
            if any(w in query_lower for w in ["stop nova", "exit nova", "quit nova", "goodbye nova"]):
                self.voice.speak("Goodbye! Have a great day!")
                self.is_running = False
                return self._build_response("Shutting down. Goodbye!", "exit")

            if any(w in query_lower for w in ["shut up", "be quiet", "stay silent", "silent mode"]):
                self.silent_mode = True
                self.voice.speak("Going silent. Say 'Hey Nova' to wake me up.")
                return self._build_response("Silent mode activated.", "silent")

            if any(w in query_lower for w in ["reset memory", "clear memory", "forget everything"]):
                self.memory.clear_session()
                self.brain.reset_chat()
                return self._build_response("Memory cleared. Starting fresh!", "success")

            # ── LAYER 1: Fast Router ──────────────────────────────────────────
            fast_result = fast_route(query_lower)
            if fast_result:
                tool_name, action, params = fast_result
                logger.info("[L1] Fast route → %s.%s", tool_name, action)
                tool_result = self.registry.execute(tool_name, action, params)
                return self._handle_tool_result(tool_result, original_query, layer="fast_router")

            # ── LAYER 2: Gemini Brain ─────────────────────────────────────────
            if self.brain.is_available:
                context = self.memory.get_context_summary()
                brain_response = self.brain.think(original_query, context)

                if brain_response["type"] == "tool_call":
                    tool_name = brain_response["tool"]
                    action = brain_response["action"]
                    params = brain_response.get("params", {})
                    logger.info("[L2] Brain → %s.%s", tool_name, action)

                    tool_result = self.registry.execute(tool_name, action, params)
                    return self._handle_tool_result(tool_result, original_query, layer="gemini_brain")

                elif brain_response["type"] == "text":
                    # Pure conversational response
                    text = brain_response["response"]
                    self.voice.speak(text)
                    self.memory.log_command(original_query, "ai_chat")
                    return self._build_response(text, "ai_chat")

                else:
                    # Brain error — fall through to direct AI chat
                    pass

            # ── LAYER 3 FALLBACK: Direct Gemini Chat (no tools) ───────────────
            fallback_text = self.brain.simple_chat(original_query) if self.brain.is_available \
                else "I didn't understand that. Try saying 'help' to see what I can do."
            self.voice.speak(fallback_text)
            self.memory.log_command(original_query, "ai_fallback")
            return self._build_response(fallback_text, "ai_chat")

        except Exception as exc:
            logger.exception("[Assistant] Unhandled error for query '%s'", original_query)
            err_msg = "Something went wrong. Please try again."
            return self._build_response(err_msg, "error")
        finally:
            if skip_speech:
                self.voice.muted = False

    # ── Tool Result Handling ──────────────────────────────────────────────────

    def _handle_tool_result(self, result: ToolResult, query: str, layer: str) -> dict:
        """Process a ToolResult — speak, log, emit, and build the API response."""
        if result.speak and not self.voice.muted:
            self.voice.speak(result.message)

        self.memory.log_command(query, "tool" if result.success else "error", result.action_taken)
        self._emit("command_result", result.to_dict())

        return {
            "response": result.message,
            "type": "success" if result.success else "error",
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
                    activated = self.voice.listen_for_wake_word()
                    if not activated:
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
            "name": settings.ASSISTANT_NAME,
            "commands_this_session": self.memory.get_session("command_count", 0),
        }

    def get_history(self) -> list[dict]:
        return self.memory.get_recent_commands(50)

    def get_memory(self) -> dict:
        return self.memory.get_full_status()

    # ── Emit Helper ───────────────────────────────────────────────────────────

    def _emit(self, event: str, data: Any) -> None:
        if self.socketio:
            try:
                self.socketio.emit(event, data)
            except Exception:
                pass
