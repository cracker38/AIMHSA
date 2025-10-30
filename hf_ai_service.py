"""
AI Service for AIMHSA
Uses OpenAI-compatible API for Ollama/Hugging Face inference
"""

import os
from openai import OpenAI
from typing import List, Dict, Optional
import logging

class HuggingFaceAIService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.openai_client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize OpenAI-compatible client for Ollama"""
        try:
            self.logger.info("Initializing OpenAI-compatible client...")
            
            # Get configuration from environment
            base_url = os.getenv("OLLAMA_BASE_URL", "https://openrouter.ai/api/v1")
            api_key = os.getenv("OLLAMA_API_KEY", "")
            
            self.openai_client = OpenAI(
                base_url=base_url,
                api_key=api_key
            )
            
            self.logger.info(f"✅ OpenAI-compatible client initialized with base URL: {base_url}")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize OpenAI client: {str(e)}")
            self.openai_client = None
    
    def generate_response(self, messages: List[Dict], system_prompt: str = "") -> str:
        """Generate AI response using OpenAI-compatible API"""
        try:
            if not self.openai_client:
                return self._get_fallback_response()
            
            # Make sure messages list is not empty and properly formatted
            if not messages or not isinstance(messages, list):
                return self._get_fallback_response()
            
            # Call OpenAI-compatible API
            chat_model = os.getenv('CHAT_MODEL', 'meta-llama/llama-3.1-8b-instruct')
            response = self.openai_client.chat.completions.create(
                model=chat_model,
                messages=messages,
                temperature=0.7,
                top_p=0.9,
                max_tokens=1024
            )
            
            # Extract the response content
            if response and response.choices and len(response.choices) > 0:
                answer = response.choices[0].message.content
                
                # Validate and return the response
                if answer and isinstance(answer, str) and answer.strip():
                    return answer.strip()
            
            return self._get_fallback_response()
                
        except Exception as e:
            self.logger.error(f"Error generating response: {str(e)}")
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