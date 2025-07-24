import pytest
from unittest.mock import Mock, patch
from backend.tools.market_data import MarketDataTool, CompanyOverviewTool
from backend.tools.economic_data import EconomicDataTool

class TestMarketDataTools:
    @pytest.mark.unit
    @patch('requests.get')
    def test_get_stock_quote_mocked(self, mock_get, sample_market_data):
        """Test getting a stock quote with a mocked API call."""
        mock_response = Mock()
        # The API returns a dictionary with a "Global Quote" key
        mock_response.json.return_value = {"Global Quote": sample_market_data['Global Quote']}
        mock_get.return_value = mock_response

        tool = MarketDataTool(api_key="test-key")
        result = tool.execute(ticker="AAPL")

        mock_get.assert_called_once_with(
            "https://www.alphavantage.co/query",
            params={'function': 'GLOBAL_QUOTE', 'symbol': 'AAPL', 'apikey': 'test-key'},
            timeout=10
        )
        assert result['symbol'] == 'AAPL'
        assert result['price'] == '150.25'

    @pytest.mark.unit
    @patch('requests.get')
    def test_get_company_overview_mocked(self, mock_get, sample_company_overview):
        """Test getting company overview with a mocked API call."""
        mock_response = Mock()
        mock_response.json.return_value = sample_company_overview
        mock_get.return_value = mock_response

        tool = CompanyOverviewTool(api_key="test-key")
        result = tool.execute(ticker="AAPL")

        mock_get.assert_called_once_with(
            "https://www.alphavantage.co/query",
            params={'function': 'OVERVIEW', 'symbol': 'AAPL', 'apikey': 'test-key'},
            timeout=10
        )
        assert result['symbol'] == 'AAPL'
        assert result['name'] == 'Apple Inc.'

class TestEconomicDataTool:
    @pytest.mark.unit
    @patch('requests.get')
    def test_get_real_gdp_mocked(self, mock_get):
        """Test getting real GDP data with a mocked API call."""
        mock_response = Mock()
        mock_response.json.return_value = {"observations": [{"date": "2023-01-01", "value": "21987.89"}]}
        mock_get.return_value = mock_response

        tool = EconomicDataTool(api_key="test-key")
        result = tool.execute(series_id='GDPC1')

        mock_get.assert_called_once_with(
            "https://api.stlouisfed.org/fred/series/observations",
            params={'series_id': 'GDPC1', 'api_key': 'test-key', 'file_type': 'json', 'limit': 10, 'sort_order': 'desc'},
            timeout=10
        )
        assert 'data' in result
        assert result['data'][0]['value'] == '21987.89'
