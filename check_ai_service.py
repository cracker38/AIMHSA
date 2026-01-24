#!/usr/bin/env python3
"""
AIMHSA AI Service Diagnostic Tool
Checks AI service configuration and connectivity
"""

import os
import sys
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

print("=" * 60)
print("AIMHSA AI Service Diagnostic")
print("=" * 60)
print()

# Check environment variables
base_url = os.getenv("OLLAMA_BASE_URL", "https://openrouter.ai/api/v1")
api_key = os.getenv("OLLAMA_API_KEY", "")
chat_model = os.getenv("CHAT_MODEL", "meta-llama/llama-3.1-8b-instruct")

print("Configuration:")
print(f"  Base URL: {base_url}")
print(f"  API Key: {'SET' if api_key else 'NOT SET'}")
if api_key:
    print(f"  API Key (first 20 chars): {api_key[:20]}...")
print(f"  Chat Model: {chat_model}")
print()

if not api_key:
    print("ERROR: OLLAMA_API_KEY is not set in .env file")
    print()
    print("To fix this:")
    print("1. Open your .env file")
    print("2. Add: OLLAMA_API_KEY=your_api_key_here")
    print("3. For OpenRouter: Get a free API key at https://openrouter.ai/keys")
    print("4. Restart the application")
    sys.exit(1)

# Test API connection
print("Testing API connection...")
try:
    client = OpenAI(
        base_url=base_url,
        api_key=api_key
    )
    
    print("  Sending test request...")
    response = client.chat.completions.create(
        model=chat_model,
        messages=[{"role": "user", "content": "Say hello"}],
        max_tokens=20
    )
    
    answer = response.choices[0].message.content
    print(f"SUCCESS! API is working correctly")
    print(f"  Response: {answer}")
    print()
    print("Your AI service is properly configured!")
    
except Exception as e:
    error_msg = str(e)
    error_type = type(e).__name__
    
    print(f"ERROR: API connection failed")
    print(f"  Error Type: {error_type}")
    print(f"  Error Message: {error_msg}")
    print()
    
    if '401' in error_msg or 'authentication' in error_msg.lower() or 'User not found' in error_msg:
        print("AUTHENTICATION ERROR:")
        print("   Your API key is invalid or expired.")
        print()
        print("To fix this:")
        print("1. Get a new API key:")
        print("   - OpenRouter: https://openrouter.ai/keys (free tier available)")
        print("   - Or use local Ollama: https://ollama.ai")
        print()
        print("2. Update your .env file:")
        print(f"   OLLAMA_API_KEY=your_new_api_key_here")
        print()
        print("3. Restart the application")
    elif '429' in error_msg or 'rate limit' in error_msg.lower():
        print("RATE LIMIT ERROR:")
        print("   You've exceeded the API rate limit.")
        print("   Please wait a few minutes and try again.")
    else:
        print("GENERAL ERROR:")
        print("   There's an issue with the API connection.")
        print("   Check your internet connection and API endpoint.")
    
    sys.exit(1)

print()
print("=" * 60)

