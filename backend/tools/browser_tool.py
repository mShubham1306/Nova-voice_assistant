"""
NOVA Tool — Browser & Web Search
Web searches, navigation, Wikipedia, YouTube, GitHub, StackOverflow.
"""

from __future__ import annotations

import webbrowser
from typing import Any
from urllib.parse import quote_plus

from tools.base_tool import BaseTool, ToolResult, param


class BrowserTool(BaseTool):
    name = "browser_tool"
    description = (
        "Opens websites, searches Google, YouTube, Wikipedia, GitHub, StackOverflow, "
        "and any custom URL. Controls browser navigation."
    )
    actions = [
        "google_search",
        "youtube_search",
        "wikipedia_search",
        "stackoverflow_search",
        "github_search",
        "open_url",
        "open_website",
        "open_localhost",
    ]
    parameters = {
        "google_search": {
            "query": param("string", "Search query for Google", required=True),
        },
        "youtube_search": {
            "query": param("string", "Search query for YouTube — song name, artist, video topic", required=True),
        },
        "wikipedia_search": {
            "query": param("string", "Topic to search on Wikipedia", required=True),
        },
        "stackoverflow_search": {
            "query": param("string", "Programming question or error to search on StackOverflow", required=True),
        },
        "github_search": {
            "query": param("string", "Repository or topic to search on GitHub", required=True),
        },
        "open_url": {
            "url": param("string", "Full URL to open e.g. https://example.com", required=True),
        },
        "open_website": {
            "site": param("string", "Website name or domain, e.g. 'netflix', 'linkedin', 'amazon'", required=True),
        },
        "open_localhost": {
            "port": param("integer", "Localhost port number to open (default 3000)"),
            "path": param("string", "URL path to append, e.g. '/api/docs'"),
        },
    }

    def execute(self, action: str, params: dict[str, Any]) -> ToolResult:
        dispatch = {
            "google_search":       self._google,
            "youtube_search":      self._youtube,
            "wikipedia_search":    self._wikipedia,
            "stackoverflow_search": self._stackoverflow,
            "github_search":       self._github,
            "open_url":            self._open_url,
            "open_website":        self._open_website,
            "open_localhost":      self._open_localhost,
        }
        fn = dispatch.get(action)
        if fn is None:
            return self._not_implemented(action)
        return fn(params)

    def _google(self, p: dict) -> ToolResult:
        q = p.get("query", "").strip()
        if not q:
            return ToolResult.fail("Please specify what to search for.")
        url = f"https://www.google.com/search?q={quote_plus(q)}"
        webbrowser.open(url)
        return ToolResult.ok(f"Searching Google for '{q}'.")

    def _youtube(self, p: dict) -> ToolResult:
        q = p.get("query", "").strip()
        if not q:
            return ToolResult.fail("Please specify what to search on YouTube.")
        url = f"https://www.youtube.com/results?search_query={quote_plus(q)}"
        webbrowser.open(url)
        return ToolResult.ok(f"Searching YouTube for '{q}'.")

    def _wikipedia(self, p: dict) -> ToolResult:
        q = p.get("query", "").strip()
        if not q:
            return ToolResult.fail("Please specify the Wikipedia topic.")
        url = f"https://en.wikipedia.org/wiki/Special:Search?search={quote_plus(q)}"
        webbrowser.open(url)
        return ToolResult.ok(f"Opening Wikipedia for '{q}'.")

    def _stackoverflow(self, p: dict) -> ToolResult:
        q = p.get("query", "").strip()
        if not q:
            return ToolResult.fail("Please specify what to search on StackOverflow.")
        url = f"https://stackoverflow.com/search?q={quote_plus(q)}"
        webbrowser.open(url)
        return ToolResult.ok(f"Searching StackOverflow for '{q}'.")

    def _github(self, p: dict) -> ToolResult:
        q = p.get("query", "").strip()
        if not q:
            return ToolResult.fail("Please specify what to search on GitHub.")
        url = f"https://github.com/search?q={quote_plus(q)}"
        webbrowser.open(url)
        return ToolResult.ok(f"Searching GitHub for '{q}'.")

    def _open_url(self, p: dict) -> ToolResult:
        url = p.get("url", "").strip()
        if not url:
            return ToolResult.fail("Please provide a URL.")
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        webbrowser.open(url)
        return ToolResult.ok(f"Opening {url}.")

    def _open_website(self, p: dict) -> ToolResult:
        from config import settings
        site = p.get("site", "").strip().lower()
        if not site:
            return ToolResult.fail("Please specify which website to open.")
        # Check shortcuts first
        for key, url in settings.WEBSITE_SHORTCUTS.items():
            if key in site or site in key:
                webbrowser.open(url)
                return ToolResult.ok(f"Opening {key}.")
        # Fallback: construct URL
        if "." in site:
            url = f"https://{site}" if not site.startswith("http") else site
        else:
            url = f"https://www.{site}.com"
        webbrowser.open(url)
        return ToolResult.ok(f"Opening {url}.")

    def _open_localhost(self, p: dict) -> ToolResult:
        port = int(p.get("port", 3000))
        path = p.get("path", "").strip().lstrip("/")
        url = f"http://localhost:{port}/{path}"
        webbrowser.open(url)
        return ToolResult.ok(f"Opening localhost:{port}.")
