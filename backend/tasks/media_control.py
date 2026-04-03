"""
NOVA Task Module - Media Control
Handles media playback controls using keyboard simulation.
"""

try:
    import pyautogui
except ImportError:
    pyautogui = None


class MediaControl:
    """Media playback controls for NOVA."""

    def __init__(self, voice):
        self.voice = voice

    def play_pause(self):
        """Toggle play/pause for media."""
        if pyautogui is None:
            return "Media controls unavailable."
        pyautogui.press("playpause")
        self.voice.speak("Toggled play/pause.")
        return "Toggled play/pause."

    def next_track(self):
        """Skip to next track."""
        if pyautogui is None:
            return "Media controls unavailable."
        pyautogui.press("nexttrack")
        self.voice.speak("Playing next track.")
        return "Skipped to next track."

    def previous_track(self):
        """Go to previous track."""
        if pyautogui is None:
            return "Media controls unavailable."
        pyautogui.press("prevtrack")
        self.voice.speak("Playing previous track.")
        return "Playing previous track."

    def stop(self):
        """Stop media playback."""
        if pyautogui is None:
            return "Media controls unavailable."
        pyautogui.press("stop")
        self.voice.speak("Media stopped.")
        return "Media playback stopped."
