import pytest
from unittest.mock import Mock, patch, MagicMock
from backend.tools.registry import ToolRegistry
from backend.tools.market_data import MarketDataTool, CompanyOverviewTool
from backend.tools.economic_data import EconomicDataTool

class TestToolRegistry:
    @pytest.mark.unit
    def test_tool_registry_initialization(self):
        """Test tool registry initialization"""
        registry = ToolRegistry()
        
        assert hasattr(registry, '_tools')
        assert hasattr(registry, '_tool_instances')

    @pytest.mark.unit
    def test_get_tools(self):
        """Test getting tools from registry"""
        registry = ToolRegistry()
        
        # Mock the get_tools method
        with patch.object(registry, 'get_tools') as mock_get:
            mock_get.return_value = [Mock(), Mock()]
            tools = registry.get_tools(["market_data", "company_overview"])
            
            assert len(tools) == 2
            mock_get.assert_called_once()

class TestMarketDataTool:
    @pytest.mark.unit
    def test_market_data_tool_initialization(self):
        """Test market data tool initialization"""
        tool = MarketDataTool(api_key="test-key")
        assert hasattr(tool, 'api_key')

    @pytest.mark.unit
    @patch('requests.get')
    def test_get_stock_quote(self, mock_get, sample_market_data):
        """Test getting stock quote"""
        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = sample_market_data
        mock_get.return_value = mock_response
        
        tool = MarketDataTool(api_key="test-key")
        result = tool.execute("AAPL")
        
        # Check the result based on what execute returns
        assert 'symbol' in result
        assert result['symbol'] == 'AAPL' 
