import requests
import sys

API_BASE = "https://api-r2b-moksh.azurewebsites.net"
FE_BASE = "https://icy-pond-06feb7300.4.azurestaticapps.net"

print(f"--- 1. Testing Frontend SWA ({FE_BASE}) ---")
try:
    r = requests.get(FE_BASE, timeout=10)
    print(f"Frontend status: {r.status_code}")
except Exception as e:
    print(f"Frontend error: {e}")

print(f"\n--- 2. Testing Backend Health ({API_BASE}/health) ---")
try:
    r = requests.get(f"{API_BASE}/health", timeout=15)
    print(f"Health status: {r.status_code}")
    print(f"Health body: {r.text}")
except Exception as e:
    print(f"Health error: {e}")

print(f"\n--- 3. Testing Backend CORS Options ({API_BASE}/papers/upload) ---")
try:
    headers = {
        "Origin": FE_BASE,
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "Content-Type",
    }
    r = requests.options(f"{API_BASE}/papers/upload", headers=headers, timeout=15)
    print(f"OPTIONS status: {r.status_code}")
    print(f"OPTIONS headers: {dict(r.headers)}")
except Exception as e:
    print(f"OPTIONS error: {e}")

print(f"\n--- 4. Testing Topic Discovery ({API_BASE}/discovery/search) ---")
try:
    r = requests.post(
        f"{API_BASE}/discovery/search",
        json={"query": "quantum computing", "max_results": 3},
        timeout=25,
    )
    print(f"Discovery status: {r.status_code}")
    print(f"Found {len(r.json()) if r.status_code == 200 else 0} papers")
except Exception as e:
    print(f"Discovery error: {e}")
