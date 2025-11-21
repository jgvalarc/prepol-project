"""
WSGI entry point for Render deployment
"""
import sys
from pathlib import Path

# Ensure project root is in path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from api.server import app

if __name__ == "__main__":
    app.run()
