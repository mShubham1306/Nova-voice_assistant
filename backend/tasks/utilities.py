"""
NOVA Task Module - Utilities
Screenshot, timer, alarm, calculator, notes, clipboard, typing.
"""

import os
import datetime
import threading
import time
try:
    import pyautogui
except ImportError:
    pyautogui = None
from config import Config


class Utilities:
    """Utility operations for NOVA."""

    def __init__(self, voice):
        self.voice = voice
        os.makedirs(Config.OUTPUT_DIR, exist_ok=True)
        os.makedirs(Config.NOTES_DIR, exist_ok=True)

    def take_screenshot(self):
        """Capture a screenshot and save it."""
        if pyautogui is None:
            self.voice.speak("Screenshots are not available on this server.")
            return "Screenshot unavailable."
        
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filepath = os.path.join(Config.OUTPUT_DIR, f"screenshot_{timestamp}.png")
        screenshot = pyautogui.screenshot()
        screenshot.save(filepath)
        self.voice.speak("Screenshot captured and saved.")
        return f"Screenshot saved: {filepath}"

    def set_timer(self, query):
        """Set a countdown timer."""
        minutes = self._extract_number(query)
        if minutes:
            self.voice.speak(f"Timer set for {minutes} minutes.")

            def timer_callback():
                time.sleep(minutes * 60)
                self.voice.speak(f"Timer is up! {minutes} minutes have passed.")

            t = threading.Thread(target=timer_callback, daemon=True)
            t.start()
            return f"Timer set for {minutes} minutes."

        self.voice.speak("How many minutes should I set the timer for?")
        return "Please specify the duration."

    def set_alarm(self, query):
        """Set an alarm (simplified - timer-based)."""
        minutes = self._extract_number(query)
        if minutes:
            self.voice.speak(f"Alarm set for {minutes} minutes from now.")

            def alarm_callback():
                time.sleep(minutes * 60)
                for _ in range(3):
                    self.voice.speak("Wake up! Your alarm is ringing!")
                    time.sleep(2)

            t = threading.Thread(target=alarm_callback, daemon=True)
            t.start()
            return f"Alarm set for {minutes} minutes from now."

        return "Please specify the time for the alarm."

    def calculate(self, query):
        """Evaluate a math expression."""
        # Extract math expression
        expression = query.lower()
        for prefix in ["calculate", "what is", "math", "solve", "compute"]:
            expression = expression.replace(prefix, "")
        expression = expression.strip()

        # Replace words with operators
        expression = expression.replace("plus", "+").replace("minus", "-")
        expression = expression.replace("times", "*").replace("multiplied by", "*")
        expression = expression.replace("divided by", "/").replace("over", "/")
        expression = expression.replace("power", "**").replace("to the power of", "**")
        expression = expression.replace("mod", "%").replace("modulo", "%")
        expression = expression.replace("x", "*")

        try:
            # Safe eval - only allow math
            allowed_chars = set("0123456789+-*/.()% ")
            if all(c in allowed_chars for c in expression):
                result = eval(expression)
                msg = f"The answer is {result}."
                self.voice.speak(msg)
                return msg
            else:
                return "I can only evaluate mathematical expressions."
        except Exception:
            self.voice.speak("I couldn't calculate that. Please try again.")
            return "Calculation error."

    def take_note(self, query):
        """Save a text note."""
        note = query.lower()
        for prefix in ["take note", "save note", "write note", "note down", "note"]:
            note = note.replace(prefix, "")
        note = note.strip()

        if note:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            filepath = os.path.join(Config.NOTES_DIR, "notes.txt")
            with open(filepath, "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] {note}\n")
            self.voice.speak("Note saved.")
            return f"Note saved: {note}"

        return "What would you like me to note down?"

    def read_notes(self):
        """Read saved notes."""
        filepath = os.path.join(Config.NOTES_DIR, "notes.txt")
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                notes = f.readlines()
            if notes:
                recent = notes[-5:]  # Last 5 notes
                note_text = " ".join([n.strip() for n in recent])
                self.voice.speak(f"Your recent notes: {note_text}")
                return "Recent notes:\n" + "".join(recent)
        self.voice.speak("You don't have any notes yet.")
        return "No notes found."

    def clipboard_content(self):
        """Read clipboard content."""
        try:
            import subprocess
            result = subprocess.run(
                ["powershell", "Get-Clipboard"],
                capture_output=True, text=True, shell=True
            )
            content = result.stdout.strip()
            if content:
                self.voice.speak(f"Your clipboard contains: {content[:100]}")
                return f"Clipboard: {content[:200]}"
            else:
                self.voice.speak("Clipboard is empty.")
                return "Clipboard is empty."
        except Exception:
            return "Could not read clipboard."

    def type_text(self, query):
        """Type text using keyboard simulation."""
        if pyautogui is None:
            self.voice.speak("Typing simulation is not available on this server.")
            return "Typing simulation unavailable."

        text = query.lower()
        for prefix in ["type", "type out", "write"]:
            text = text.replace(prefix, "")
        text = text.strip()

        if text:
            time.sleep(1)  # Give user time to focus the target window
            pyautogui.typewrite(text, interval=0.05)
            self.voice.speak("Done typing.")
            return f"Typed: {text}"

        return "What would you like me to type?"

    def _extract_number(self, text):
        """Extract a number from text."""
        import re
        word_to_num = {
            "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
            "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
            "fifteen": 15, "twenty": 20, "thirty": 30, "forty": 40,
            "forty five": 45, "sixty": 60, "half": 30,
        }

        text_lower = text.lower()
        for word, num in word_to_num.items():
            if word in text_lower:
                return num

        numbers = re.findall(r'\d+', text)
        if numbers:
            return int(numbers[0])

        return None
