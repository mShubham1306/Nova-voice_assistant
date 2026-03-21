"""
NOVA Voice Assistant - Flask Application Entry Point
"""

from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO
from config import Config
from core.assistant import Assistant
from routes.api import api_bp, init_assistant
import os

# Create Flask app
app = Flask(__name__)
app.config["SECRET_KEY"] = Config.SECRET_KEY

# Enable CORS for React frontend
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Initialize SocketIO for real-time events
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# Create output directories
os.makedirs(Config.OUTPUT_DIR, exist_ok=True)
os.makedirs(Config.NOTES_DIR, exist_ok=True)

# Initialize assistant with socketio
assistant = Assistant(socketio=socketio)
init_assistant(assistant)

# Register blueprints
app.register_blueprint(api_bp)


# SocketIO event handlers
@socketio.on("connect")
def handle_connect():
    print("[WS] Client connected")
    socketio.emit("connected", {"name": Config.ASSISTANT_NAME, "status": "ready"})


@socketio.on("disconnect")
def handle_disconnect():
    print("[WS] Client disconnected")


@socketio.on("voice_command")
def handle_voice_command(data):
    """Handle voice command from frontend."""
    query = data.get("query", "")
    if query:
        result = assistant.process_command(query)
        socketio.emit("command_result", result)


@socketio.on("start_listening")
def handle_start_listening():
    """Start voice listening from frontend trigger."""
    assistant.start()


@socketio.on("stop_listening")
def handle_stop_listening():
    """Stop voice listening."""
    assistant.stop()


# Health check
@app.route("/health")
def health():
    return {"status": "healthy", "name": Config.ASSISTANT_NAME}


if __name__ == "__main__":
    print(f"""
    ╔══════════════════════════════════════╗
    ║     🚀 NOVA Voice Assistant 🚀      ║
    ║     Running on port {Config.PORT}            ║
    ╚══════════════════════════════════════╝
    """)
    socketio.run(app, host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)
