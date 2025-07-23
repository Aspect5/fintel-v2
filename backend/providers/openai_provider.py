from typing import Dict, Any
import os
from .base import BaseProvider

class OpenAIProvider(BaseProvider):
    """OpenAI provider implementation"""
    
    def validate_connection(self) -> bool:
        """Validate OpenAI connection and credentials"""
        try:
            # Check if API key is set
            api_key = self.config.api_key or os.getenv('OPENAI_API_KEY')
            if not api_key:
                print("OpenAI API key not found")
                return False
            
            # You could add a simple API call here to validate the key
            # For now, just check if key exists
            return True
        except Exception as e:
            print(f"OpenAI provider validation failed: {e}")
            return False
    
    def create_model_config(self) -> str:
        """Create ControlFlow model configuration"""
        return f"openai/{self.config.model}"
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get OpenAI provider health status"""
        return {
            'provider': 'openai',
            'model': self.config.model,
            'api_key_set': bool(self.config.api_key or os.getenv('OPENAI_API_KEY')),
            'available': self.is_available()
        }
