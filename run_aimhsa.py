#!/usr/bin/env python3
"""
AIMHSA Production Launcher (single origin)
Runs the Flask app from app.py - API and static frontend on one origin.
Use this file to start the server; do not use a duplicate app.
"""

import os
from dotenv import load_dotenv

# Load .env from project root so OLLAMA_API_KEY is set before app is imported
_env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
load_dotenv(dotenv_path=_env_path, override=True)

# Default to production environment for hosted deployments
os.environ.setdefault('FLASK_ENV', 'production')

from app import app
from config import current_config

if __name__ == "__main__":
    host = os.environ.get('HOST', getattr(current_config, 'HOST', '0.0.0.0'))
    port = int(os.environ.get('PORT', getattr(current_config, 'PORT', 7860)))

    print("Starting AIMHSA on %s:%s (production mode)" % (host, port))
    print("Base URL: http://%s:%s" % (host, port))
    # Confirm .env and AI are ready
    key_set = bool((os.environ.get("OLLAMA_API_KEY") or "").strip())
    print("OLLAMA_API_KEY loaded: %s" % ("yes" if key_set else "NO - add it to .env for AI responses"))
    print("Check http://%s:%s/api/ai-status for API status" % (host, port))

    app.run(
        host=host,
        port=port,
        debug=False,
        threaded=True
    )
