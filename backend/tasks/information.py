"""
NOVA Task Module - Information
Weather, news, time, date, jokes, facts, dictionary, translation, quotes, dice, coin.
"""

import datetime
import random
import requests


class Information:
    """Information retrieval operations for NOVA."""

    def __init__(self, voice):
        self.voice = voice

    def get_time(self):
        """Get current time."""
        now = datetime.datetime.now()
        time_str = now.strftime("%I:%M %p")
        msg = f"The current time is {time_str}."
        self.voice.speak(msg)
        return msg

    def get_date(self):
        """Get current date."""
        now = datetime.datetime.now()
        date_str = now.strftime("%A, %B %d, %Y")
        msg = f"Today is {date_str}."
        self.voice.speak(msg)
        return msg

    def get_weather(self, query):
        """Get weather info (using wttr.in API - no key required)."""
        city = query.lower()
        for prefix in ["weather in", "weather at", "weather for", "temperature in",
                       "forecast for", "weather", "temperature", "forecast"]:
            city = city.replace(prefix, "")
        city = city.strip() or "auto"

        try:
            url = f"https://wttr.in/{city}?format=%C+%t+%h+%w"
            response = requests.get(url, timeout=5, headers={"User-Agent": "curl"})
            if response.status_code == 200:
                weather = response.text.strip()
                if city == "auto":
                    msg = f"Current weather: {weather}."
                else:
                    msg = f"Weather in {city}: {weather}."
                self.voice.speak(msg)
                return msg
        except Exception:
            pass

        self.voice.speak("I couldn't fetch the weather right now.")
        return "Weather data unavailable."

    def get_news(self):
        """Get top news headlines (using RSS feeds)."""
        try:
            # Simple approach: open Google News
            import webbrowser
            webbrowser.open("https://news.google.com")
            self.voice.speak("Opening Google News for you.")
            return "Opened Google News."
        except Exception:
            self.voice.speak("Couldn't open the news.")
            return "News unavailable."

    def tell_joke(self):
        """Tell a random joke."""
        jokes = [
            "Why don't scientists trust atoms? Because they make up everything!",
            "Why did the scarecrow win an award? He was outstanding in his field!",
            "I told my wife she was drawing her eyebrows too high. She looked surprised.",
            "Why don't eggs tell jokes? They'd crack each other up!",
            "What do you call a fake noodle? An impasta!",
            "Why did the math book look so sad? Because it had too many problems.",
            "What do you call a bear with no teeth? A gummy bear!",
            "Why can't a bicycle stand on its own? Because it's two-tired!",
            "I'm reading a book about anti-gravity. It's impossible to put down!",
            "What did the ocean say to the beach? Nothing, it just waved.",
            "Why don't skeletons fight each other? They don't have the guts!",
            "What do you call a lazy kangaroo? A pouch potato!",
            "I used to hate facial hair, but then it grew on me.",
            "Why did the coffee file a police report? It got mugged!",
            "What do you call a dog magician? A Labracadabrador!",
        ]
        joke = random.choice(jokes)
        self.voice.speak(joke)
        return joke

    def fun_fact(self):
        """Tell a random fun fact."""
        facts = [
            "Honey never spoils. Archaeologists have found 3000-year-old honey in Egyptian tombs that was still edible!",
            "Octopuses have three hearts and blue blood.",
            "A group of flamingos is called a 'flamboyance'.",
            "The shortest war in history lasted 38 minutes, between Britain and Zanzibar.",
            "Bananas are berries, but strawberries aren't!",
            "A day on Venus is longer than a year on Venus.",
            "The first computer programmer was Ada Lovelace in the 1840s.",
            "There are more stars in the universe than grains of sand on Earth.",
            "The human brain uses 20% of the body's total energy.",
            "Light takes 8 minutes and 20 seconds to travel from the Sun to Earth.",
            "The Great Wall of China is not visible from space with the naked eye.",
            "Cows have best friends and get stressed when separated.",
            "A cloud can weigh more than a million pounds!",
            "The inventor of the Pringles can is buried in one.",
            "Sea otters hold hands while sleeping to keep from drifting apart.",
        ]
        fact = random.choice(facts)
        self.voice.speak(f"Fun fact: {fact}")
        return fact

    def define_word(self, query):
        """Get the definition of a word."""
        word = query.lower()
        for prefix in ["define", "meaning of", "definition of", "what does", "mean"]:
            word = word.replace(prefix, "")
        word = word.strip()

        if word:
            try:
                url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    definition = data[0]["meanings"][0]["definitions"][0]["definition"]
                    part = data[0]["meanings"][0]["partOfSpeech"]
                    msg = f"{word.capitalize()} ({part}): {definition}"
                    self.voice.speak(msg)
                    return msg
            except Exception:
                pass

            # Fallback: open dictionary.com
            import webbrowser
            webbrowser.open(f"https://www.dictionary.com/browse/{word}")
            self.voice.speak(f"Opening the dictionary for {word}.")
            return f"Opened dictionary for: {word}"

        return "Which word would you like me to define?"

    def translate(self, query):
        """Open Google Translate for a translation request."""
        import webbrowser
        text = query.lower()
        for prefix in ["translate", "translation of", "translation"]:
            text = text.replace(prefix, "")
        text = text.strip()

        if text:
            url = f"https://translate.google.com/?sl=auto&tl=en&text={text.replace(' ', '%20')}&op=translate"
            webbrowser.open(url)
            self.voice.speak(f"Opening Google Translate for: {text}")
            return f"Opened Google Translate for: {text}"

        import webbrowser
        webbrowser.open("https://translate.google.com")
        self.voice.speak("Opening Google Translate.")
        return "Opened Google Translate."

    def motivational_quote(self):
        """Share a motivational quote."""
        quotes = [
            "The only way to do great work is to love what you do. — Steve Jobs",
            "Innovation distinguishes between a leader and a follower. — Steve Jobs",
            "Stay hungry, stay foolish. — Steve Jobs",
            "The future belongs to those who believe in the beauty of their dreams. — Eleanor Roosevelt",
            "It does not matter how slowly you go as long as you do not stop. — Confucius",
            "Success is not final, failure is not fatal: It is the courage to continue that counts. — Winston Churchill",
            "Believe you can and you're halfway there. — Theodore Roosevelt",
            "The best time to plant a tree was 20 years ago. The second best time is now. — Chinese Proverb",
            "Your time is limited, don't waste it living someone else's life. — Steve Jobs",
            "Be the change that you wish to see in the world. — Mahatma Gandhi",
            "In the middle of difficulty lies opportunity. — Albert Einstein",
            "The only impossible journey is the one you never begin. — Tony Robbins",
        ]
        quote = random.choice(quotes)
        self.voice.speak(quote)
        return quote

    def flip_coin(self):
        """Flip a virtual coin."""
        result = random.choice(["Heads", "Tails"])
        msg = f"I flipped a coin and it landed on {result}!"
        self.voice.speak(msg)
        return msg

    def roll_dice(self):
        """Roll a virtual dice."""
        result = random.randint(1, 6)
        msg = f"I rolled a dice and got {result}!"
        self.voice.speak(msg)
        return msg

    def introduce(self):
        """Introduce NOVA."""
        intro = (
            "I'm Nova, your AI voice assistant! I can help you with system controls, "
            "web searches, media playback, weather updates, news, calculations, notes, "
            "screenshots, timers, definitions, translations, and much more. "
            "Just say 'Hey Nova' followed by your command!"
        )
        self.voice.speak(intro)
        return intro
