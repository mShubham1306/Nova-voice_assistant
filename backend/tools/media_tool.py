"""
NOVA Tool — Media Control
Play/pause music, track navigation, and volume via media keys.
"""

from __future__ import annotations

from typing import Any

from tools.base_tool import BaseTool, ToolResult, param

try:
    import pyautogui
    _PYAUTOGUI = True
except ImportError:
    _PYAUTOGUI = False


class MediaTool(BaseTool):
    name = "media_tool"
    description = (
        "Controls media playback: play, pause, skip tracks, go back, "
        "and searches for music on YouTube or Spotify."
    )
    actions = [
        "play_pause",
        "next_track",
        "previous_track",
        "stop",
        "play_on_youtube",
        "play_on_spotify",
    ]
    parameters = {
        "play_on_youtube": {
            "query": param("string", "Song name, artist, or playlist to search and play on YouTube", required=True),
        },
        "play_on_spotify": {
            "query": param("string", "Song name, artist, or playlist to search on Spotify", required=True),
        },
    }

    def execute(self, action: str, params: dict[str, Any]) -> ToolResult:
        dispatch = {
            "play_pause":       self._play_pause,
            "next_track":       self._next_track,
            "previous_track":   self._previous_track,
            "stop":             self._stop,
            "play_on_youtube":  self._play_youtube,
            "play_on_spotify":  self._play_spotify,
        }
        fn = dispatch.get(action)
        if fn is None:
            return self._not_implemented(action)
        return fn(params)

    def _require_pyautogui(self) -> ToolResult | None:
        if not _PYAUTOGUI:
            return ToolResult.fail("Media key control unavailable — pyautogui not installed.")
        return None

    def _play_pause(self, p: dict) -> ToolResult:
        if err := self._require_pyautogui():
            return err
        pyautogui.press("playpause")
        return ToolResult.ok("Toggled play/pause.")

    def _next_track(self, p: dict) -> ToolResult:
        if err := self._require_pyautogui():
            return err
        pyautogui.press("nexttrack")
        return ToolResult.ok("Skipped to the next track.")

    def _previous_track(self, p: dict) -> ToolResult:
        if err := self._require_pyautogui():
            return err
        pyautogui.press("prevtrack")
        return ToolResult.ok("Went back to the previous track.")

    def _stop(self, p: dict) -> ToolResult:
        if err := self._require_pyautogui():
            return err
        pyautogui.press("stop")
        return ToolResult.ok("Stopped playback.")

    def _play_youtube(self, p: dict) -> ToolResult:
        query = p.get("query", "").strip()
        if not query:
            return ToolResult.fail("Please specify what to play.")
        import webbrowser
        from urllib.parse import quote_plus
        url = f"https://www.youtube.com/results?search_query={quote_plus(query)}"
        webbrowser.open(url)
        return ToolResult.ok(f"Searching YouTube for '{query}'.")

    def _play_spotify(self, p: dict) -> ToolResult:
        query = p.get("query", "").strip()
        if not query:
            return ToolResult.fail("Please specify what to play on Spotify.")
        import webbrowser
        from urllib.parse import quote_plus
        url = f"https://open.spotify.com/search/{quote_plus(query)}"
        webbrowser.open(url)
        return ToolResult.ok(f"Searching Spotify for '{query}'.")
