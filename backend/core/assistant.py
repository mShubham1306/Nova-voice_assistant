"""
NOVA Assistant Core - Command Router & State Manager
Central brain that parses commands and dispatches to task modules.
"""

import datetime
import threading
from core.voice_engine import VoiceEngine
from tasks.system_control import SystemControl
from tasks.web_search import WebSearch
from tasks.media_control import MediaControl
from tasks.utilities import Utilities
from tasks.information import Information
from tasks.ai_chat import AIChat
from config import Config


class Assistant:
    """Central command router for NOVA voice assistant."""

    def __init__(self, socketio=None):
        self.socketio = socketio
        self.voice = VoiceEngine(socketio)
        self.is_running = False
        self.silent_mode = False
        self.command_history = []
        self.wake_word_mode = False
        self._thread = None

        # Initialize task modules
        self.system = SystemControl(self.voice)
        self.web = WebSearch(self.voice)
        self.media = MediaControl(self.voice)
        self.utils = Utilities(self.voice)
        self.info = Information(self.voice)
        self.ai = AIChat(self.voice)

        # Command routing map — order matters (first match wins)
        self.command_routes = [
            # Exit / Stop
            (["stop nova", "exit nova", "quit nova", "goodbye nova", "shut down", "stop assistant"],
             self._stop),

            # Silent mode
            (["shut up", "be quiet", "stay silent", "silent mode", "mute", "go silent"],
             self._go_silent),

            # Wake from silent
            (["hey nova", "nova", "wake up", "hello nova", "i need you"],
             self._wake_up),

            # System control
            (["open ", "launch ", "start app"],
             self.system.open_app),
            (["close app", "kill app", "close program"],
             self.system.close_app),
            (["volume up", "increase volume", "louder"],
             lambda q: self.system.volume_control("up")),
            (["volume down", "decrease volume", "quieter", "softer"],
             lambda q: self.system.volume_control("down")),
            (["mute volume", "unmute volume", "toggle mute"],
             lambda q: self.system.volume_control("mute")),
            (["brightness up", "increase brightness", "brighter"],
             lambda q: self.system.brightness_control("up")),
            (["brightness down", "decrease brightness", "dimmer"],
             lambda q: self.system.brightness_control("down")),
            (["battery", "battery status", "battery level", "power status"],
             lambda q: self.system.battery_status()),
            (["lock screen", "lock computer", "lock pc"],
             lambda q: self.system.lock_screen()),
            (["shutdown computer", "turn off computer", "shutdown pc"],
             lambda q: self.system.shutdown()),
            (["restart computer", "restart pc", "reboot"],
             lambda q: self.system.restart()),
            (["empty recycle bin", "clear recycle bin", "clean recycle"],
             lambda q: self.system.empty_recycle_bin()),
            (["system info", "system information", "pc info", "computer info"],
             lambda q: self.system.system_info()),
            (["cpu usage", "cpu status", "processor usage"],
             lambda q: self.system.cpu_usage()),
            (["memory usage", "ram usage", "ram status"],
             lambda q: self.system.memory_usage()),
            (["disk usage", "disk space", "storage space"],
             lambda q: self.system.disk_usage()),
            (["ip address", "my ip", "what is my ip"],
             lambda q: self.system.get_ip_address()),
            (["wifi", "wi-fi", "internet status"],
             lambda q: self.system.wifi_status()),

            # Web & search
            (["search youtube", "youtube search", "play on youtube"],
             self.web.youtube_search),
            (["search google", "google search", "google for"],
             self.web.google_search),
            (["search wikipedia", "wikipedia", "wiki"],
             self.web.wikipedia_search),
            (["search stackoverflow", "stack overflow"],
             self.web.stackoverflow_search),
            (["open website", "go to website", "visit"],
             self.web.open_website),

            # Media
            (["play music", "play song", "start music"],
             lambda q: self.media.play_pause()),
            (["pause music", "stop music", "pause song"],
             lambda q: self.media.play_pause()),
            (["next song", "next track", "skip song"],
             lambda q: self.media.next_track()),
            (["previous song", "previous track", "last song"],
             lambda q: self.media.previous_track()),

            # Utilities
            (["screenshot", "take screenshot", "capture screen", "screen capture"],
             lambda q: self.utils.take_screenshot()),
            (["set timer", "start timer", "timer for"],
             self.utils.set_timer),
            (["set alarm", "alarm for", "wake me"],
             self.utils.set_alarm),
            (["calculate", "what is", "math"],
             self.utils.calculate),
            (["take note", "save note", "write note", "note down"],
             self.utils.take_note),
            (["read notes", "show notes", "my notes"],
             lambda q: self.utils.read_notes()),
            (["clipboard", "copy text", "paste text", "what's copied"],
             lambda q: self.utils.clipboard_content()),
            (["type", "type out"],
             self.utils.type_text),

            # Information
            (["weather", "temperature", "forecast"],
             self.info.get_weather),
            (["news", "headlines", "latest news", "top news"],
             lambda q: self.info.get_news()),
            (["time", "what time", "current time"],
             lambda q: self.info.get_time()),
            (["date", "what date", "today's date", "what day"],
             lambda q: self.info.get_date()),
            (["joke", "tell me a joke", "make me laugh", "funny"],
             lambda q: self.info.tell_joke()),
            (["fun fact", "random fact", "interesting fact", "did you know"],
             lambda q: self.info.fun_fact()),
            (["define", "meaning of", "definition"],
             self.info.define_word),
            (["translate", "translation"],
             self.info.translate),
            (["motivate", "motivation", "inspire", "quote"],
             lambda q: self.info.motivational_quote()),
            (["flip a coin", "coin flip", "heads or tails"],
             lambda q: self.info.flip_coin()),
            (["roll a dice", "roll dice", "throw dice"],
             lambda q: self.info.roll_dice()),
            (["who are you", "what are you", "your name", "introduce yourself", "about you"],
             lambda q: self.info.introduce()),

            # AI Chat (Gemini) — fallback for complex queries
            (["ask ai", "ask nova", "chat", "tell me about", "explain", "how to", "what is", "why"],
             self.ai.ask),
        ]

    def process_command(self, query, skip_speech=False):
        """Route a text command to the appropriate handler.
        Supports multilingual input — detects language and translates keywords if needed.
        skip_speech: if True, suppress TTS (for text-typed commands from frontend).
        """
        if not query or query.strip() == "":
            return {"response": "I didn't catch that.", "type": "error"}

        # Mute voice for text commands (skip TTS to return response instantly)
        if skip_speech:
            self.voice.muted = True

        original_query = query.strip()
        query_lower = original_query.lower().strip()
        timestamp = datetime.datetime.now().isoformat()

        try:
            # Check silent mode (only respond to wake commands)
            if self.silent_mode:
                wake_words = ["hey nova", "nova", "wake up", "hello nova",
                              "हे नोवा", "नोवा", "जागो", "ノバ", "노바"]
                if any(w in query_lower for w in wake_words):
                    self._wake_up(query_lower)
                    result = {"response": "I'm back! How can I help?", "type": "wake"}
                else:
                    result = {"response": "(silent mode)", "type": "silent"}
                self._add_to_history(query_lower, result, timestamp)
                return result

            # Try to match English command routes first
            for keywords, handler in self.command_routes:
                if any(kw in query_lower for kw in keywords):
                    try:
                        response = handler(query_lower)
                        result = {"response": response or "Done!", "type": "success"}
                    except Exception as e:
                        print(f"[Command Error] {e}")
                        result = {"response": f"Sorry, something went wrong: {str(e)}", "type": "error"}
                    self._add_to_history(query_lower, result, timestamp)
                    return result

            # Try multilingual keyword matching (translate common commands)
            translated = self._translate_multilingual(query_lower)
            if translated and translated != query_lower:
                for keywords, handler in self.command_routes:
                    if any(kw in translated for kw in keywords):
                        try:
                            response = handler(translated)
                            result = {"response": response or "Done!", "type": "success"}
                        except Exception as e:
                            print(f"[Command Error] {e}")
                            result = {"response": f"Sorry, something went wrong: {str(e)}", "type": "error"}
                        self._add_to_history(original_query, result, timestamp)
                        return result

            # Fallback to AI chat (Gemini handles multilingual natively)
            try:
                response = self.ai.ask(original_query)
                result = {"response": response or "I'm not sure about that.", "type": "ai"}
            except Exception:
                result = {"response": "I didn't understand that. Try saying 'help' for available commands.", "type": "error"}

            self._add_to_history(original_query, result, timestamp)
            return result
        finally:
            # Always unmute after processing
            if skip_speech:
                self.voice.muted = False

    def _translate_multilingual(self, query):
        """Translate common non-English command keywords to English equivalents."""
        # Multilingual keyword mappings
        translations = {
            # Hindi
            "खोलो": "open", "बंद करो": "close app", "आवाज़ बढ़ाओ": "volume up",
            "आवाज़ कम करो": "volume down", "बैटरी": "battery", "समय": "time",
            "तारीख": "date", "मौसम": "weather", "चुटकुला": "joke",
            "संगीत चलाओ": "play music", "स्क्रीनशॉट": "screenshot",
            "गूगल पर खोजो": "search google", "क्या समय हुआ": "what time",
            "लॉक करो": "lock screen", "कैलकुलेट": "calculate",
            "मजाक सुनाओ": "tell me a joke", "तथ्य": "fun fact",
            "नोट लिखो": "take note", "मदद": "help",
            # Gujarati
            "ખોલો": "open", "બંધ": "close app", "અવાજ વધારો": "volume up",
            "અવાજ ઘટાડો": "volume down", "બેટરી": "battery", "સમય": "time",
            "હવામાન": "weather", "જોક": "joke", "સંગીત": "play music",
            "ગૂગલ": "search google", "મદદ": "help",
            # French
            "ouvrir": "open", "fermer": "close app", "volume haut": "volume up",
            "volume bas": "volume down", "batterie": "battery", "heure": "time",
            "météo": "weather", "blague": "joke", "musique": "play music",
            "capture d'écran": "screenshot", "aide": "help",
            # German
            "öffne": "open", "schließen": "close app", "lauter": "volume up",
            "leiser": "volume down", "batterie": "battery", "uhrzeit": "time",
            "wetter": "weather", "witz": "joke", "musik": "play music",
            "screenshot": "screenshot", "hilfe": "help",
            # Spanish
            "abrir": "open", "cerrar": "close app", "subir volumen": "volume up",
            "bajar volumen": "volume down", "batería": "battery", "hora": "time",
            "clima": "weather", "chiste": "joke", "música": "play music",
            "captura": "screenshot", "ayuda": "help",
        }

        for foreign, english in translations.items():
            if foreign in query:
                return query.replace(foreign, english)

        return query

    def start_voice_loop(self):
        """Start the continuous voice listening loop."""
        self.is_running = True
        self._emit("assistant_started", {"message": f"{Config.ASSISTANT_NAME} is ready!"})
        self.voice.speak(f"Hello! I'm {Config.ASSISTANT_NAME}, your voice assistant. How can I help you?")

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
                print(f"[Loop Error] {e}")
                continue

    def start(self):
        """Start the assistant in a background thread."""
        if self._thread and self._thread.is_alive():
            return {"status": "already_running"}

        self._thread = threading.Thread(target=self.start_voice_loop, daemon=True)
        self._thread.start()
        return {"status": "started", "name": Config.ASSISTANT_NAME}

    def stop(self):
        """Stop the assistant."""
        self.is_running = False
        self.voice.stop_wake_word()
        self._emit("assistant_stopped", {})
        return {"status": "stopped"}

    def get_status(self):
        """Get current assistant status."""
        return {
            "is_running": self.is_running,
            "is_listening": self.voice.is_listening,
            "is_speaking": self.voice.is_speaking,
            "silent_mode": self.silent_mode,
            "wake_word_mode": self.wake_word_mode,
            "name": Config.ASSISTANT_NAME,
        }

    def get_history(self):
        """Get command history."""
        return self.command_history[-50:]  # Last 50 commands

    def _go_silent(self, query):
        self.silent_mode = True
        self.voice.speak("Going silent. Say 'Hey Nova' to wake me up.")
        return "Silent mode activated."

    def _wake_up(self, query):
        self.silent_mode = False
        self.voice.speak("I'm back! How can I help you?")
        return "I'm awake and ready!"

    def _stop(self, query):
        self.voice.speak("Goodbye! Have a great day!")
        self.is_running = False
        return "Shutting down..."

    def _add_to_history(self, query, result, timestamp):
        self.command_history.append({
            "query": query,
            "response": result.get("response", ""),
            "type": result.get("type", ""),
            "timestamp": timestamp,
        })
        self._emit("history_update", self.command_history[-1])

    def _emit(self, event, data):
        if self.socketio:
            try:
                self.socketio.emit(event, data)
            except Exception:
                pass
