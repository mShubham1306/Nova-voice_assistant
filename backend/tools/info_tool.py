"""
NOVA Tool — Information
Time, date, weather, news, jokes, facts, definitions, translations,
motivational quotes, coin flip, dice roll, and NOVA's self-introduction.
"""

from __future__ import annotations

import datetime
import random
from typing import Any
from urllib.parse import quote_plus

import requests

from tools.base_tool import BaseTool, ToolResult, param


class InfoTool(BaseTool):
    name = "info_tool"
    description = (
        "Provides information: current time, date, live weather, latest news, "
        "word definitions, language translations, jokes, fun facts, motivational quotes, "
        "coin flips, dice rolls, and introduces NOVA."
    )
    actions = [
        "get_time",
        "get_date",
        "get_weather",
        "get_news",
        "define_word",
        "translate",
        "tell_joke",
        "fun_fact",
        "motivational_quote",
        "flip_coin",
        "roll_dice",
        "introduce",
    ]
    parameters = {
        "get_weather": {
            "city": param("string", "City name to get weather for, e.g. 'Mumbai', 'London'"),
        },
        "define_word": {
            "word": param("string", "Word to define", required=True),
        },
        "translate": {
            "text": param("string", "Text to translate", required=True),
            "target_language": param("string", "Target language, e.g. 'Hindi', 'French', 'Spanish'"),
        },
        "roll_dice": {
            "sides": param("integer", "Number of sides on the dice (default 6)"),
            "count": param("integer", "Number of dice to roll (default 1)"),
        },
    }

    _JOKES = [
        "Why do programmers prefer dark mode? Because light attracts bugs!",
        "Why did the developer quit? Because he didn't get arrays.",
        "I told my computer I needed a break. Now it won't stop sending me Kit Kat ads.",
        "Why do Java developers wear glasses? Because they don't C#.",
        "A SQL query walks into a bar, walks up to two tables and asks... 'Can I join you?'",
        "What's a computer's favorite snack? Microchips.",
        "Why was the function sad? Because it had too many arguments.",
        "I would tell you a joke about UDP but I'm not sure you'd get it.",
        "There are 10 kinds of people: those who understand binary and those who don't.",
        "Why did the programmer go broke? Because he used up all his cache.",
    ]

    _FACTS = [
        "The first computer bug was an actual bug — a moth found in a Harvard Mark II computer in 1947.",
        "The average person spends 6 years and 8 months of their life on social media.",
        "There are more possible iterations of a game of chess than atoms in the observable universe.",
        "The original name of Windows was 'Interface Manager'.",
        "Python was named after Monty Python, not the snake.",
        "The first mouse was made of wood.",
        "E-mail predates the World Wide Web by about 12 years.",
        "India has the most internet users in the world after China.",
        "The first 1GB hard drive cost $40,000 in 1980.",
        "More than 50% of all internet traffic is from mobile devices.",
    ]

    _QUOTES = [
        "The best way to predict the future is to invent it. — Alan Kay",
        "Code is like humor. When you have to explain it, it's bad. — Cory House",
        "First, solve the problem. Then, write the code. — John Johnson",
        "Experience is the name everyone gives to their mistakes. — Oscar Wilde",
        "In order to be irreplaceable, one must always be different. — Coco Chanel",
        "The harder I work, the luckier I get. — Samuel Goldwyn",
        "Don't watch the clock; do what it does. Keep going. — Sam Levenson",
        "Believe you can and you're halfway there. — Theodore Roosevelt",
        "The only way to do great work is to love what you do. — Steve Jobs",
        "Your time is limited, so don't waste it living someone else's life. — Steve Jobs",
    ]

    def execute(self, action: str, params: dict[str, Any]) -> ToolResult:
        dispatch = {
            "get_time":          self._get_time,
            "get_date":          self._get_date,
            "get_weather":       self._get_weather,
            "get_news":          self._get_news,
            "define_word":       self._define_word,
            "translate":         self._translate,
            "tell_joke":         self._tell_joke,
            "fun_fact":          self._fun_fact,
            "motivational_quote": self._motivational_quote,
            "flip_coin":         self._flip_coin,
            "roll_dice":         self._roll_dice,
            "introduce":         self._introduce,
        }
        fn = dispatch.get(action)
        if fn is None:
            return self._not_implemented(action)
        return fn(params)

    def _get_time(self, p: dict) -> ToolResult:
        now = datetime.datetime.now()
        t = now.strftime("%I:%M %p")
        return ToolResult.ok(f"The current time is {t}.", data={"time": t})

    def _get_date(self, p: dict) -> ToolResult:
        now = datetime.datetime.now()
        d = now.strftime("%A, %d %B %Y")
        return ToolResult.ok(f"Today is {d}.", data={"date": d})

    def _get_weather(self, p: dict) -> ToolResult:
        city = p.get("city", "").strip() or "your city"
        try:
            # Using wttr.in — free, no API key needed
            url = f"https://wttr.in/{quote_plus(city)}?format=3"
            resp = requests.get(url, timeout=5)
            if resp.ok:
                weather_text = resp.text.strip()
                return ToolResult.ok(f"Weather in {city}: {weather_text}", data={"raw": weather_text})
            return ToolResult.fail(f"Could not fetch weather for {city}.")
        except Exception:
            return ToolResult.fail(f"Weather service is unavailable right now.")

    def _get_news(self, p: dict) -> ToolResult:
        try:
            url = "https://feeds.bbci.co.uk/news/rss.xml"
            resp = requests.get(url, timeout=5)
            if resp.ok:
                import re
                titles = re.findall(r"<title>(.*?)</title>", resp.text)
                # Skip the first (channel title)
                headlines = [t for t in titles[1:6] if t and "BBC" not in t]
                if headlines:
                    msg = "Top headlines: " + ". ".join(f"{i+1}. {h}" for i, h in enumerate(headlines))
                    return ToolResult.ok(msg, data={"headlines": headlines})
            return ToolResult.fail("Could not fetch news right now.")
        except Exception:
            return ToolResult.fail("News service unavailable. Please check your internet connection.")

    def _define_word(self, p: dict) -> ToolResult:
        word = p.get("word", "").strip().lower()
        if not word:
            return ToolResult.fail("Please specify a word to define.")
        try:
            url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{quote_plus(word)}"
            resp = requests.get(url, timeout=5)
            if resp.ok:
                data = resp.json()
                if data and isinstance(data, list):
                    meanings = data[0].get("meanings", [])
                    if meanings:
                        part = meanings[0].get("partOfSpeech", "word")
                        defs = meanings[0].get("definitions", [])
                        if defs:
                            defn = defs[0].get("definition", "")
                            msg = f"{word.capitalize()} ({part}): {defn}"
                            return ToolResult.ok(msg, data={"word": word, "definition": defn, "part": part})
            return ToolResult.fail(f"Couldn't find a definition for '{word}'.")
        except Exception:
            # Fallback — open in browser
            import webbrowser
            webbrowser.open(f"https://www.google.com/search?q=define+{quote_plus(word)}")
            return ToolResult.ok(f"Opened Google definition for '{word}'.")

    def _translate(self, p: dict) -> ToolResult:
        text = p.get("text", "").strip()
        lang = p.get("target_language", "Hindi").strip()
        if not text:
            return ToolResult.fail("Please specify the text to translate.")
        import webbrowser
        url = f"https://translate.google.com/?sl=auto&tl={quote_plus(lang)}&text={quote_plus(text)}&op=translate"
        webbrowser.open(url)
        return ToolResult.ok(f"Opened Google Translate for '{text}' to {lang}.")

    def _tell_joke(self, p: dict) -> ToolResult:
        joke = random.choice(self._JOKES)
        return ToolResult.ok(joke, data={"joke": joke})

    def _fun_fact(self, p: dict) -> ToolResult:
        fact = random.choice(self._FACTS)
        return ToolResult.ok(f"Here's a fun fact: {fact}", data={"fact": fact})

    def _motivational_quote(self, p: dict) -> ToolResult:
        quote = random.choice(self._QUOTES)
        return ToolResult.ok(quote, data={"quote": quote})

    def _flip_coin(self, p: dict) -> ToolResult:
        result = random.choice(["Heads", "Tails"])
        return ToolResult.ok(f"I flipped a coin and got... {result}!", data={"result": result})

    def _roll_dice(self, p: dict) -> ToolResult:
        sides = max(2, int(p.get("sides", 6)))
        count = max(1, min(int(p.get("count", 1)), 10))
        rolls = [random.randint(1, sides) for _ in range(count)]
        total = sum(rolls)
        if count == 1:
            return ToolResult.ok(f"Rolled a d{sides} and got {rolls[0]}!", data={"rolls": rolls, "total": total})
        return ToolResult.ok(f"Rolled {count}d{sides}: {rolls}. Total: {total}.", data={"rolls": rolls, "total": total})

    def _introduce(self, p: dict) -> ToolResult:
        msg = (
            "I'm Nova, your AI Operating Assistant. I can open apps, search the web, manage your files, "
            "control media, run developer workflows, take notes, set timers, check the weather, and much more. "
            "Just speak naturally and I'll figure out what to do. "
            "For example, say 'prepare my coding environment' and I'll start all your dev tools at once!"
        )
        return ToolResult.ok(msg)
