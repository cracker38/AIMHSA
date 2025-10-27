#!/usr/bin/env python3
"""
AIMHSA Entry Point for Hugging Face Spaces
This file starts the AIMHSA application when deployed on Hugging Face Spaces
"""

import os
import sys

# Set environment for Hugging Face Spaces
os.environ.setdefault('FLASK_ENV', 'production')
os.environ.setdefault('SERVER_HOST', '0.0.0.0')
os.environ.setdefault('SERVER_PORT', '7860')

# For Hugging Face Spaces, we need to use the full app.py
if __name__ == "__main__":
    print("🚀 Starting AIMHSA on Hugging Face Spaces...")
    print("Note: This deployment requires Ollama to be running.")
    print("To use locally, run: python run_aimhsa.py")
    
    # Import and run the main app
    from app import app
    
    # Run the app
    app.run(
        host='0.0.0.0',
        port=7860,
        debug=False
    )

