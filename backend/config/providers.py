from dataclasses import dataclass
from typing import Dict, Any, Optional

@dataclass
class ProviderConfig:
    """Configuration for LLM providers"""
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