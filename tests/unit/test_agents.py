import pytest
from unittest.mock import Mock, patch
from backend.agents.base import BaseAgentConfig
from backend.agents.registry import AgentRegistry

class TestBaseAgentConfig:
    @pytest.mark.unit
    def test_base_agent_config_creation(self):
        """Test basic agent configuration creation"""
        config = BaseAgentConfig(
            name="TestAgent",
            instructions="Test instructions",
            tools=["tool1", "tool2"],
        )
        
        assert config.name == "TestAgent"
        assert config.instructions == "Test instructions"
        assert config.tools == ["tool1", "tool2"]

    @pytest.mark.unit
    @patch('backend.agents.base.cf.Agent')
    @patch('backend.agents.base.get_tool_registry')
    def test_create_agent_with_tools(self, mock_get_tool_registry, mock_agent_class):
        """Test that create_agent correctly calls cf.Agent with the right parameters."""
        mock_tool = Mock()
        mock_tool_registry = Mock()
        mock_tool_registry.get_available_tools.return_value = {"tool1": mock_tool}
        mock_get_tool_registry.return_value = mock_tool_registry
        
        config = BaseAgentConfig(
            name="TestAgent",
            instructions="Test instructions",
            tools=["tool1"]
        )
        
        agent = config.create_agent(model="openai/gpt-4")
        
        mock_agent_class.assert_called_once()
        args, kwargs = mock_agent_class.call_args
        assert kwargs['name'] == 'TestAgent'
        assert kwargs['instructions'] == 'Test instructions'
        assert len(kwargs['tools']) == 1
        assert kwargs['tools'][0] == mock_tool
        assert kwargs['model'] == 'openai/gpt-4'

class TestAgentRegistry:
    @pytest.mark.unit
    @patch('backend.agents.registry.ProviderFactory')
    def test_agent_registry_initialization(self, mock_provider_factory):
        """Test agent registry initialization"""
        registry = AgentRegistry()
        
        assert hasattr(registry, '_agent_configs')
        assert hasattr(registry, '_agents')

    @pytest.mark.unit
    @patch('backend.agents.registry.ProviderFactory')
    def test_get_agent(self, mock_provider_factory):
        """Test getting agent from registry"""
        mock_provider = Mock()
        mock_provider.create_model_config.return_value = "openai/gpt-4"
        mock_provider_factory.create_provider.return_value = mock_provider
        
        registry = AgentRegistry()
        
        with patch.object(registry, '_load_yaml_agents'):
            registry._agent_configs['TestAgent'] = BaseAgentConfig(name='TestAgent', instructions='Test', tools=[])
            
            agent = registry.get_agent("TestAgent", "openai")
            
            assert agent is not None
            mock_provider_factory.create_provider.assert_called_with("openai")
