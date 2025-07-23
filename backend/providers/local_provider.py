import requests
from typing import Dict, Any
from .base import BaseProvider

class LocalProvider(BaseProvider):
    """Local OpenAI-compatible provider implementation"""
    
    def validate_connection(self) -> bool:
        """Validate local model connection"""
        try:
            if not self.config.base_url:
                return False
            
            # Test health endpoint
            response = requests.get(
                f"{self.config.base_url}/models",
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Local provider validation failed: {e}")
            return False
    
    def create_model_config(self) -> str:
        """Create ControlFlow model configuration"""
        # Local models use OpenAI-compatible format
        return f"openai/{self.config.model}"
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get local provider health status"""
        return {
            'provider': 'local',
            'model': self.config.model,
            'base_url': self.config.base_url,
            'available': self.is_available()
        }