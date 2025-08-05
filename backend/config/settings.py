# backend/config/settings.py - Simple, centralized configuration
import os
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from dataclasses import dataclass

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

@dataclass
class ProviderConfig:
    """Simple provider configuration"""
    name: str
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: float = 0.1
    max_tokens: int = 2000
    timeout: int = 30
    
    def to_controlflow_model(self) -> str:
        """Convert to ControlFlow model string format"""
        if self.name == 'openai':
            return f"openai/{self.model}"
        elif self.name == 'google':
            return f"google/{self.model}"
        elif self.name == 'local':
            return f"openai/{self.model}"  # Local uses OpenAI-compatible format
        else:
            raise ValueError(f"Unknown provider: {self.name}")
    
    def validate(self) -> bool:
        """Validate provider configuration"""
        if self.name in ['openai', 'google'] and not self.api_key:
            return False
        if self.name == 'local' and not self.base_url:
            return False
        return True

class Settings:
    """Centralized configuration management - simple and modular"""
    
    def __init__(self):
        # API Keys
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        self.alpha_vantage_api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
        self.fred_api_key = os.getenv("FRED_API_KEY")
        
        # Application Settings
        self.debug = os.getenv("DEBUG", "false").lower() == "true"
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.default_provider = os.getenv("DEFAULT_PROVIDER", "openai")
        
        # Rate Limiting
        self.api_rate_limit = int(os.getenv("API_RATE_LIMIT", "60"))
        self.cache_ttl = int(os.getenv("CACHE_TTL", "300"))
        
        # ControlFlow Settings
        self.enable_experimental_tui = False
        self.enable_print_handler = False
    
    def get_provider_config(self, provider: str) -> ProviderConfig:
        """Get configuration for a specific provider"""
        configs = {
            'openai': ProviderConfig(
                name='openai',
                model='gpt-4o-mini',
                api_key=self.openai_api_key,
                temperature=0.1,
                max_tokens=2000
            ),
            'google': ProviderConfig(
                name='google',
                model='gemini-1.5-flash',
                api_key=self.google_api_key,
                temperature=0.1,
                max_tokens=2000
            ),
            'local': ProviderConfig(
                name='local',
                model='local-model',
                base_url=os.getenv("LOCAL_BASE_URL", 'http://127.0.0.1:8080/v1'),
                temperature=0.1,
                max_tokens=2000
            )
        }
        return configs.get(provider)
    
    def validate_provider(self, provider: str) -> bool:
        """Validate provider name"""
        valid_providers = ['openai', 'google', 'local']
        return provider in valid_providers
    
    def get_config_analytics(self) -> Dict[str, Any]:
        """Get simple configuration analytics"""
        return {
            "total_providers": 3,
            "providers": {
                "openai": {"configured": bool(self.openai_api_key)},
                "google": {"configured": bool(self.google_api_key)},
                "local": {"configured": True}  # Local is always available
            },
            "api_keys_configured": {
                "alpha_vantage": bool(self.alpha_vantage_api_key),
                "fred": bool(self.fred_api_key)
            },
            "environment": "development" if self.debug else "production"
        }

# Global settings instance
_settings = None

def get_settings() -> Settings:
    """Get global settings instance"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
