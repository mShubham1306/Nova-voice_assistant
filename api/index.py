"""
NOVA Voice Assistant — Vercel Serverless Entry Point
This is a lightweight Flask app for Vercel's serverless Python runtime.
No SocketIO, no TTS/voice (those run client-side via Web Speech API).
"""

import os
import sys
import datetime

from flask import Flask, jsonify, request
from flask_cors import CORS

# ── Make backend modules importable ───────────────────────────────────────────
backend_dir = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, os.path.abspath(backend_dir))

# ── App setup ─────────────────────────────────────────────────────────────────
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# ── Lazy-load the assistant (avoids Windows-only imports crashing at startup) ──
_assistant = None
_assistant_error = None

def get_assistant():
    global _assistant
    global _assistant_error
    if _assistant is None:
        try:
            from core.assistant import Assistant
            _assistant = Assistant(socketio=None)
            _assistant_error = None
        except Exception as e:
            import traceback
            _assistant_error = traceback.format_exc()
            print(f"[Serverless] Could not init assistant: {_assistant_error}")
    return _assistant


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "name": "Nova", "mode": "serverless"}), 200


@app.route("/api/status", methods=["GET"])
def status():
    assistant = get_assistant()
    if assistant:
        return jsonify(assistant.get_status())
    return jsonify({"is_running": False, "name": "Nova", "mode": "serverless"})


@app.route("/api/start", methods=["POST"])
def start():
    """On serverless, voice loop can't run — just return ok."""
    return jsonify({"status": "started", "name": "Nova", "note": "Voice runs in browser via Web Speech API"})


@app.route("/api/stop", methods=["POST"])
def stop():
    return jsonify({"status": "stopped"})


@app.route("/api/command", methods=["POST"])
def command():
    data = request.get_json() or {}
    query = data.get("query", "").strip()
    if not query:
        return jsonify({"error": "No command provided"}), 400

    assistant = get_assistant()
    if assistant:
        result = assistant.process_command(query, skip_speech=True)
        return jsonify(result)

    # Fallback: no assistant available
    err_str = globals().get('_assistant_error', 'Unknown Error')
    return jsonify({
        "response": f"Vercel Deployment Error: {str(err_str)[:400]}... My AI core is warming up — make sure GEMINI_API_KEY is set in Vercel env vars!",
        "type": "error"
    })


@app.route("/api/history", methods=["GET"])
def history():
    assistant = get_assistant()
    if assistant:
        return jsonify({"history": assistant.get_history()})
    return jsonify({"history": []})


@app.route("/api/features", methods=["GET"])
def features():
    return jsonify({
        "categories": [
            {
                "name": "AI Chat",
                "icon": "🤖",
                "color": "#8b5cf6",
                "commands": [
                    {"cmd": "Tell me about black holes", "desc": "Ask anything"},
                    {"cmd": "Explain quantum computing", "desc": "Deep explanations"},
                    {"cmd": "How to learn Python?", "desc": "Get advice"},
                    {"cmd": "Who are you?", "desc": "Meet Nova"},
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
                    {"cmd": "Open website...", "desc": "Visit any site"},
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
                    {"cmd": "Tell me a joke", "desc": "Random humor"},
                    {"cmd": "Fun fact", "desc": "Interesting facts"},
                    {"cmd": "Motivational quote", "desc": "Get inspired"},
                    {"cmd": "Flip a coin", "desc": "Heads or tails"},
                    {"cmd": "Roll a dice", "desc": "Random 1-6"},
                ]
            },
            {
                "name": "Utilities",
                "icon": "🛠️",
                "color": "#f59e0b",
                "commands": [
                    {"cmd": "Calculate 5 plus 3", "desc": "Math calculations"},
                    {"cmd": "Take note...", "desc": "Save a note"},
                ]
            },
        ],
        "total_commands": 20,
        "wake_word": "Hey Nova",
    })


@app.route("/api/languages", methods=["GET"])
def languages():
    langs = {
        "hi": "Hindi", "gu": "Gujarati", "bn": "Bengali", "ta": "Tamil",
        "te": "Telugu", "kn": "Kannada", "ml": "Malayalam", "mr": "Marathi",
        "pa": "Punjabi", "en": "English", "fr": "French", "de": "German",
        "es": "Spanish", "it": "Italian", "pt": "Portuguese", "ru": "Russian",
        "zh": "Chinese", "ja": "Japanese", "ko": "Korean", "ar": "Arabic",
    }
    return jsonify({
        "languages": langs,
        "total": len(langs),
        "description": "Nova understands 40+ languages. Speak or type — Nova auto-detects and replies in the same language."
    })


@app.route("/api/wake-word", methods=["POST"])
def wake_word():
    return jsonify({"wake_word_mode": False, "message": "Wake word runs client-side in the browser."})


# ── Vercel serverless handler ──────────────────────────────────────────────────
# Vercel automatically discovers `app` as the WSGI handler.
