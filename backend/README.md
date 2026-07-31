# 🚀 NOVA — AI Operating Assistant (Backend 2.0)

NOVA is a high-performance, tool-based AI Operating Assistant designed for Windows desktop automation, file intelligence, developer workflows, and natural language voice/text interaction.

---

## 🌟 Key Architectural Innovations

### 1. 3-Layer Intelligent Routing Pipeline
```
[ User Voice / Text Input ]
            │
            ▼
┌─────────────────────────────────────────┐
│ Layer 1: Fast Router (Regex <1ms)      │ ──► Simple commands (volume, lock, screenshot)
└────────────────────┬────────────────────┘     executed with zero API latency.
                     │ complex/ambiguous
                     ▼
┌─────────────────────────────────────────┐
│ Layer 2: Gemini Brain (Function Calls)  │ ──► Native Gemini Function Calling parses intent
└────────────────────┬────────────────────┘     and returns structured JSON: {tool, action, params}.
                     │
                     ▼
┌─────────────────────────────────────────┐
│ Layer 3: Tool Plugin Registry           │ ──► Executes typed action via modular plugin system.
└─────────────────────────────────────────┘
```

### 2. Extensible Plugin System (`BaseTool`)
Every feature is encapsulated as an independent plugin extending `BaseTool`. Tools self-describe their parameters and actions, generating Gemini-compatible JSON schemas on the fly.

To add a new tool (e.g. `docker_tool.py`), simply drop a file extending `BaseTool` into `backend/tools/` — NOVA auto-discovers and registers it on startup without touching core code!

---

## 🛠️ Registered Tools & Capabilities

| Tool | Actions | Capabilities |
|---|---|---|
| ⚙️ `system_tool` | 21 actions | Open/close apps, volume, brightness, lock screen, shutdown/restart, battery/CPU/RAM/disk stats, process killer |
| 📁 `file_tool` | 14 actions | Search files by query/extension, open in target apps, delete, rename, copy, move, organize folder by category, find duplicates, recent files |
| 🌐 `browser_tool` | 8 actions | Google search, YouTube, Wikipedia, StackOverflow, GitHub, custom URLs, localhost dev ports |
| 🎵 `media_tool` | 6 actions | Play/pause, next track, previous track, stop playback, search YouTube/Spotify |
| 🛠️ `utility_tool` | 8 actions | Screenshots, countdown timers, alarms, math expression calculator, clipboard R/W, typing simulation, unit converter |
| 📚 `info_tool` | 12 actions | Time, date, live weather, news headlines, dictionary definitions, Google translate, jokes, facts, motivational quotes, coin flip, dice roll |
| 📝 `notes_tool` | 6 actions | JSON-backed smart notes with tags, full-text search, date recall ("yesterday's notes"), list, delete |
| 💻 `dev_tool` | 12 actions | Single-command project startup (FastAPI/React/Django/Node), Git status/log/pull/push/branch/diff, run shell commands, open in VS Code, kill port |
| ⚡ `workflow_tool` | 8 actions | Multi-step automated workflows: interview prep, coding environment, morning routine, focus mode, presentation mode, folder cleanup, study session |

---

## ⚡ Quickstart

### 1. Requirements
- Python 3.10+
- Google Gemini API Key (free from [Google AI Studio](https://aistudio.google.com/))

### 2. Environment Setup
```bash
cp .env.example .env
```
Edit `.env` and add your `GEMINI_API_KEY`.

### 3. Run Server
```bash
python app.py
```
Or with Uvicorn:
```bash
uvicorn app:app --reload --port 5000
```
Interactive API documentation will be available at: `http://localhost:5000/docs`

---

## 🧪 Verification Tests

Run the test suite to verify tool discovery, fast routing, schema generation, and tool execution:
```bash
python tests/test_backend.py
```

---

## 🔌 API Endpoints Summary

- `POST /api/command` — Send text/voice query to 3-layer pipeline
- `POST /api/tool` — Direct tool execution (bypasses LLM)
- `GET /api/tools` — List registered tools and capabilities
- `GET /api/status` — Get NOVA operational status
- `GET /api/memory` — View session & persistent memory
- `DELETE /api/memory` — Reset memory
- `GET /api/features` — Categorized feature tree for UI
- `WS /ws` — Real-time WebSocket event connection
