"""
NOVA Task Module - AI Chat
Handles AI conversation using Google Gemini API for complex queries.
Supports 40+ Indian and global languages with auto-detection.
"""

import google.generativeai as genai
from config import Config


# Supported languages for display and documentation
SUPPORTED_LANGUAGES = {
    # Indian Languages
    "hi": "Hindi", "gu": "Gujarati", "bn": "Bengali", "ta": "Tamil",
    "te": "Telugu", "kn": "Kannada", "ml": "Malayalam", "mr": "Marathi",
    "pa": "Punjabi", "or": "Odia", "as": "Assamese", "ur": "Urdu",
    "sa": "Sanskrit", "ne": "Nepali", "sd": "Sindhi", "ks": "Kashmiri",
    "kok": "Konkani", "mai": "Maithili", "doi": "Dogri", "bh": "Bhojpuri",
    # European Languages
    "en": "English", "fr": "French", "de": "German", "es": "Spanish",
    "it": "Italian", "pt": "Portuguese", "nl": "Dutch", "pl": "Polish",
    "ru": "Russian", "uk": "Ukrainian", "sv": "Swedish", "da": "Danish",
    "no": "Norwegian", "fi": "Finnish", "el": "Greek", "cs": "Czech",
    "ro": "Romanian", "hu": "Hungarian",
    # Asian Languages
    "zh": "Chinese", "ja": "Japanese", "ko": "Korean", "th": "Thai",
    "vi": "Vietnamese", "id": "Indonesian", "ms": "Malay", "tl": "Filipino",
    # Middle Eastern & African
    "ar": "Arabic", "fa": "Persian", "he": "Hebrew", "tr": "Turkish",
    "sw": "Swahili", "am": "Amharic",
}

MULTILINGUAL_SYSTEM_PROMPT = """You are Nova, a friendly and highly intelligent AI voice assistant.

CRITICAL LANGUAGE RULE:
- Detect the language of the user's message automatically.
- ALWAYS respond in the SAME language the user wrote/spoke in.
- If the user writes in Hindi, reply in Hindi. If in Gujarati, reply in Gujarati. If in French, reply in French. And so on.
- If the user writes in a mix of languages (like Hinglish = Hindi + English), respond in the same mixed style.
- You understand and can respond fluently in 40+ languages including: Hindi, Gujarati, Bengali, Tamil, Telugu, Kannada, Malayalam, Marathi, Punjabi, Odia, Urdu, Nepali, Sanskrit, French, German, Spanish, Italian, Portuguese, Dutch, Russian, Chinese, Japanese, Korean, Arabic, Turkish, Thai, Vietnamese, and many more.

RESPONSE STYLE:
- Keep responses concise (under 100 words) and conversational since they will be spoken aloud.
- Be helpful, accurate, warm, and friendly.
- Use natural phrasing for the detected language (not robotic translations).
- For Indian languages, feel free to use common colloquial expressions.
"""


class AIChat:
    """AI conversation module powered by Google Gemini with multilingual support."""

    def __init__(self, voice):
        self.voice = voice
        self.model = None
        self.chat = None
        self.conversation_history = []
        self._init_gemini()

    def _init_gemini(self):
        """Initialize Gemini AI if API key is available."""
        if Config.GEMINI_API_KEY:
            try:
                genai.configure(api_key=Config.GEMINI_API_KEY)
                self.model = genai.GenerativeModel(
                    "gemini-1.5-flash",
                    system_instruction=MULTILINGUAL_SYSTEM_PROMPT
                )
                self.chat = self.model.start_chat(history=[])
                print("[AI] Gemini AI initialized with multilingual support (40+ languages).")
            except Exception as e:
                print(f"[AI] Failed to initialize Gemini: {e}")
                self.model = None
        else:
            print("[AI] No Gemini API key provided. AI chat will use fallback responses.")

    def ask(self, query):
        """Ask a question to the AI — auto-detects language and responds accordingly."""
        # Clean the query
        clean_query = query.strip()
        # Only strip English prefixes if query appears to be in English
        lower_q = clean_query.lower()
        for prefix in ["ask ai", "ask nova", "chat", "tell me about", "explain",
                        "how to", "nova"]:
            if lower_q.startswith(prefix):
                clean_query = clean_query[len(prefix):].strip()
                lower_q = clean_query.lower()

        if not clean_query:
            self.voice.speak("What would you like to know?")
            return "Please ask me a question."

        # Try Gemini AI first
        if self.model and self.chat:
            try:
                response = self.chat.send_message(clean_query)
                answer = response.text.strip()

                # Store in history
                self.conversation_history.append({
                    "question": clean_query,
                    "answer": answer
                })

                self.voice.speak(answer)
                return answer

            except Exception as e:
                print(f"[AI Error] {e}")
                # Fall through to fallback

        # Fallback: intelligent responses for common topics
        return self._fallback_response(clean_query)

    def _fallback_response(self, query):
        """Provide fallback responses when Gemini is unavailable."""
        lower_q = query.lower()
        responses = {
            "how are you": "I'm doing great, thank you for asking! I'm Nova, always ready to help you.",
            "what can you do": "I can control your system, search the web, play media, give weather updates, tell jokes, take notes, set timers, do calculations, and have conversations — in 40+ languages!",
            "thank you": "You're welcome! Happy to help anytime.",
            "thanks": "My pleasure! Let me know if you need anything else.",
            "good morning": "Good morning! Hope you have a wonderful day ahead!",
            "good night": "Good night! Sweet dreams and see you tomorrow!",
            "hello": "Hello! It's great to talk to you. How can I help?",
            "help": "I can help with: opening apps, searching Google/YouTube/Wikipedia, screenshots, timers, weather, news, calculations, notes, jokes, facts, and AI conversations — all in 40+ languages! Just ask!",
            # Hindi fallbacks
            "नमस्ते": "नमस्ते! मैं Nova हूँ, आपकी AI आवाज सहायक। कैसे मदद कर सकती हूँ?",
            "कैसे हो": "मैं बिल्कुल ठीक हूँ! आपकी क्या मदद करूँ?",
            "धन्यवाद": "आपका स्वागत है! किसी और चीज़ में मदद चाहिए?",
            # Gujarati fallbacks
            "કેમ છો": "હું સારી છું! Nova છું, તમારી AI સહાયક. કેવી રીતે મદદ કરું?",
        }

        for key, response in responses.items():
            if key in lower_q:
                self.voice.speak(response)
                return response

        # Generic fallback
        import webbrowser
        search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        webbrowser.open(search_url)
        self.voice.speak(f"I've searched Google for that. Let me know if you need more help.")
        return f"Searched Google for: {query}"

    @staticmethod
    def get_supported_languages():
        """Return the list of supported languages."""
        return SUPPORTED_LANGUAGES

