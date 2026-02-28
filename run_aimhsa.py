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
    # Confirm .env and AI are ready (safe diagnostic: no key value logged)
    raw_key = (os.environ.get("OLLAMA_API_KEY") or os.environ.get("OPENROUTER_API_KEY") or "")
    key_stripped = raw_key.strip()
    key_set = bool(key_stripped)
    print("OLLAMA_API_KEY loaded: %s" % ("yes" if key_set else "NO - add it to .env for AI responses"))
    if key_set:
        print("API key length: %d (raw had newline/space: %s)" % (
            len(key_stripped),
            "yes" if raw_key != key_stripped or "\n" in raw_key or "\r" in raw_key else "no"
        ))
        # Test OpenRouter from this environment (same key works locally vs 401 on Space = env/network)
        try:
            import requests
            base_url = (os.environ.get("OLLAMA_BASE_URL") or "https://openrouter.ai/api/v1").strip().rstrip("/")
            r = requests.get(
                base_url + "/models",
                headers={"Authorization": "Bearer %s" % key_stripped},
                timeout=10,
            )
            if r.status_code == 401:
                print("OpenRouter test: 401 (key rejected from THIS environment - fix secret or check OpenRouter IP restrictions)")
            elif r.status_code == 200:
                print("OpenRouter test: OK (key works from this environment)")
            else:
                print("OpenRouter test: HTTP %s" % r.status_code)
        except Exception as e:
            print("OpenRouter test: error - %s" % (e,))
    print("Check http://%s:%s/api/ai-status for API status" % (host, port))

    app.run(
        host=host,
        port=port,
        debug=False,
        threaded=True
    )
