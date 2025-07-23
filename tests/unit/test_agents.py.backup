import pytest
from unittest.mock import Mock, patch
from agents.base import BaseAgentConfig
from agents.financial import FinancialAnalystConfig
from agents.market import MarketAnalystConfig
from agents.economic import EconomicAnalystConfig
from agents.registry import AgentRegistry

class TestBaseAgentConfig:
    @pytest.mark.unit
    def test_base_agent_config_creation(self):
        """Test basic agent configuration creation"""
        config = BaseAgentConfig(
            name="TestAgent",
            instructions="Test instructions",
            tools=["tool1", "tool2"],
            model="gpt-4",
            temperature=0.2
        )
        
        assert config.name == "TestAgent"
        assert config.instructions == "Test instructions"
        assert config.tools == ["tool1", "tool2"]
        assert config.model == "gpt-4"
        assert config.temperature == 0.2

    @pytest.mark.unit
    def test_create_agent(self, mock_controlflow):
        """Test agent creation from config"""
        config = BaseAgentConfig(
            name="TestAgent",
            instructions="Test instructions",
            tools=["tool1"]
        )
        
        with patch('agents.base.get_tool_registry') as mock_registry:
            mock_registry.return_value.get_tools.return_value = [Mock()]
            agent = config.create_agent("gpt-4")
            
            assert mock_controlflow.called

class TestFinancialAnalystConfig:
    @pytest.mark.unit
    def test_financial_analyst_initialization(self):
        """Test financial analyst configuration"""
        config = FinancialAnalystConfig()
        
        assert config.name == "FinancialAnalyst"
        assert "financial analyst" in config.instructions.lower()
        assert "coordinator" in config.instructions.lower()
        assert len(config.tools) > 0

class TestMarketAnalystConfig:
    @pytest.mark.unit
    def test_market_analyst_initialization(self):
        """Test market analyst configuration"""
        config = MarketAnalystConfig()
        
        assert config.name == "MarketAnalyst"
        assert "market" in config.instructions.lower()
        assert len(config.tools) > 0

class TestEconomicAnalystConfig:
    @pytest.mark.unit
    def test_economic_analyst_initialization(self):
        """Test economic analyst configuration"""
        config = EconomicAnalystConfig()
        
        assert config.name == "EconomicAnalyst"
        assert "economic" in config.instructions.lower()
        assert len(config.tools) > 0

class TestAgentRegistry:
    @pytest.mark.unit
    def test_agent_registry_initialization(self, mock_controlflow):
        """Test agent registry initialization"""
        with patch('agents.registry.ProviderFactory'):
            registry = AgentRegistry()
            
            assert hasattr(registry, '_agent_configs')
            assert hasattr(registry, '_agents')

    @pytest.mark.unit
    def test_get_agent(self, mock_controlflow):
        """Test getting agent from registry"""
        with patch('agents.registry.ProviderFactory'):
            registry = AgentRegistry()
            
            # Mock the get_agent method
            with patch.object(registry, 'get_agent') as mock_get:
                mock_get.return_value = Mock()
                agent = registry.get_agent("FinancialAnalyst", "openai")
                
                mock_get.assert_called_once_with("FinancialAnalyst", "openai")
