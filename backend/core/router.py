"""
NOVA Core — Layer 1 Fast Router
Regex pattern matching for simple, deterministic commands.
These bypass Gemini entirely — zero API calls, <1ms response.

Design:
  Each rule is: (pattern, tool_name, action, static_params)
  Params can also be a callable that extracts dynamic values from the query.
"""

from __future__ import annotations

import re
from typing import Callable

# ─── Type Aliases ─────────────────────────────────────────────────────────────
# Each route: (compiled_regex, tool_name, action, params_or_extractor)
RouteEntry = tuple[re.Pattern, str, str, dict | Callable[[re.Match], dict]]


def _steps(m: re.Match) -> dict:
    """Extract optional step count from volume commands."""
    try:
        return {"steps": int(m.group(1))}
    except (IndexError, TypeError):
        return {}


def _amount(m: re.Match) -> dict:
    """Extract optional amount from brightness commands."""
    try:
        return {"amount": int(m.group(1))}
    except (IndexError, TypeError):
        return {}


def _query(group: int = 1) -> Callable[[re.Match], dict]:
    """Extract a query/app name from a capture group."""
    def _extract(m: re.Match) -> dict:
        try:
            return {"query": m.group(group).strip()}
        except (IndexError, AttributeError):
            return {}
    return _extract


def _app_name(m: re.Match) -> dict:
    try:
        return {"app_name": m.group(1).strip()}
    except (IndexError, AttributeError):
        return {}


def _port(m: re.Match) -> dict:
    try:
        return {"port": int(m.group(1))}
    except (IndexError, TypeError, AttributeError):
        return {}


# ─── Fast Route Table ─────────────────────────────────────────────────────────
# Order matters — more specific patterns first.

_RAW_ROUTES: list[tuple[str, str, str, dict | Callable]] = [

    # ── Volume ──────────────────────────────────────────────────────────────
    (r"volume\s+up|louder|increase\s+volume|awaz\s+badhao|sound\s+up",
     "system_tool", "volume_up", {}),
    (r"volume\s+down|quieter|decrease\s+volume|softer|awaz\s+kam\s+karo",
     "system_tool", "volume_down", {}),
    (r"mute|unmute|toggle\s+mute|volume\s+mute|band\s+karo",
     "system_tool", "volume_mute", {}),

    # ── Brightness ────────────────────────────────────────────────────────
    (r"brightness\s+up|brighter|increase\s+brightness",
     "system_tool", "brightness_up", {}),
    (r"brightness\s+down|dimmer|decrease\s+brightness|dim\s+screen",
     "system_tool", "brightness_down", {}),

    # ── Power ─────────────────────────────────────────────────────────────
    (r"lock\s+screen|lock\s+pc|lock\s+computer",
     "system_tool", "lock_screen", {}),
    (r"shutdown|shut\s+down|turn\s+off\s+(?:pc|computer)",
     "system_tool", "shutdown", {}),
    (r"restart|reboot|restart\s+(?:pc|computer)",
     "system_tool", "restart", {}),
    (r"cancel\s+shutdown|abort\s+shutdown",
     "system_tool", "cancel_shutdown", {}),

    # ── System Stats ──────────────────────────────────────────────────────
    (r"battery|battery\s+(?:status|level|percent)|how\s+much\s+battery",
     "system_tool", "battery_status", {}),
    (r"cpu\s+(?:usage|status|percent)|processor\s+usage",
     "system_tool", "cpu_usage", {}),
    (r"(?:ram|memory)\s+(?:usage|status)|how\s+much\s+(?:ram|memory)",
     "system_tool", "memory_usage", {}),
    (r"disk\s+(?:usage|space|status)|storage\s+(?:space|status)",
     "system_tool", "disk_usage", {}),
    (r"system\s+info|pc\s+info|computer\s+(?:info|specs)",
     "system_tool", "system_info", {}),
    (r"(?:my\s+)?ip\s+(?:address|addr)|what\s+is\s+my\s+ip",
     "system_tool", "get_ip", {}),
    (r"wifi\s+status|internet\s+(?:status|connection)|am\s+i\s+connected",
     "system_tool", "wifi_status", {}),
    (r"empty\s+recycle\s+bin|clear\s+recycle\s+bin",
     "system_tool", "empty_recycle_bin", {}),
    (r"running\s+(?:apps|processes)|list\s+(?:processes|apps)",
     "system_tool", "list_running_apps", {}),

    # ── Media ─────────────────────────────────────────────────────────────
    (r"play\s*/?pause|toggle\s+(?:play|music)|resume\s+music",
     "media_tool", "play_pause", {}),
    (r"next\s+(?:song|track)|skip\s+(?:song|track)",
     "media_tool", "next_track", {}),
    (r"(?:previous|prev|last)\s+(?:song|track)|go\s+back",
     "media_tool", "previous_track", {}),
    (r"stop\s+(?:music|playing|song)",
     "media_tool", "stop", {}),

    # ── Screenshot ────────────────────────────────────────────────────────
    (r"(?:take\s+)?screenshot|capture\s+screen|screen\s+capture",
     "utility_tool", "screenshot", {}),

    # ── Time / Date ───────────────────────────────────────────────────────
    (r"(?:what(?:'s|\s+is)\s+the\s+)?(?:current\s+)?time|what\s+time\s+is\s+it|kitne\s+baje",
     "info_tool", "get_time", {}),
    (r"(?:what(?:'s|\s+is)\s+(?:today(?:'s)?|the)\s+)?date|what\s+day\s+is\s+it|aaj\s+kya\s+date",
     "info_tool", "get_date", {}),

    # ── Info ──────────────────────────────────────────────────────────────
    (r"(?:tell\s+me\s+a\s+|crack\s+a\s+)?joke|make\s+me\s+laugh",
     "info_tool", "tell_joke", {}),
    (r"(?:fun|random|interesting)\s+fact|did\s+you\s+know",
     "info_tool", "fun_fact", {}),
    (r"(?:motivational|motivate\s+me|give\s+me\s+a)\s+quote|inspire\s+me",
     "info_tool", "motivational_quote", {}),
    (r"flip\s+(?:a\s+)?coin|heads\s+or\s+tails",
     "info_tool", "flip_coin", {}),
    (r"roll\s+(?:a\s+)?(?:dice|die)|throw\s+dice",
     "info_tool", "roll_dice", {}),
    (r"who\s+are\s+you|what\s+are\s+you|introduce\s+yourself|about\s+(?:you|nova)",
     "info_tool", "introduce", {}),

    # ── Notes ─────────────────────────────────────────────────────────────
    (r"(?:show|read|list|my)\s+notes|show\s+me\s+my\s+notes",
     "notes_tool", "list_notes", {}),
    (r"(?:yesterday(?:'s)?|recent)\s+notes",
     "notes_tool", "get_recent_notes", {"date": "yesterday"}),

    # ── Folder shortcuts ──────────────────────────────────────────────────
    (r"open\s+downloads(?:\s+folder)?",
     "file_tool", "open_folder", {"folder": "downloads"}),
    (r"open\s+desktop(?:\s+folder)?",
     "file_tool", "open_folder", {"folder": "desktop"}),
    (r"open\s+documents(?:\s+folder)?",
     "file_tool", "open_folder", {"folder": "documents"}),
    (r"open\s+(?:file\s+)?explorer|open\s+(?:my\s+)?(?:files?|folder)",
     "system_tool", "open_app", {"app_name": "explorer"}),

    # ── Dev shortcuts ─────────────────────────────────────────────────────
    (r"open\s+vs\s*code|open\s+vscode|launch\s+vs\s*code",
     "system_tool", "open_app", {"app_name": "vscode"}),
    (r"git\s+status",
     "dev_tool", "git_status", {}),
    (r"git\s+log",
     "dev_tool", "git_log", {}),
    (r"git\s+pull",
     "dev_tool", "git_pull", {}),

    # ── Localhost ─────────────────────────────────────────────────────────
    (r"open\s+localhost(?::(\d+))?|go\s+to\s+localhost",
     "browser_tool", "open_localhost", _port),

    # ── Browser ───────────────────────────────────────────────────────────
    (r"open\s+chrome|launch\s+chrome",
     "system_tool", "open_app", {"app_name": "chrome"}),
    (r"open\s+(?:fire\s*fox|firefox)",
     "system_tool", "open_app", {"app_name": "firefox"}),
    (r"open\s+(?:edge|microsoft\s+edge)",
     "system_tool", "open_app", {"app_name": "edge"}),

    # ── Workflow shortcuts ────────────────────────────────────────────────
    (r"morning\s+routine|good\s+morning\s+nova",
     "workflow_tool", "morning_routine", {}),
    (r"focus\s+mode|pomodoro|do\s+not\s+disturb",
     "workflow_tool", "focus_mode", {"duration": "25 minutes"}),
    (r"interview\s+prep(?:aration)?",
     "workflow_tool", "interview_prep", {}),
]


# ─── Compiled Route Table ─────────────────────────────────────────────────────

FAST_ROUTES: list[RouteEntry] = [
    (re.compile(pattern, re.IGNORECASE), tool, action, params)
    for pattern, tool, action, params in _RAW_ROUTES
]


# ─── Router Function ──────────────────────────────────────────────────────────

def fast_route(query: str) -> tuple[str, str, dict] | None:
    """
    Attempt to match the query against fast routes.
    Returns (tool_name, action, params) if matched, else None.
    """
    for pattern, tool, action, params_or_fn in FAST_ROUTES:
        m = pattern.search(query)
        if m:
            if callable(params_or_fn):
                resolved = params_or_fn(m)
            else:
                resolved = dict(params_or_fn)  # copy to avoid mutation
            return tool, action, resolved
    return None
