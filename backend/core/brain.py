"""
NOVA Core — Layer 2 Gemini Brain
Handles complex / ambiguous commands using Gemini Function Calling.

Flow:
  1. Build context from memory (user's session history, preferences)
  2. Send query + all tool schemas to Gemini as function declarations
  3. Gemini returns a function call JSON: {tool, action, params}
  4. Brain returns that structured call — does NOT execute it
     (execution happens in Assistant)
  5. If Gemini returns text (conversational response), return it directly

This design keeps the Brain thin and testable.
"""

from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger("nova.brain")


NOVA_SYSTEM_PROMPT = """You are Nova, a powerful AI Operating Assistant running on a Windows PC.

Your job is to understand the user's intent and call the correct tool function.

RULES:
1. ALWAYS use a function call when the user wants to do something actionable.
2. Use conversational text ONLY for greetings, farewells, and questions that don't need a tool.
3. For any file, app, system, or workflow request — call a tool.
4. Extract entities precisely: app names, file names, folder names, durations, queries.
5. Support multilingual input. Detect the language and respond in the same language.
6. When the user says something in Hindi/Gujarati/other language, still call the correct tool.
7. Keep spoken responses short (under 80 words) — they are read aloud.

MULTILINGUAL INTENT MAPPING EXAMPLES:
- "Chrome kholo" → open_app(app_name="chrome")
- "Awaz badhao" → volume_up
- "Resume khol do" → file_tool.search_file + open_file
- "Mera project shuru karo" → workflow_tool.coding_environment
- "Aaj ka news batao" → info_tool.get_news
- "Screenshot lo" → utility_tool.screenshot
"""


class Brain:
    """
    Gemini-powered Layer 2 brain for complex command understanding.
    Uses native Gemini function calling — returns structured tool calls.
    """

    def __init__(self, tool_schemas: list[dict]) -> None:
        self._schemas = tool_schemas
        self._model = None
        self._chat = None
        self._available = False
        self._init_gemini()

    def _init_gemini(self) -> None:
        from config import settings
        if not settings.GEMINI_API_KEY:
            logger.warning("[Brain] No GEMINI_API_KEY — AI routing disabled. Using fast router only.")
            return
        try:
            import google.generativeai as genai
            genai.configure(api_key=settings.GEMINI_API_KEY)

            # Convert tool schemas to Gemini function declarations
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
        Send the query to Gemini and return a structured response.

        Returns one of:
          {
            "type": "tool_call",
            "tool": "file_tool",
            "action": "open_file",
            "params": { "filename": "resume.pdf" }
          }
          OR
          {
            "type": "text",
            "response": "Good morning! How can I help you?"
          }
          OR
          {
            "type": "error",
            "response": "I couldn't understand that."
          }
        """
        if not self._available:
            return {"type": "error", "response": "AI brain is offline. Gemini API key not configured."}

        # Inject context if available
        full_query = query
        if context:
            full_query = f"[Context: {context}]\n\n{query}"

        try:
            response = self._chat.send_message(full_query)

            # Check for function call
            for candidate in response.candidates:
                for part in candidate.content.parts:
                    if part.function_call.name:
                        fc = part.function_call
                        tool_name = fc.name
                        # Extract action and params from the function call args
                        args = dict(fc.args)
                        action = args.pop("action", "")
                        # Remove 'tool' key if Gemini echoes it back
                        args.pop("tool", None)

                        logger.info("[Brain] Tool call: %s.%s params=%s", tool_name, action, args)
                        return {
                            "type": "tool_call",
                            "tool": tool_name,
                            "action": action,
                            "params": args,
                        }

            # No function call — text response
            text = response.text.strip()
            logger.info("[Brain] Text response: %s", text[:80])
            return {"type": "text", "response": text}

        except Exception as exc:
            logger.error("[Brain] Gemini error: %s", exc)
            return {"type": "error", "response": f"I had trouble understanding that. Please try again."}

    def simple_chat(self, query: str) -> str:
        """
        Pure conversational response without tool calling.
        Used for AI-only chat queries.
        """
        if not self._available:
            return "AI chat is unavailable — no Gemini API key configured."
        try:
            # Use a separate model instance without tools for pure chat
            from config import settings
            import google.generativeai as genai
            model = genai.GenerativeModel(
                model_name=settings.GEMINI_MODEL,
                system_instruction=NOVA_SYSTEM_PROMPT,
            )
            r = model.generate_content(query)
            return r.text.strip()
        except Exception as exc:
            logger.error("[Brain] Chat error: %s", exc)
            return "Sorry, I couldn't process that right now."

    def reset_chat(self) -> None:
        """Reset conversation history."""
        if self._model:
            self._chat = self._model.start_chat(history=[])
