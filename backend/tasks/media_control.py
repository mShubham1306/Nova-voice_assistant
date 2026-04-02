"""
NOVA Task Module - Media Control
Handles media playback controls using keyboard simulation.
"""

import pyautogui


class MediaControl:
    """Media playback controls for NOVA."""

    def __init__(self, voice):
        self.voice = voice

    def play_pause(self):
        """Toggle play/pause for media."""
        pyautogui.press("playpause")
        self.voice.speak("Toggled play/pause.")
        return "Toggled play/pause."

    def next_track(self):
        """Skip to next track."""
        pyautogui.press("nexttrack")
        self.voice.speak("Playing next track.")
        return "Skipped to next track."

    def previous_track(self):
        """Go to previous track."""
        pyautogui.press("prevtrack")
        self.voice.speak("Playing previous track.")
        return "Playing previous track."

    def stop(self):
        """Stop media playback."""
        pyautogui.press("stop")
        self.voice.speak("Media stopped.")
        return "Media playback stopped."
