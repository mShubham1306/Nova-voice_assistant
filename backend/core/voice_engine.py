"""
NOVA Voice Engine - Speech Recognition & Text-to-Speech
Handles all voice I/O including wake word detection.
Optimized for fast, non-blocking TTS.
Gracefully handles missing PyAudio (voice input disabled, TTS + text commands still work).
"""

import threading
import time
import queue
from config import Config

# Try to import speech recognition (needs PyAudio for microphone)
try:
    import speech_recognition as sr
    _SR_AVAILABLE = True
except ImportError:
    _SR_AVAILABLE = False
    print("[Voice] speech_recognition not available. Voice input disabled.")

# Try to import TTS engine
try:
    import pyttsx3
    _TTS_AVAILABLE = True
except ImportError:
    _TTS_AVAILABLE = False
    print("[Voice] pyttsx3 not available. Text-to-speech disabled.")


class VoiceEngine:
    """Manages speech recognition and text-to-speech for NOVA.
    Works in degraded mode if PyAudio/pyttsx3 are missing.
    """

    def __init__(self, socketio=None):
        self.socketio = socketio
        self.is_listening = False
        self.is_speaking = False
        self.wake_word_active = False
        self.muted = False  # When True, speak() is a no-op (for text commands)
        self.mic_available = False

        # Init speech recognizer if available
        if _SR_AVAILABLE:
            try:
                self.recognizer = sr.Recognizer()
                self.recognizer.dynamic_energy_threshold = True
                self.recognizer.energy_threshold = 300
                self.recognizer.pause_threshold = 0.6
                # Test if microphone is accessible
                sr.Microphone()
                self.mic_available = True
                print("[Voice] Microphone ready.")
            except Exception as e:
                self.recognizer = None
                self.mic_available = False
                print(f"[Voice] Microphone not available: {e}")
                print("[Voice] Text commands will still work. Voice input disabled.")
        else:
            self.recognizer = None

        # TTS runs in its own dedicated thread to never block
        self._tts_queue = queue.Queue()
        if _TTS_AVAILABLE:
            self._tts_thread = threading.Thread(target=self._tts_worker, daemon=True)
            self._tts_thread.start()

    def _tts_worker(self):
        """Dedicated TTS worker thread — processes speech queue."""
        try:
            from comtypes import CoInitialize
            CoInitialize()
        except Exception:
            pass

        try:
            engine = pyttsx3.init()
            voices = engine.getProperty('voices')
            if Config.VOICE_GENDER == "female" and len(voices) > 1:
                engine.setProperty('voice', voices[1].id)
            else:
                engine.setProperty('voice', voices[0].id)
            engine.setProperty('rate', Config.VOICE_RATE)
            print("[Voice] TTS engine ready.")
        except Exception as e:
            print(f"[TTS] Failed to init engine: {e}")
            return

        while True:
            try:
                text = self._tts_queue.get()
                if text is None:
                    break
                self.is_speaking = True
                self._emit("nova_speaking", {"text": text})
                engine.say(text)
                engine.runAndWait()
                self.is_speaking = False
                self._emit("nova_idle", {})
                self._tts_queue.task_done()
            except Exception as e:
                print(f"[TTS Error] {e}")
                self.is_speaking = False
                try:
                    self._tts_queue.task_done()
                except ValueError:
                    pass

    def speak(self, text):
        """Queue text for speech (non-blocking). Returns immediately.
        If muted or TTS unavailable, skips entirely."""
        if not text or self.muted or not _TTS_AVAILABLE:
            return
        self._tts_queue.put(text)

    def listen(self, timeout=None, phrase_limit=None):
        """Listen for voice input and return recognized text."""
        if not self.mic_available or not self.recognizer:
            return None

        timeout = timeout or Config.LISTEN_TIMEOUT
        phrase_limit = phrase_limit or Config.PHRASE_TIME_LIMIT

        self.is_listening = True
        self._emit("nova_listening", {})

        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.3)
                audio = self.recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_limit
                )

            self._emit("nova_processing", {})
            text = self.recognizer.recognize_google(audio, language=Config.LANGUAGE)
            print(f"[Heard] {text}")
            return text.lower().strip()

        except sr.WaitTimeoutError:
            return None
        except sr.UnknownValueError:
            return None
        except sr.RequestError as e:
            print(f"[Speech API Error] {e}")
            return None
        except Exception as e:
            print(f"[Listen Error] {e}")
            return None
        finally:
            self.is_listening = False

    def listen_for_wake_word(self):
        """Continuously listen for the wake word 'Hey Nova'."""
        if not self.mic_available or not self.recognizer:
            print("[Voice] Cannot listen for wake word — no microphone.")
            return False

        self.wake_word_active = True
        self._emit("nova_standby", {"message": "Waiting for 'Hey Nova'..."})

        while self.wake_word_active:
            try:
                with sr.Microphone() as source:
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.2)
                    audio = self.recognizer.listen(source, timeout=3, phrase_time_limit=3)

                text = self.recognizer.recognize_google(audio, language=Config.LANGUAGE)
                if text and Config.WAKE_WORD in text.lower():
                    self._emit("nova_activated", {"message": "Hey! How can I help?"})
                    self.speak("Hey! How can I help you?")
                    return True

            except (sr.WaitTimeoutError, sr.UnknownValueError):
                continue
            except sr.RequestError:
                time.sleep(1)
                continue
            except Exception:
                continue

        return False

    def stop_wake_word(self):
        """Stop wake word listening."""
        self.wake_word_active = False

    def _emit(self, event, data):
        """Emit event to frontend via SocketIO."""
        if self.socketio:
            try:
                self.socketio.emit(event, data)
            except Exception:
                pass


