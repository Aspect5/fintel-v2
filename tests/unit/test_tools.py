import pytest
from unittest.mock import Mock, patch, MagicMock
from tools.registry import ToolRegistry
from tools.market_data import MarketDataTool, CompanyOverviewTool
from tools.economic_data import EconomicDataTool

class TestToolRegistry:
    @pytest.mark.unit
    def test_tool_registry_initialization(self):
        """Test tool registry initialization"""
        with patch('tools.registry.get_settings') as mock_settings:
            mock_settings.return_value = Mock()
            registry = ToolRegistry()
            
            assert hasattr(registry, '_tools')
            assert hasattr(registry, '_tool_instances')

    @pytest.mark.unit
    def test_get_tools(self):
        """Test getting tools from registry"""
        with patch('tools.registry.get_settings') as mock_settings:
            mock_settings.return_value = Mock()
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
        with patch('tools.market_data.get_settings') as mock_settings:
            mock_settings.return_value = Mock(alpha_vantage_api_key="test-key")
            tool = MarketDataTool()
            
            assert hasattr(tool, 'api_key')

    @pytest.mark.unit
    @patch('requests.get')
    def test_get_stock_quote(self, mock_get, sample_market_data):
        """Test getting stock quote"""
        with patch('tools.market_data.get_settings') as mock_settings:
            mock_settings.return_value = Mock(alpha_vantage_api_key="test-key")
            
            # Mock API response
            mock_response = Mock()
            mock_response.json.return_value = {
                'Global Quote': {
                    '01. symbol': 'AAPL',
                    '05. price': '150.25',
                    '09. change': '2.50',
                    '10. change percent': '1.69%'
                }
            }
            mock_get.return_value = mock_response
            
            tool = MarketDataTool()
            result = tool.get_stock_quote("AAPL")
            
            assert 'symbol' in result
            assert result['symbol'] == 'AAPL'

class TestCompanyOverviewTool:
    @pytest.mark.unit
    def test_company_overview_initialization(self):
        """Test company overview tool initialization"""
        with patch('tools.market_data.get_settings') as mock_settings:
            mock_settings.return_value = Mock(alpha_vantage_api_key="test-key")
            tool = CompanyOverviewTool()
            
            assert hasattr(tool, 'api_key')

class TestEconomicDataTool:
    @pytest.mark.unit
    def test_economic_data_tool_initialization(self):
        """Test economic data tool initialization"""
        with patch('tools.economic_data.get_settings') as mock_settings:
            mock_settings.return_value = Mock(alpha_vantage_api_key="test-key")
            tool = EconomicDataTool()
            
            assert hasattr(tool, 'api_key')

    @pytest.mark.unit
    @patch('requests.get')
    def test_get_gdp_data(self, mock_get):
        """Test getting GDP data"""
        with patch('tools.economic_data.get_settings') as mock_settings:
            mock_settings.return_value = Mock(alpha_vantage_api_key="test-key")
            
            # Mock API response
            mock_response = Mock()
            mock_response.json.return_value = {
                'data': [
                    {'date': '2023-Q4', 'value': '27000000000000'},
                    {'date': '2023-Q3', 'value': '26800000000000'}
                ]
            }
            mock_get.return_value = mock_response
            
            tool = EconomicDataTool()
            result = tool.get_gdp_data()
            
            assert 'data' in result
            assert len(result['data']) == 2
