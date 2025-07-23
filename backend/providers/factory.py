from typing import Dict, Type, Optional
from .base import BaseProvider
from .openai_provider import OpenAIProvider
from .gemini_provider import GeminiProvider
from .local_provider import LocalProvider
from config.settings import get_settings
from config.providers import ProviderConfig

class ProviderFactory:
    """Factory for creating LLM providers"""
    
    _providers: Dict[str, Type[BaseProvider]] = {
        'openai': OpenAIProvider,
        'google': GeminiProvider,
        'local': LocalProvider
    }
    
    _instances: Dict[str, BaseProvider] = {}
    
    @classmethod
    def create_provider(cls, provider_name: str) -> Optional[BaseProvider]:
        """Create or get cached provider instance"""
        if provider_name in cls._instances:
            return cls._instances[provider_name]
        
        if provider_name not in cls._providers:
            raise ValueError(f"Unknown provider: {provider_name}")
        
        settings = get_settings()
        provider_config_dict = settings.get_provider_config(provider_name)
        
        # Create provider config
        config = ProviderConfig(
            name=provider_name,
            **provider_config_dict
        )
        
        # Validate configuration
        if not config.validate():
            print(f"Invalid configuration for provider: {provider_name}")
            return None
        
        # Create provider instance
        provider_class = cls._providers[provider_name]
        provider = provider_class(config)
        
        # Cache if valid
        if provider.is_available():
            cls._instances[provider_name] = provider
            return provider
        
        return None
    
    @classmethod
    def get_available_providers(cls) -> Dict[str, BaseProvider]:
        """Get all available providers"""
        available = {}
        for name in cls._providers.keys():
            provider = cls.create_provider(name)
            if provider and provider.is_available():
                available[name] = provider
        return available
    
    @classmethod
    def get_provider_status(cls) -> Dict[str, Dict]:
        """Get status of all providers"""
        status = {}
        for name in cls._providers.keys():
            try:
                provider = cls.create_provider(name)
                if provider:
                    status[name] = provider.get_health_status()
                else:
                    status[name] = {
                        'provider': name,
                        'available': False,
                        'error': 'Configuration invalid'
                    }
            except Exception as e:
                status[name] = {
                    'provider': name,
                    'available': False,
                    'error': str(e)
                }
        return status