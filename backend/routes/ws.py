"""
NOVA WebSocket Route — Real-time event communication
Handles WebSocket connections from web frontend for voice commands, audio status, and events.
"""

from __future__ import annotations

import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Any

logger = logging.getLogger("nova.ws")

ws_router = APIRouter(tags=["websocket"])

# Active connections manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info("[WS] Client connected. Total active: %d", len(self.active_connections))

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info("[WS] Client disconnected. Remaining: %d", len(self.active_connections))

    async def broadcast(self, event: str, data: Any):
        payload = json.dumps({"event": event, "data": data})
        for connection in list(self.active_connections):
            try:
                await connection.send_text(payload)
            except Exception as e:
                logger.warning("[WS] Broadcast failed for client: %s", e)

manager = ConnectionManager()

# Injected assistant reference
_assistant = None

def init_ws_assistant(assistant):
    global _assistant
    _assistant = assistant
    # Hook assistant emit to ws broadcast
    old_emit = assistant._emit
    def ws_emit(event, data):
        try:
            import asyncio
            old_emit(event, data)
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(manager.broadcast(event, data))
        except Exception:
            pass
    assistant._emit = ws_emit


@ws_router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Send initial connected handshake
        await websocket.send_json({
            "event": "connected",
            "data": {
                "name": "Nova",
                "status": "ready",
                "brain_available": _assistant.brain.is_available if _assistant else False
            }
        })

        while True:
            data_text = await websocket.receive_text()
            try:
                msg = json.loads(data_text)
                event = msg.get("event")
                payload = msg.get("data", {})

                if event == "voice_command":
                    query = payload.get("query", "")
                    if query and _assistant:
                        result = _assistant.process_command(query, skip_speech=payload.get("skip_speech", False))
                        await websocket.send_json({"event": "command_result", "data": result})

                elif event == "start_listening":
                    if _assistant:
                        _assistant.start()

                elif event == "stop_listening":
                    if _assistant:
                        _assistant.stop()

                elif event == "ping":
                    await websocket.send_json({"event": "pong", "data": {}})

            except json.JSONDecodeError:
                logger.warning("[WS] Received non-JSON payload: %s", data_text)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error("[WS] Connection error: %s", e)
        manager.disconnect(websocket)
