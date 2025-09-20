"""AI model configuration for Mistral - WORKING VERSION"""

import os
from mistralai import Mistral
from dotenv import load_dotenv

# Make sure to load environment variables
load_dotenv()

class MistralConfig:
    """Configuration for Mistral AI integration"""
    
    def __init__(self):
        self.api_key = os.getenv("MISTRAL_API_KEY")
        if not self.api_key:
            raise ValueError("MISTRAL_API_KEY not found in environment variables")
        
        # Initialize Mistral client (your working code)
        self.client = Mistral(api_key=self.api_key)
        self.model = "mistral-small-latest"  # Using the model from your working example
        self.temperature = 0.3
        self.max_tokens = 1000
    
    def create_chat_completion(self, messages, temperature=None, max_tokens=None):
        """Create chat completion using Mistral (your working approach)"""
        response = self.client.chat.complete(
            model=self.model,
            messages=messages,
            temperature=temperature or self.temperature,
            max_tokens=max_tokens or self.max_tokens
        )
        return response
    
    def create_system_message(self, content: str) -> dict:
        """Create system message"""
        return {"role": "system", "content": content}
    
    def create_user_message(self, content: str) -> dict:
        """Create user message"""
        return {"role": "user", "content": content}
    
    def create_assistant_message(self, content: str) -> dict:
        """Create assistant message"""
        return {"role": "assistant", "content": content}

# Global instance - only create if API key exists
try:
    mistral_config = MistralConfig()
    print(f"✅ Mistral initialized with model: {mistral_config.model}")
except ValueError as e:
    print(f"⚠️ Mistral not initialized: {e}")
    mistral_config = None