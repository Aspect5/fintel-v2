from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import controlflow as cf
from backend.config.providers import ProviderConfig

class BaseProvider(ABC):
    """Abstract base class for LLM providers"""
    
    def __init__(self, config: ProviderConfig):
        self.config = config
        self._validated = False
    
    @abstractmethod
    def validate_connection(self) -> bool:
        """Validate provider connection and credentials"""
        pass
    
    @abstractmethod
    def create_model_config(self) -> str:
        """Create ControlFlow model configuration string"""
        pass
    
    @abstractmethod
    def get_health_status(self) -> Dict[str, Any]:
        """Get provider health status"""
        pass
    
    def is_available(self) -> bool:
        """Check if provider is available"""
        if not self._validated:
            self._validated = self.validate_connection()
        return self._validated