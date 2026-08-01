import yaml, sys
sys.path.insert(0, 'backend')
from config import Settings

SECTIONS = [
    ("1. CRITICAL REQUIRED", ["GEMINI_API_KEY", "SECRET_KEY", "CORS_ORIGINS"]),
    ("2. SERVER", ["ENVIRONMENT", "DEBUG", "HOST", "PORT", "PYTHONUNBUFFERED", "PYTHONPATH"]),
    ("3. IDENTITY", ["ASSISTANT_NAME", "WAKE_WORD"]),
    ("4. AI / GEMINI", ["GEMINI_MODEL", "GEMINI_MAX_TOKENS"]),
    ("5. VOICE ENGINE", ["VOICE_RATE", "VOICE_GENDER", "LISTEN_TIMEOUT", "PHRASE_TIME_LIMIT", "LANGUAGE"]),
    ("6. PATHS", ["DATA_DIR", "NOTES_DIR", "SCREENSHOTS_DIR", "OUTPUT_DIR", "MEMORY_FILE"]),
    ("7. USER ENVIRONMENT PATHS", ["USER_HOME", "PROJECTS_DIR", "DOWNLOADS_DIR", "DOCUMENTS_DIR"]),
    ("8. APP PATHS", ["APP_PATHS"]),
    ("9. WEBSITE SHORTCUTS", ["WEBSITE_SHORTCUTS"]),
]

# 1. Count pydantic Settings fields
settings_fields = set(Settings.model_fields.keys())
settings_fields.add("PYTHONUNBUFFERED")
settings_fields.add("PYTHONPATH")
settings_fields_actual = set()
for f in Settings.model_fields.keys():
    if f == "CORS_ORIGINS_RAW":
        settings_fields_actual.add("CORS_ORIGINS")
    else:
        settings_fields_actual.add(f)
settings_fields_actual.add("PYTHONUNBUFFERED")
settings_fields_actual.add("PYTHONPATH")

print("=" * 70)
print(f"SETTINGS CLASS: {len(settings_fields_actual)} total settable env keys")
print("=" * 70)

# 2. Check render.yaml
with open("render.yaml", encoding="utf-8") as f:
    yaml_data = yaml.safe_load(f)
yaml_keys = sorted([v["key"] for v in yaml_data["services"][0]["envVars"]])
yaml_keys_set = set(yaml_keys)

print()
print(f"RENDER.YAML: {len(yaml_keys)} env var entries")
print("  Missing from Settings?", sorted(settings_fields_actual - yaml_keys_set - {"PYTHONPATH"}))
print("  Extra (in yaml beyond Settings)?", sorted(yaml_keys_set - settings_fields_actual))

# 3. Check backend/.env.example
env_keys = set()
with open("backend/.env.example", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = __import__("re").match(r"^([A-Z_][A-Z0-9_]*)=", line)
        if m:
            env_keys.add(m.group(1))

print()
print(f"BACKEND .env.example: {len(env_keys)} env keys")
print("  Missing from Settings?", sorted(settings_fields_actual - env_keys))
print("  Extra in .env.example beyond Settings?", sorted(env_keys - settings_fields_actual))

# 4. Check root .env.example
root_keys = set()
with open(".env.example", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = __import__("re").match(r"^([A-Z_][A-Z0-9_]*)=", line)
        if m:
            root_keys.add(m.group(1))

frontend_keys = set()
with open("frontend/.env.example", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = __import__("re").match(r"^(VITE_[A-Z_][A-Z0-9_]*)=", line)
        if m:
            frontend_keys.add(m.group(1))

print()
print(f"ROOT .env.example keys: {len(root_keys)}")
print(f"  Backend portion: {len(root_keys - frontend_keys)}")
print(f"  Frontend portion: {len(frontend_keys)}")

# Cross-file comparison
print()
print("=" * 70)
print("CROSS-FILE COMPARISON (same 9 sections everywhere?):")
print("=" * 70)
expected_backend = set()
for _, keys in SECTIONS:
    expected_backend.update(keys)
yaml_ok = expected_backend - {"PYTHONPATH"} <= yaml_keys_set
env_ok = expected_backend <= env_keys
root_ok = expected_backend <= root_keys
print(f"  render.yaml has all backend keys:        {'✅ YES' if yaml_ok else '❌ NO'}")
print(f"  backend/.env.example has all keys:      {'✅ YES' if env_ok else '❌ NO'}")
print(f"  root .env.example has all backend keys: {'✅ YES' if root_ok else '❌ NO'}")
print(f"  frontend/.env.example has all VITE_:    {'✅ YES' if len(frontend_keys) == 6 else '❌ NO'}")
