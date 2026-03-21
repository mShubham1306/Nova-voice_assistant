"""
NOVA Task Module - Web Search
Handles searching Google, YouTube, Wikipedia, StackOverflow, and opening websites.
"""

import webbrowser
from config import Config


class WebSearch:
    """Web search and browsing operations for NOVA."""

    def __init__(self, voice):
        self.voice = voice

    def google_search(self, query):
        """Search Google."""
        search_term = self._extract_search_term(query, ["search google", "google search", "google for", "google", "search"])
        if search_term:
            url = f"https://www.google.com/search?q={search_term.replace(' ', '+')}"
            webbrowser.open(url)
            self.voice.speak(f"Searching Google for {search_term}.")
            return f"Searched Google for: {search_term}"
        self.voice.speak("What would you like to search for?")
        return "Please specify a search query."

    def youtube_search(self, query):
        """Search YouTube."""
        search_term = self._extract_search_term(query, ["search youtube", "youtube search", "play on youtube", "youtube", "play"])
        if search_term:
            url = f"https://www.youtube.com/results?search_query={search_term.replace(' ', '+')}"
            webbrowser.open(url)
            self.voice.speak(f"Searching YouTube for {search_term}.")
            return f"Searched YouTube for: {search_term}"
        else:
            webbrowser.open("https://www.youtube.com")
            self.voice.speak("Opening YouTube.")
            return "Opened YouTube."

    def wikipedia_search(self, query):
        """Search Wikipedia."""
        search_term = self._extract_search_term(query, ["search wikipedia", "wikipedia", "wiki", "search"])
        if search_term:
            url = f"https://en.wikipedia.org/wiki/{search_term.replace(' ', '_')}"
            webbrowser.open(url)
            self.voice.speak(f"Searching Wikipedia for {search_term}.")
            return f"Searched Wikipedia for: {search_term}"
        self.voice.speak("What would you like to look up on Wikipedia?")
        return "Please specify a topic."

    def stackoverflow_search(self, query):
        """Search Stack Overflow."""
        search_term = self._extract_search_term(query, ["search stackoverflow", "stack overflow", "stackoverflow"])
        if search_term:
            url = f"https://stackoverflow.com/search?q={search_term.replace(' ', '+')}"
            webbrowser.open(url)
            self.voice.speak(f"Searching Stack Overflow for {search_term}.")
            return f"Searched Stack Overflow for: {search_term}"
        self.voice.speak("What programming question do you have?")
        return "Please specify a query."

    def open_website(self, query):
        """Open a specific website."""
        # Check shortcuts first
        for site_name, url in Config.WEBSITE_SHORTCUTS.items():
            if site_name in query.lower():
                webbrowser.open(url)
                self.voice.speak(f"Opening {site_name}.")
                return f"Opened {site_name}."

        # Extract domain name
        site = query.lower()
        for prefix in ["open website", "go to website", "visit", "open", "go to"]:
            site = site.replace(prefix, "")
        site = site.strip()

        if site:
            if not site.startswith("http"):
                site = f"https://www.{site}.com" if "." not in site else f"https://{site}"
            webbrowser.open(site)
            self.voice.speak(f"Opening {site}.")
            return f"Opened {site}."

        return "Please specify a website."

    def _extract_search_term(self, query, prefixes):
        """Extract the actual search term by removing command prefixes."""
        result = query.lower()
        for prefix in prefixes:
            result = result.replace(prefix, "")
        result = result.strip()
        return result if result else None
