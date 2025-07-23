import google.generativeai as genai
from typing import Dict, Any
from .base import BaseProvider

class GeminiProvider(BaseProvider):
    """Google Gemini provider implementation"""
    
    def validate_connection(self) -> bool:
        """Validate Gemini API connection"""
        try:
            if not self.config.api_key:
                return False
            
            genai.configure(api_key=self.config.api_key)
            # Test connection
            models = genai.list_models()
            return True
        except Exception as e:
            print(f"Gemini validation failed: {e}")
            return False
    
    def create_model_config(self) -> str:
        """Create ControlFlow model configuration"""
        return f"google/{self.config.model}"
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get Gemini health status"""
        return {
            'provider': 'google',
            'model': self.config.model,
            'available': self.is_available(),
            'api_key_configured': bool(self.config.api_key)
        }