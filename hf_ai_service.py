"""
Hugging Face AI Service for AIMHSA
Uses Hugging Face transformers instead of Ollama
"""

import os
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from typing import List, Dict, Optional
import logging

class HuggingFaceAIService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.model_name = "microsoft/DialoGPT-medium"
        self.tokenizer = None
        self.model = None
        self.pipeline = None
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the Hugging Face model"""
        try:
            self.logger.info(f"Loading Hugging Face model: {self.model_name}")
            
            # Use CPU for Hugging Face Spaces
            device = "cpu"
            
            # Load tokenizer and model
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=torch.float32,
                device_map=device
            )
            
            # Create text generation pipeline
            self.pipeline = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                device=device,
                max_length=512,
                do_sample=True,
                temperature=0.7,
                pad_token_id=self.tokenizer.eos_token_id
            )
            
            self.logger.info("✅ Hugging Face model loaded successfully")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to load Hugging Face model: {str(e)}")
            self.pipeline = None
    
    def generate_response(self, messages: List[Dict], system_prompt: str = "") -> str:
        """Generate AI response using Hugging Face model"""
        try:
            if not self.pipeline:
                return "I'm sorry, I'm having trouble accessing my AI model right now. However, I can still help you with mental health resources in Rwanda. Please contact the Mental Health Hotline at 105 or CARAES Ndera Hospital at +250 788 305 703 for immediate support."
            
            # Convert messages to conversation format
            conversation_text = self._format_conversation(messages, system_prompt)
            
            # Generate response
            response = self.pipeline(
                conversation_text,
                max_new_tokens=150,
                num_return_sequences=1,
                temperature=0.7,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id
            )
            
            # Extract generated text
            generated_text = response[0]['generated_text']
            
            # Extract only the new response part
            new_response = generated_text[len(conversation_text):].strip()
            
            # Clean up the response
            if new_response:
                # Remove any incomplete sentences or repetitive text
                lines = new_response.split('\n')
                clean_response = lines[0].strip()
                
                # Ensure it's a reasonable length
                if len(clean_response) > 200:
                    clean_response = clean_response[:200] + "..."
                
                return clean_response if clean_response else "I understand you're reaching out for support. How can I help you today?"
            else:
                return "I understand you're reaching out for support. How can I help you today?"
                
        except Exception as e:
            self.logger.error(f"Error generating response: {str(e)}")
            return "I'm sorry, I'm having trouble accessing my AI model right now. However, I can still help you with mental health resources in Rwanda. Please contact the Mental Health Hotline at 105 or CARAES Ndera Hospital at +250 788 305 703 for immediate support."
    
    def _format_conversation(self, messages: List[Dict], system_prompt: str = "") -> str:
        """Format conversation for the model"""
        try:
            conversation = ""
            
            if system_prompt:
                conversation += f"System: {system_prompt}\n"
            
            # Add recent messages (last 5 to keep context manageable)
            recent_messages = messages[-5:] if len(messages) > 5 else messages
            
            for msg in recent_messages:
                role = msg.get('role', 'user')
                content = msg.get('content', '')
                
                if role == 'user':
                    conversation += f"Human: {content}\n"
                elif role == 'assistant':
                    conversation += f"AI: {content}\n"
            
            # Add prompt for AI response
            conversation += "AI: "
            
            return conversation
            
        except Exception as e:
            self.logger.error(f"Error formatting conversation: {str(e)}")
            return "Human: Hello\nAI: "
    
    def is_available(self) -> bool:
        """Check if the AI service is available"""
        return self.pipeline is not None

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