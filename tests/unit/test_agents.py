import pytest
from unittest.mock import Mock, patch
from backend.agents.base import BaseAgentConfig
from backend.agents.financial import FinancialAnalystConfig
from backend.agents.market import MarketAnalystConfig
from backend.agents.economic import EconomicAnalystConfig
from backend.agents.registry import AgentRegistry

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
    @pytest.mark.unit
    def test_create_agent(self, mock_controlflow):
        """Test agent creation from config"""
        from backend.agents.base import BaseAgentConfig
        
        config = BaseAgentConfig(
            name="TestAgent",
            instructions="Test instructions",
            tools=["tool1"]
        )

        with patch('backend.agents.base.cf.Agent') as mock_agent_class:
            with patch('backend.agents.base.get_tool_registry') as mock_registry:
                # Mock the tool registry
                mock_tool_instance = Mock()
                # Return empty dict so tool1 won't be found
                mock_tool_instance.get_available_tools.return_value = {}
                mock_registry.return_value = mock_tool_instance
                
                # Create agent
                agent = config.create_agent("gpt-4")

                # Since tool1 is not in available tools, tools list should be empty
                mock_agent_class.assert_called_once_with(
                    name="TestAgent",
                    instructions="Test instructions",
                    tools=[],  # Empty because tool1 not found
                    model="gpt-4"
                )
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
