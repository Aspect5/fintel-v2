import os
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

class Settings:
    """Centralized configuration management"""
    
    def __init__(self):
        # API Keys
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        self.alpha_vantage_api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
        self.fred_api_key = os.getenv("FRED_API_KEY")
        
        # Provider Settings
        self.default_provider = os.getenv("DEFAULT_PROVIDER", "openai")
        self.base_url = os.getenv("BASE_URL")
        
        # Application Settings
        self.debug = os.getenv("DEBUG", "false").lower() == "true"
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        
        # Rate Limiting
        self.api_rate_limit = int(os.getenv("API_RATE_LIMIT", "60"))
        self.cache_ttl = int(os.getenv("CACHE_TTL", "300"))
        
        # ControlFlow Settings
        self.enable_experimental_tui = False
        self.enable_print_handler = False
    
    def validate_provider(self, provider: str) -> bool:
        """Validate provider name"""
        valid_providers = ['openai', 'google', 'local']
        return provider in valid_providers
    
    def get_provider_config(self, provider: str) -> Dict[str, Any]:
        """Get configuration for a specific provider"""
        configs = {
            'openai': {
                'api_key': self.openai_api_key,
                'model': 'gpt-4o-mini',
                'temperature': 0.1,
                'max_tokens': 2000
            },
            'google': {
                'api_key': self.google_api_key,
                'model': 'gemini-1.5-flash',
                'temperature': 0.1,
                'max_output_tokens': 2000
            },
            'local': {
                'base_url': self.base_url or 'http://127.0.0.1:8080/v1',
                'model': 'local-model',
                'temperature': 0.1,
                'max_tokens': 2000
            }
        }
        return configs.get(provider, {})

# Global settings instance
_settings = None

def get_settings():
    """Get global settings instance"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
