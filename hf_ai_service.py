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
            
            if not api_key:
                self.logger.warning("=" * 60)
                self.logger.warning("⚠️ OLLAMA_API_KEY NOT SET")
                self.logger.warning("=" * 60)
                self.logger.warning("AI responses will use fallback mode.")
                self.logger.warning("")
                self.logger.warning("To fix this:")
                self.logger.warning("1. Go to: https://huggingface.co/spaces/CYPADILtd/aimhsa-chatbot/settings")
                self.logger.warning("2. Click 'Repository secrets'")
                self.logger.warning("3. Add secret: OLLAMA_API_KEY = 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")
                self.logger.warning("4. Restart the Space")
                self.logger.warning("=" * 60)
                self.openai_client = None
                return
            
            self.openai_client = OpenAI(
                base_url=base_url,
                api_key=api_key
            )
            
            # Test the connection with a simple call
            try:
                self.logger.info("Testing API connection...")
                test_response = self.openai_client.chat.completions.create(
                    model=os.getenv('CHAT_MODEL', 'meta-llama/llama-3.1-8b-instruct'),
                    messages=[{"role": "user", "content": "test"}],
                    max_tokens=5
                )
                self.logger.info(f"✅ OpenAI-compatible client initialized successfully with base URL: {base_url}")
            except Exception as test_error:
                error_msg = str(test_error)
                if '401' in error_msg or 'authentication' in error_msg.lower() or 'User not found' in error_msg:
                    self.logger.error(f"❌ API Authentication Failed: Invalid API key")
                    self.logger.error(f"   Please check your OLLAMA_API_KEY in .env file")
                    self.logger.error(f"   Error: {error_msg}")
                    self.openai_client = None
                else:
                    self.logger.warning(f"⚠️ API test failed but client initialized: {error_msg}")
                    self.logger.info(f"✅ OpenAI-compatible client initialized with base URL: {base_url} (test failed)")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize OpenAI client: {str(e)}")
            self.openai_client = None
    
    def generate_response(self, messages: List[Dict], system_prompt: str = "") -> str:
        """Generate AI response using OpenAI-compatible API"""
        try:
            if not self.openai_client:
                self.logger.warning("OpenAI client not initialized")
                return self._get_fallback_response()
            
            # Make sure messages list is not empty and properly formatted
            if not messages or not isinstance(messages, list):
                self.logger.warning("Invalid messages format")
                return self._get_fallback_response()
            
            # Call OpenAI-compatible API
            chat_model = os.getenv('CHAT_MODEL', 'meta-llama/llama-3.1-8b-instruct')
            
            # Add system prompt if provided
            formatted_messages = messages.copy()
            if system_prompt and formatted_messages and formatted_messages[0].get('role') != 'system':
                formatted_messages.insert(0, {'role': 'system', 'content': system_prompt})
            
            try:
                response = self.openai_client.chat.completions.create(
                    model=chat_model,
                    messages=formatted_messages,
                    temperature=0.7,
                    top_p=0.9,
                    max_tokens=1024
                )
                
                # Extract the response content
                if response and response.choices and len(response.choices) > 0:
                    answer = response.choices[0].message.content
                    
                    # Validate and return the response
                    if answer and isinstance(answer, str) and answer.strip():
                        self.logger.info(f"Successfully generated response (length: {len(answer)})")
                        return answer.strip()
                
                self.logger.warning("Empty response from API")
                return self._get_fallback_response()
                
            except Exception as api_error:
                error_type = type(api_error).__name__
                error_msg = str(api_error)
                
                # Handle specific error types
                if '401' in error_msg or 'AuthenticationError' in error_type or 'authentication' in error_msg.lower():
                    self.logger.error(f"API Authentication Error: {error_msg}")
                    self.logger.error("Please check your OLLAMA_API_KEY in .env file")
                    return self._get_fallback_response_with_auth_error()
                elif '429' in error_msg or 'rate limit' in error_msg.lower():
                    self.logger.error(f"API Rate Limit Error: {error_msg}")
                    return self._get_fallback_response_with_rate_limit()
                else:
                    self.logger.error(f"API Error ({error_type}): {error_msg}")
                    return self._get_fallback_response()
                
        except Exception as e:
            self.logger.error(f"Unexpected error generating response: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return self._get_fallback_response()
    
    def _get_fallback_response(self) -> str:
        """Get a helpful fallback response when AI is unavailable"""
        return "I'm here to help. Could you please rephrase your question? If this is an emergency, contact Rwanda's Mental Health Hotline at 105 or CARAES Ndera Hospital at +250 788 305 703."
    
    def _get_fallback_response_with_auth_error(self) -> str:
        """Fallback response when API authentication fails"""
        return "Hello! I'm AIMHSA, your mental health companion for Rwanda. I'm currently experiencing a configuration issue with my AI service. Please contact the Mental Health Hotline at 105 or CARAES Ndera Hospital at +250 788 305 703 for immediate support. The system administrator has been notified."
    
    def _get_fallback_response_with_rate_limit(self) -> str:
        """Fallback response when API rate limit is exceeded"""
        return "Hello! I'm AIMHSA. I'm currently experiencing high demand. Please try again in a moment, or contact the Mental Health Hotline at 105 or CARAES Ndera Hospital at +250 788 305 703 for immediate support."
    
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