"""
NOVA Core — Layer 2 Gemini Brain (NOVA 3.0 Resilient Engine)
Handles complex / ambiguous commands using Gemini Function Calling,
with automatic fallback resiliency if Gemini is offline or rate-limited.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from config import settings

logger = logging.getLogger("nova.brain")


NOVA_SYSTEM_PROMPT = """You are Nova, a powerful AI Operating Assistant running on a Windows PC.

Your job is to understand the user's intent and call the correct tool function.

RULES:
1. ALWAYS use a function call when the user wants to do something actionable.
2. Use conversational text ONLY for greetings, farewells, and questions that don't need a tool.
3. For any file, app, system, or workflow request — call a tool.
4. Extract entities precisely: app names, file names, folder names, durations, queries.
5. Support multilingual input. Detect the language and respond in the same language.
"""


class Brain:
    """
    Gemini-powered Layer 2 brain for complex command understanding.
    Uses native Gemini function calling with automatic offline fallback resiliency.
    """

    def __init__(self, tool_schemas: list[dict]) -> None:
        self._schemas = tool_schemas
        self._model = None
        self._chat = None
        self._available = False
        self._init_gemini()

    def _init_gemini(self) -> None:
        if not settings.GEMINI_API_KEY:
            logger.warning("[Brain] No GEMINI_API_KEY — primary AI routing offline. Secondary offline router ready.")
            return
        try:
            import google.generativeai as genai
            genai.configure(api_key=settings.GEMINI_API_KEY)

            tools = [genai.protos.Tool(
                function_declarations=[
                    genai.protos.FunctionDeclaration(**schema)
                    for schema in self._schemas
                ]
            )]

            self._model = genai.GenerativeModel(
                model_name=settings.GEMINI_MODEL,
                system_instruction=NOVA_SYSTEM_PROMPT,
                tools=tools,
            )
            self._chat = self._model.start_chat(history=[])
            self._available = True
            logger.info("[Brain] Gemini brain initialized with %d tool schemas.", len(self._schemas))
        except Exception as exc:
            logger.error("[Brain] Failed to initialize Gemini: %s", exc)
            self._available = False

    @property
    def is_available(self) -> bool:
        return self._available

    def think(self, query: str, context: str = "") -> dict:
        """
        Send the query to Gemini.
        If Gemini throws an error or is offline, falls back gracefully to offline intent parsing.
        """
        if self._available:
            try:
                full_query = f"[Context: {context}]\n\n{query}" if context else query
                response = self._chat.send_message(full_query)

                for candidate in response.candidates:
                    for part in candidate.content.parts:
                        if part.function_call.name:
                            fc = part.function_call
                            tool_name = fc.name
                            args = dict(fc.args)
                            action = args.pop("action", "")
                            args.pop("tool", None)

                            logger.info("[Brain] Tool call: %s.%s params=%s", tool_name, action, args)
                            return {
                                "type": "tool_call",
                                "tool": tool_name,
                                "action": action,
                                "params": args,
                            }

                text = response.text.strip()
                return {"type": "text", "response": text}

            except Exception as exc:
                logger.error("[Brain] Primary Gemini API error: %s. Switching to offline fallback.", exc)

        # ── Secondary Offline Intent Fallback Engine ────────────────────────
        return self._offline_fallback_think(query)

    def _offline_fallback_think(self, query: str) -> dict:
        """Rule-based offline intent engine when Gemini is offline or rate-limited."""
        q = query.lower().strip()

        if "open" in q:
            target = q.replace("open", "").strip()
            if "chrome" in target:
                return {"type": "tool_call", "tool": "system_tool", "action": "open_app", "params": {"app_name": "chrome"}}
            if "vscode" in target or "code" in target:
                return {"type": "tool_call", "tool": "system_tool", "action": "open_app", "params": {"app_name": "vscode"}}
            return {"type": "tool_call", "tool": "system_tool", "action": "open_app", "params": {"app_name": target}}

        if "search" in q:
            term = q.replace("search", "").strip()
            return {"type": "tool_call", "tool": "browser_tool", "action": "google_search", "params": {"query": term}}

        return {
            "type": "text",
            "response": f"NOVA is in offline fallback mode. Processed query: '{query}'.",
        }

    def simple_chat(self, query: str) -> str:
        if not self._available:
            return "AI chat is offline — using standard system mode."
        try:
            import google.generativeai as genai
            model = genai.GenerativeModel(model_name=settings.GEMINI_MODEL)
            r = model.generate_content(query)
            return r.text.strip()
        except Exception:
            return "I couldn't reach the AI service right now."

    def reset_chat(self) -> None:
        if self._model:
            self._chat = self._model.start_chat(history=[])
