"""
NOVA API Routes - REST endpoints and WebSocket events
"""

from flask import Blueprint, jsonify, request

api_bp = Blueprint("api", __name__, url_prefix="/api")

# Will be set by app.py
_assistant = None


def init_assistant(assistant):
    """Initialize the shared assistant instance."""
    global _assistant
    _assistant = assistant


@api_bp.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint for deployment monitoring."""
    return jsonify({"status": "healthy", "service": "NOVA Voice Assistant"}), 200


@api_bp.route("/status", methods=["GET"])
def get_status():
    """Get assistant status."""
    if _assistant:
        return jsonify(_assistant.get_status())
    return jsonify({"is_running": False, "name": "Nova"})


@api_bp.route("/start", methods=["POST"])
def start_assistant():
    """Start voice assistant."""
    if _assistant:
        result = _assistant.start()
        return jsonify(result)
    return jsonify({"error": "Assistant not initialized"}), 500


@api_bp.route("/stop", methods=["POST"])
def stop_assistant():
    """Stop voice assistant."""
    if _assistant:
        result = _assistant.stop()
        return jsonify(result)
    return jsonify({"error": "Assistant not initialized"}), 500


@api_bp.route("/command", methods=["POST"])
def send_command():
    """Send a text command to the assistant.
    Text commands skip TTS for instant response.
    """
    data = request.get_json()
    query = data.get("query", "") if data else ""

    if not query:
        return jsonify({"error": "No command provided"}), 400

    if _assistant:
        result = _assistant.process_command(query, skip_speech=True)
        return jsonify(result)

    return jsonify({"error": "Assistant not initialized"}), 500


@api_bp.route("/history", methods=["GET"])
def get_history():
    """Get command history."""
    if _assistant:
        return jsonify({"history": _assistant.get_history()})
    return jsonify({"history": []})


@api_bp.route("/features", methods=["GET"])
def get_features():
    """Get list of all supported features/commands."""
    features = {
        "categories": [
            {
                "name": "System Control",
                "icon": "⚙️",
                "color": "#6366f1",
                "commands": [
                    {"cmd": "Open Chrome", "desc": "Launch applications"},
                    {"cmd": "Close Notepad", "desc": "Close running apps"},
                    {"cmd": "Volume up/down", "desc": "Control volume"},
                    {"cmd": "Brightness up/down", "desc": "Adjust brightness"},
                    {"cmd": "Battery status", "desc": "Check battery level"},
                    {"cmd": "Lock screen", "desc": "Lock your PC"},
                    {"cmd": "System info", "desc": "Get PC info"},
                    {"cmd": "CPU/RAM/Disk usage", "desc": "System diagnostics"},
                    {"cmd": "IP address", "desc": "Get your IP"},
                    {"cmd": "Wi-Fi status", "desc": "Check internet"},
                    {"cmd": "Shutdown/Restart", "desc": "Power controls"},
                    {"cmd": "Empty recycle bin", "desc": "Clean up storage"},
                ]
            },
            {
                "name": "Web & Search",
                "icon": "🌐",
                "color": "#06b6d4",
                "commands": [
                    {"cmd": "Search Google for...", "desc": "Google search"},
                    {"cmd": "Search YouTube for...", "desc": "YouTube search"},
                    {"cmd": "Wikipedia...", "desc": "Look up Wikipedia"},
                    {"cmd": "Stack Overflow...", "desc": "Find code answers"},
                    {"cmd": "Open website...", "desc": "Visit any site"},
                ]
            },
            {
                "name": "Media Control",
                "icon": "🎵",
                "color": "#8b5cf6",
                "commands": [
                    {"cmd": "Play/Pause music", "desc": "Toggle playback"},
                    {"cmd": "Next/Previous song", "desc": "Switch tracks"},
                ]
            },
            {
                "name": "Utilities",
                "icon": "🛠️",
                "color": "#f59e0b",
                "commands": [
                    {"cmd": "Take screenshot", "desc": "Capture screen"},
                    {"cmd": "Set timer for 5 minutes", "desc": "Countdown timer"},
                    {"cmd": "Set alarm", "desc": "Wake-up alarm"},
                    {"cmd": "Calculate 5 plus 3", "desc": "Math calculations"},
                    {"cmd": "Take note...", "desc": "Save a note"},
                    {"cmd": "Read notes", "desc": "View saved notes"},
                    {"cmd": "Clipboard", "desc": "Read clipboard"},
                    {"cmd": "Type...", "desc": "Auto-type text"},
                ]
            },
            {
                "name": "Information",
                "icon": "📚",
                "color": "#10b981",
                "commands": [
                    {"cmd": "What time is it?", "desc": "Current time"},
                    {"cmd": "What's the date?", "desc": "Today's date"},
                    {"cmd": "Weather in London", "desc": "Weather updates"},
                    {"cmd": "News", "desc": "Top headlines"},
                    {"cmd": "Tell me a joke", "desc": "Random humor"},
                    {"cmd": "Fun fact", "desc": "Interesting facts"},
                    {"cmd": "Define serendipity", "desc": "Word definitions"},
                    {"cmd": "Translate hello", "desc": "Google Translate"},
                    {"cmd": "Motivational quote", "desc": "Get inspired"},
                    {"cmd": "Flip a coin", "desc": "Heads or tails"},
                    {"cmd": "Roll a dice", "desc": "Random 1-6"},
                ]
            },
            {
                "name": "AI Chat",
                "icon": "🤖",
                "color": "#ec4899",
                "commands": [
                    {"cmd": "Tell me about black holes", "desc": "Ask anything"},
                    {"cmd": "Explain quantum computing", "desc": "Deep explanations"},
                    {"cmd": "How to learn Python?", "desc": "Get advice"},
                    {"cmd": "Who are you?", "desc": "Meet Nova"},
                ]
            },
        ],
        "total_commands": 45,
        "wake_word": "Hey Nova",
    }
    return jsonify(features)


@api_bp.route("/wake-word", methods=["POST"])
def toggle_wake_word():
    """Toggle wake word mode."""
    if _assistant:
        _assistant.wake_word_mode = not _assistant.wake_word_mode
        return jsonify({
            "wake_word_mode": _assistant.wake_word_mode,
            "message": f"Wake word mode {'enabled' if _assistant.wake_word_mode else 'disabled'}."
        })
    return jsonify({"error": "Assistant not initialized"}), 500


@api_bp.route("/languages", methods=["GET"])
def get_languages():
    """Get list of all supported languages."""
    from tasks.ai_chat import SUPPORTED_LANGUAGES
    return jsonify({
        "languages": SUPPORTED_LANGUAGES,
        "total": len(SUPPORTED_LANGUAGES),
        "description": "Nova understands and responds in 40+ Indian and global languages. Simply speak or type in your preferred language — Nova auto-detects and replies in the same language."
    })

