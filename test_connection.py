#!/usr/bin/env python3
print("Testing connections...")
print("=" * 60)

# Test 1: Internet
import subprocess
result = subprocess.run(["ping", "-c", "1", "8.8.8.8"], capture_output=True)
print(f"Internet: {'✅ Working' if result.returncode == 0 else '❌ Failed'}")

# Test 2: OpenAI (if internet works)
if result.returncode == 0:
    import requests
    try:
        r = requests.get("https://api.openai.com/v1/models", timeout=5)
        print(f"OpenAI: ✅ Reachable (status: {r.status_code})")
    except Exception as e:
        print(f"OpenAI: ❌ Error: {e}")

# Test 3: Ollama
try:
    import requests
    r = requests.get("http://localhost:11434/api/tags", timeout=2)
    print(f"Ollama: ✅ Running")
except Exception:
    print("Ollama: ❌ Not running (start with: ollama serve)")
print("=" * 60)
