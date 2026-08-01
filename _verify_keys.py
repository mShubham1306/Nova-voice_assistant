import yaml, json, re

with open("render.yaml", encoding="utf-8") as f:
    data = yaml.safe_load(f)
svc = data["services"][0]
vars = svc["envVars"]
render_keys = sorted([v["key"] for v in vars])

backend_keys = set()
with open("backend/.env.example", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r"^([A-Z_][A-Z0-9_]*)=", line)
        if m:
            backend_keys.add(m.group(1))

frontend_keys = set()
with open("frontend/.env.example", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r"^(VITE_[A-Z_][A-Z0-9_]*)=", line)
        if m:
            frontend_keys.add(m.group(1))

print("=" * 70)
print(f"RENDER.YAML  env vars: {len(render_keys)} total")
print("=" * 70)
for k in render_keys:
    v = next((x for x in vars if x["key"] == k), {})
    val = v.get("value", "(user-set: sync=false)" if v.get("sync") == False else "(auto-generate)" if v.get("generateValue") else "")
    print(f"  ✅ {k} = {val}")

print()
print("=" * 70)
print(f"BACKEND .env.example keys: {len(backend_keys)}")
print("=" * 70)
for k in sorted(backend_keys):
    marker = "  ✅" if k in render_keys or k == "PYTHONPATH" else "  ❌ MISSING FROM render.yaml"
    print(f"{marker} {k}")

print()
print("=" * 70)
print(f"FRONTEND .env.example keys: {len(frontend_keys)}")
print("=" * 70)
for k in sorted(frontend_keys):
    print(f"  ✅ {k}")

missing = backend_keys - set(render_keys) - {"PYTHONPATH"}
if missing:
    print()
    print("❌ KEYS IN .env.example BUT MISSING FROM render.yaml:", sorted(missing))
else:
    print()
    print("✅ ALL keys match! No missing keys in render.yaml")
