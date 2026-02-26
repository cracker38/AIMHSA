"""
AI Service for AIMHSA
Uses OpenAI-compatible API for OpenRouter / Ollama inference
"""

import os
from pathlib import Path
from openai import OpenAI
from typing import List, Dict, Optional
import logging

# Load .env from project root so OLLAMA_API_KEY is set when this module is imported
try:
    from dotenv import load_dotenv
    _root = Path(__file__).resolve().parent
    load_dotenv(_root / ".env", override=True)
except Exception:
    pass

class HuggingFaceAIService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.openai_client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize OpenAI-compatible client for OpenRouter/Ollama"""
        try:
            base_url = (os.getenv("OLLAMA_BASE_URL") or "https://openrouter.ai/api/v1").strip()
            api_key = (os.getenv("OLLAMA_API_KEY") or "").strip()
            
            if not api_key:
                self.logger.warning(
                    "OLLAMA_API_KEY is not set. Set it in .env for AI responses. "
                    "Using fallback for all messages until then."
                )
                self.openai_client = None
                return
            
            self.openai_client = OpenAI(base_url=base_url, api_key=api_key)
            self.logger.info("AI client initialized (OpenRouter/Ollama). Base URL: %s", base_url)
            
        except Exception as e:
            self.logger.error("Failed to initialize AI client: %s", str(e))
            self.openai_client = None
    
    def generate_response(self, messages: List[Dict], system_prompt: str = "") -> str:
        """Generate AI response using OpenAI-compatible API"""
        if not self.openai_client:
            self.logger.debug("No AI client; returning fallback")
            return self._get_fallback_response()
        if not messages or not isinstance(messages, list):
            self.logger.warning("Empty or invalid messages; returning fallback")
            return self._get_fallback_response()
        
        try:
            chat_model = os.getenv("CHAT_MODEL", "meta-llama/llama-3.1-8b-instruct:free").strip()
            # Reject invalid model IDs (e.g. URL path like "api/v1")
            if not chat_model or chat_model in ("api/v1", "api/v1/") or chat_model.startswith("http"):
                chat_model = "meta-llama/llama-3.1-8b-instruct:free"
                self.logger.warning("Invalid CHAT_MODEL, using fallback: %s", chat_model)
            self.logger.info("Calling API model=%s messages=%d", chat_model, len(messages))
            
            response = self.openai_client.chat.completions.create(
                model=chat_model,
                messages=messages,
                temperature=0.7,
                top_p=0.9,
                max_tokens=1024,
            )
            
            if not response or not getattr(response, "choices", None) or len(response.choices) == 0:
                self.logger.warning("API returned no choices; using fallback")
                return self._get_fallback_response()
            
            content = response.choices[0].message.content
            if content and isinstance(content, str) and content.strip():
                return content.strip()
            
            self.logger.warning("API returned empty content; using fallback")
            return self._get_fallback_response()
            
        except Exception as e:
            self.logger.exception("API call failed: %s", str(e))
            return self._get_fallback_response()
    
    def _get_fallback_response(self) -> str:
        """Get a helpful fallback response when AI is unavailable"""
        return "I'm here to help. Could you please rephrase your question? If this is an emergency, contact Rwanda's Mental Health Hotline at 105 or CARAES Ndera Hospital at +250 788 305 703."
    
    def is_available(self) -> bool:
        """Check if the AI service is available"""
        return self.openai_client is not None

# Global AI service instance
ai_service = None

def get_ai_service():
    """Get the global AI service instance"""
    global ai_service
    if ai_service is None:
        ai_service = HuggingFaceAIService()
    return ai_service

def initialize_ai_service():
    """Initialize the AI service"""
    global ai_service
    ai_service = HuggingFaceAIService()
    return ai_service