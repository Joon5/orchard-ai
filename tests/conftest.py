"""pytest configuration — adds src/ to sys.path so test imports resolve."""
import sys
import os

# Add src/ to path: resolves "from api.main import app" → src/api/main.py
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

# Set required env vars before any module is imported
os.environ.setdefault("ORCHARD_AGENT_SECRET", "test-secret")
