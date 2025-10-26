#!/usr/bin/env python3
"""
AIMHSA Production Launcher
Optimized for hosting platforms like Heroku, Railway, etc.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set production environment
os.environ['FLASK_ENV'] = 'production'

# Import and run the app
from app import app
from config import current_config

if __name__ == "__main__":
    # Get port from environment (for hosting platforms)
    port = int(os.environ.get('PORT', current_config.PORT))
    host = os.environ.get('HOST', current_config.HOST)
    
    print(f"🚀 Starting AIMHSA in production mode on {host}:{port}")
    
    # Run with production settings
    app.run(
        host=host,
        port=port,
        debug=False,
        threaded=True
    )
