import pytest
from unittest.mock import Mock, patch
from providers.factory import ProviderFactory
from providers.openai_provider import OpenAIProvider
from providers.gemini_provider import GeminiProvider
from providers.local_provider import LocalProvider

class TestProviderFactory:
    @pytest.mark.unit
    def test_factory_initialization(self):
        """Test provider factory initialization"""
        factory = ProviderFactory()
        assert hasattr(factory, '_providers')

    @pytest.mark.unit
    def test_get_provider_openai(self, mock_api_keys):
        """Test getting OpenAI provider"""
        factory = ProviderFactory()
        
        with patch('providers.factory.OpenAIProvider') as mock_provider:
            mock_instance = Mock()
            mock_provider.return_value = mock_instance
            
            provider = factory.get_provider("openai")
            assert provider is not None

    @pytest.mark.unit
    def test_get_provider_gemini(self, mock_api_keys):
        """Test getting Gemini provider"""
        factory = ProviderFactory()
        
        with patch('providers.factory.GeminiProvider') as mock_provider:
            mock_instance = Mock()
            mock_provider.return_value = mock_instance
            
            provider = factory.get_provider("gemini")
            assert provider is not None

    @pytest.mark.unit
    def test_get_provider_local(self):
        """Test getting local provider"""
        factory = ProviderFactory()
        
        with patch('providers.factory.LocalProvider') as mock_provider:
            mock_instance = Mock()
            mock_provider.return_value = mock_instance
            
            provider = factory.get_provider("local")
            assert provider is not None

    @pytest.mark.unit
    def test_invalid_provider(self):
        """Test getting invalid provider"""
        factory = ProviderFactory()
        
        with pytest.raises(ValueError):
            factory.get_provider("invalid_provider")

class TestOpenAIProvider:
    @pytest.mark.unit
    def test_openai_provider_initialization(self, mock_api_keys):
        """Test OpenAI provider initialization"""
        with patch('providers.openai_provider.openai'):
            provider = OpenAIProvider()
            assert hasattr(provider, 'client')

class TestGeminiProvider:
    @pytest.mark.unit
    def test_gemini_provider_initialization(self, mock_api_keys):
        """Test Gemini provider initialization"""
        with patch('providers.gemini_provider.genai'):
            provider = GeminiProvider()
            assert hasattr(provider, 'model')

class TestLocalProvider:
    @pytest.mark.unit
    def test_local_provider_initialization(self):
        """Test local provider initialization"""
        provider = LocalProvider()
        assert hasattr(provider, 'model_name')
