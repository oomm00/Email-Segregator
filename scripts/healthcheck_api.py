"""Healthcheck script for API container. Exits 0 if healthy, 1 otherwise."""
import sys
import urllib.request

try:
    resp = urllib.request.urlopen("http://localhost:8000/health", timeout=5)
    assert resp.status == 200
    sys.exit(0)
except Exception:
    sys.exit(1)
